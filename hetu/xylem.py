"""Create and initialize Xylem, which services the forward and backward requests from other neurons."""

import os
import time
import uvicorn
import logging
import asyncio
import threading
import contextlib
from typing import Optional, Callable, Any, Union, Dict, List
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import FastAPI, APIRouter
from inspect import signature, Signature, Parameter

from hetu.utils.priority import PriorityThreadPoolExecutor
from hetu.synapse import Synapse,BaseSynapse

class FastAPIThreadedServer(uvicorn.Server):
    """
    The FastAPIThreadedServer class runs the FastAPI application in a separate thread.
    This allows the Xylem server to handle HTTP requests concurrently.
    """

    should_exit: bool = False
    is_running: bool = False

    def install_signal_handlers(self):
        """Disable default signal handlers as we run in a thread."""
        pass

    def start(self):
        """Start the server in a separate thread."""
        self.is_running = True
        self.started = False
        
        # Create and start thread
        thread = threading.Thread(target=self._run_server)
        thread.daemon = True  # Set as daemon thread
        thread.start()
        
        # Wait for server startup
        max_wait = 10
        wait_time = 0
        while not self.started and wait_time < max_wait:
            time.sleep(0.1)
            wait_time += 0.1
        
        if not self.started:
            raise RuntimeError("Server failed to start within timeout")

    def _run_server(self):
        """Run server in background thread"""
        try:
            self.run()
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.is_running = False
            self.started = False

    def stop(self):
        """Stop the server."""
        if self.is_running:
            self.should_exit = True
            self.is_running = False
            # Wait for server shutdown
            try:
                self.should_exit = True
            except:
                pass

class Xylem:
    """
    The Xylem class provides a FastAPI-based HTTP server for handling network requests.
    It supports multiple services, request prioritization, and health checks.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        wallet_path: Optional[str] = None,
        port: Optional[int] = None,
        ip: Optional[str] = None,
        external_ip: Optional[str] = None,
        external_port: Optional[int] = None,
        max_workers: Optional[int] = None,
        trace: bool = False,
        netuid: int = 1,
        network: str = "mainnet",
        hetutensor: Optional["Hetutensor"] = None,
        wallet: Optional["Account"] = None,
    ):
        """Initialize the Xylem server.
        
        Args:
            username (str): Wallet username (optional if wallet is provided)
            password (str): Wallet password (deprecated, use wallet parameter instead)
            wallet_path (Optional[str]): Custom wallet path
            port (Optional[int]): Server port
            ip (Optional[str]): Server IP
            external_ip (Optional[str]): External IP for NAT
            external_port (Optional[int]): External port for NAT
            max_workers (Optional[int]): Max thread pool workers
            trace (bool): Enable trace logging
            netuid (int): Subnet ID to operate on
            network (str): Network name (mainnet, testnet, etc.)
            hetutensor (Optional[Hututensor]): Hetutensor client instance
            wallet (Optional[Account]): Pre-initialized wallet Account object
        """
        # --- Server Config ---
        self.ip = ip or os.getenv("HOST_IP", "127.0.0.1")
        self.port = port or int(os.getenv("PORT", "8091"))
        self.external_ip = external_ip or os.getenv("EXTERNAL_IP")
        self.external_port = external_port or int(os.getenv("EXTERNAL_PORT", "0"))
        self.max_workers = max_workers or int(os.getenv("MAX_WORKERS", "10"))
        self.trace = trace

        # --- Network Configuration ---
        self.netuid = netuid
        self.network = network
        
        # --- Wallet ---
        self.username = username
        self.password = password
        self.wallet_path = wallet_path
        self.wallet = wallet  # Add this line to store the wallet object

        # --- Server ---
        self.started = False
        self.thread_pool = PriorityThreadPoolExecutor(max_workers=self.max_workers)

        # --- Function Registry (支持多个服务) ---
        self.forward_class_types: Dict[str, type] = {}
        self.blacklist_fns: Dict[str, Optional[Callable]] = {}
        self.priority_fns: Dict[str, Optional[Callable]] = {}
        self.forward_fns: Dict[str, Optional[Callable]] = {}
        self.verify_fns: Dict[str, Optional[Callable]] = {}

        # --- Hetutensor ---
        self.hetutensor = hetutensor
        self.wallet_address = None
        
        # --- FastAPI ---
        self.app = FastAPI()
        self.router = APIRouter()
        
        # Add middleware first
        self.app.add_middleware(
            XylemMiddleware,
            xylem=self
        )
        
        # Include router after middleware
        self.app.include_router(self.router)

        # --- Default endpoints ---
        @self.app.post("/ping")
        def ping():
            """Basic health check endpoint."""
            return {"completion": "pong", "status": "ok"}

        @self.app.get("/ping")
        def ping_get():
            """GET ping endpoint for simple health check."""
            return {"completion": "pong", "status": "ok"}

        # Initialize Hetutensor if not provided
        if not self.hetutensor:
            self._init_hetutensor()
        
        # Validate miner status (moved after FastAPI initialization)
        self._validate_miner_status()

    def _init_hetutensor(self):
        """Initialize Hetutensor client if not provided."""
        try:
            from hetu.hetu import Hetutensor
            
            if hasattr(self, 'wallet') and self.wallet:
                # Use pre-initialized wallet
                self.hetutensor = Hetutensor(
                    network=self.network,
                    wallet=self.wallet,
                    wallet_path=self.wallet_path,
                    log_verbose=self.trace
                )
                # Set wallet address immediately for pre-initialized wallet
                self.wallet_address = self.wallet.address
                logging.info(f"Using pre-initialized wallet: {self.wallet_address}")
            else:
                # Use username-based initialization
                self.hetutensor = Hetutensor(
                    network=self.network,
                    username=self.username,
                    wallet_path=self.wallet_path,
                    log_verbose=self.trace
                )
                
                # Set wallet if credentials provided
                if self.username:
                    success = self.hetutensor.set_wallet_from_username(
                        self.username, 
                        self.wallet_path
                    )
                    if success:
                        self.wallet_address = self.hetutensor.get_wallet_address()
                        logging.info(f"Wallet initialized: {self.wallet_address}")
                    else:
                        logging.warning("Failed to initialize wallet")
                else:
                    logging.warning("No wallet credentials provided")
                
        except Exception as e:
            logging.error(f"Failed to initialize Hetutensor: {e}")
            raise RuntimeError(f"Hetutensor initialization failed: {e}")

    def _validate_miner_status(self):
        """Validate that the user is a miner on the specified subnet."""
        if not self.hetutensor or not self.wallet_address:
            logging.error("Cannot validate miner status: no Hetutensor client or wallet")
            raise RuntimeError("No Hetutensor client or wallet available")
        
        try:
            # Check if wallet is a neuron
            is_neuron = self.hetutensor.is_neuron(self.netuid, self.wallet_address)
            if not is_neuron:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not registered as a neuron on subnet {self.netuid}.\n"
                    f"💡 You need to register as a neuron first before starting an Xylem server.\n"
                    f"   Use hetutensor.register_neuron() to register, or use the serve() method.\n"
                    f"   Example: xylem.serve(netuid={self.netuid})"
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Check if wallet is a miner (not a validator)
            is_miner = self.hetutensor.is_miner(self.netuid, self.wallet_address)
            if not is_miner:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not a miner on subnet {self.netuid}.\n"
                    f"💡 Only miners can run Xylem servers. Validators cannot run compute services.\n"
                    f"   You need to register as a miner (not validator) on this subnet.\n"
                    f"   Use hetutensor.register_neuron(is_validator_role=False) to register as a miner."
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Get neuron info for additional validation
            neuron_info = self.hetutensor.get_neuron_info(self.netuid, self.wallet_address)
            if neuron_info:
                is_active = neuron_info.get("is_active", False)
                if not is_active:
                    error_msg = (
                        f"❌ Neuron {self.wallet_address} is not active on subnet {self.netuid}.\n"
                        f"💡 Your neuron registration is inactive. You may need to:\n"
                        f"   1. Wait for activation if recently registered\n"
                        f"   2. Check if you have sufficient stake\n"
                        f"   3. Contact network administrators if the issue persists"
                    )
                    logging.error(error_msg)
                    raise RuntimeError(error_msg)
                
                logging.info(f"✅ Miner validation passed: {self.wallet_address} is an active miner on subnet {self.netuid}")
                logging.info(f"   Stake: {neuron_info.get('stake', 'N/A')}")
                logging.info(f"   Last Update: {neuron_info.get('last_update', 'N/A')}")
            else:
                logging.warning("Could not get detailed neuron info for validation")
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise  # Re-raise our custom errors
            logging.error(f"Failed to validate miner status: {e}")
            raise RuntimeError(f"Miner validation failed: {e}")

    def info(self) -> dict:
        """Return server info."""
        info = {
            'ip': self.ip,
            'port': self.port,
            'external_ip': self.external_ip,
            'external_port': self.external_port,
            'started': self.started,
            'netuid': self.netuid,
            'network': self.network,
            'username': self.username,
            'services': list(self.forward_fns.keys())  # 显示已注册的服务
        }
        
        if self.wallet_address:
            info['wallet_address'] = self.wallet_address
            
        return info

    def attach(
        self,
        forward_fn: Callable,
        blacklist_fn: Optional[Callable] = None,
        priority_fn: Optional[Callable] = None,
        verify_fn: Optional[Callable] = None,
    ) -> "Xylem":
        """Attach handler functions to the server.
        
        Args:
            forward_fn (Callable): Main request handler
            blacklist_fn (Optional[Callable]): Function to check if request should be blacklisted
            priority_fn (Optional[Callable]): Function to determine request priority
            verify_fn (Optional[Callable]): Function to verify request
            
        Returns:
            self: Returns self for method chaining
        """
        # 检查 forward_fn 签名
        forward_sig = signature(forward_fn)
        try:
            first_param = next(iter(forward_sig.parameters.values()))
        except StopIteration:
            raise ValueError("The forward_fn must have at least one argument")

        param_class = first_param.annotation
        if not isinstance(param_class, type) or not issubclass(param_class, BaseSynapse):
            raise ValueError("The first argument of forward_fn must inherit from Synapse")

        # 使用 Synapse 类名作为服务名
        service_name = param_class.__name__
        
        # 创建端点函数
        async def endpoint(request: Request):
            """Endpoint that forwards requests to handler function."""
            try:
                logging.info(f"🔍 Endpoint called: {request.method} {request.url.path}")
                
                # 获取请求体
                if request.method == "GET":
                    # GET 请求通常没有请求体，使用查询参数或默认值
                    body = {}
                    logging.info("🔍 GET request, using empty body")
                else:
                    # POST 请求获取 JSON 体
                    body = await request.json()
                    logging.info(f"🔍 POST request, body: {body}")
                
                # 创建 Synapse 对象
                logging.info("🔍 Creating synapse object...")
                synapse = param_class.from_dict(body)
                logging.info(f"🔍 Synapse created: {synapse}")
                
                # 运行验证
                if verify_fn:
                    logging.info("🔍 Running verification...")
                    try:
                        if asyncio.iscoroutinefunction(verify_fn):
                            await verify_fn(synapse)
                        else:
                            verify_fn(synapse)
                        logging.info("🔍 Verification passed")
                    except Exception as e:
                        logging.error(f"❌ Verification failed: {e}")
                        return JSONResponse(
                            status_code=401,
                            content={"error": f"Verification failed: {e}"}
                        )

                # 检查黑名单
                if blacklist_fn:
                    logging.info("🔍 Checking blacklist...")
                    try:
                        if asyncio.iscoroutinefunction(blacklist_fn):
                            is_blacklisted = await blacklist_fn(synapse)
                        else:
                            is_blacklisted = blacklist_fn(synapse)
                        
                        if is_blacklisted:
                            logging.warning("❌ Request blacklisted")
                            return JSONResponse(
                                status_code=403,
                                content={"error": "Request blacklisted"}
                            )
                        logging.info("🔍 Blacklist check passed")
                    except Exception as e:
                        logging.warning(f"❌ Blacklist check failed: {e}")

                # 调用 forward 函数
                logging.info("🔍 Calling forward function...")
                result = await forward_fn(synapse) if asyncio.iscoroutinefunction(forward_fn) else forward_fn(synapse)
                logging.info(f"🔍 Forward function result: {result}")
                
                # 处理返回结果
                if hasattr(result, 'to_dict'):
                    synapse_dict = result.to_dict()
                    status_code = synapse_dict.get('status_code', 200)
                    logging.info(f"🔍 Returning synapse response: {status_code}")
                    
                    if synapse_dict.get('error'):
                        return JSONResponse(
                            status_code=status_code,
                            content=synapse_dict
                        )
                    
                    return JSONResponse(
                        status_code=status_code,
                        content=synapse_dict
                    )
                else:
                    logging.info("🔍 Returning direct response")
                    return JSONResponse(
                        status_code=200,
                        content=result
                    )
                    
            except Exception as e:
                logging.error(f"❌ Forward function error: {e}")
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Error processing request: {e}"}
                )

        # 添加端点到路由器
        self.router.add_api_route(
            path=f"/{service_name}",
            endpoint=endpoint,
            methods=["GET", "POST"]
        )

        # 重新包含路由器以确保路由生效
        self.app.include_router(self.router)

        # 存储函数到注册表
        self.forward_class_types[service_name] = param_class
        self.blacklist_fns[service_name] = blacklist_fn
        self.priority_fns[service_name] = priority_fn
        self.verify_fns[service_name] = verify_fn or self.default_verify
        self.forward_fns[service_name] = forward_fn

        logging.info(f"✅ Service '{service_name}' attached to endpoint /{service_name}")
        
        return self  # 支持链式调用

    async def default_verify(self, synapse: "Synapse"):
        """Default verification - always passes."""
        return True

    def to_string(self):
        """Get string representation."""
        return self.__str__()

    def __str__(self) -> str:
        """String representation."""
        services = list(self.forward_fns.keys())
        return f"Xylem({self.ip}:{self.port}, services: {services})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Xylem(ip:{self.ip}, port:{self.port}, external_ip:{self.external_ip}, external_port:{self.external_port}, services:{list(self.forward_fns.keys())})"

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if hasattr(self, 'started') and self.started:
                self.stop()
        except Exception:
            pass

    def start(self) -> "Xylem":
        """Start the server."""
        if not self.started:
            log_level = "trace" if self.trace else "info"
            
            # Start server directly with uvicorn in a background thread
            import threading
            
            def run_server():
                try:
                    uvicorn.run(
                        self.app,
                        host=self.ip,
                        port=self.port,
                        log_level=log_level
                    )
                except Exception as e:
                    logging.error(f"Server error: {e}")
            
            # Start server in background thread
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            # Wait a bit for server to start
            import time
            time.sleep(2)
            
            self.started = True
            logging.info(f"Xylem server started successfully on {self.ip}:{self.port}")
            logging.info(f"Available services: {list(self.forward_fns.keys())}")
                
        return self

    def stop(self) -> "Xylem":
        """Stop the server."""
        if self.started:
            self.started = False
            logging.info("Xylem server stopped")
        return self

    def serve(
        self,
        netuid: Optional[int] = None,
        hetutensor: Optional["Hetutensor"] = None,
    ) -> "Xylem":
        """Start serving on network.
        
        Args:
            netuid (Optional[int]): Network ID to serve on (overrides constructor netuid)
            hetutensor (Optional[Hututensor]): Hetutensor client (overrides constructor)
        """
        try:
            target_netuid = netuid if netuid is not None else self.netuid
            target_hetutensor = hetutensor if hetutensor is not None else self.hetutensor
            
            if not target_hetutensor:
                raise ValueError("No Hetutensor client available")

            if not target_hetutensor.has_wallet():
                raise ValueError("No wallet available")

            wallet_address = target_hetutensor.get_wallet_address()
            is_registered = target_hetutensor.is_neuron(target_netuid, wallet_address)
            
            if not is_registered:
                success = target_hetutensor.register_neuron(
                    netuid=target_netuid,
                    is_validator_role=False,
                    axon_endpoint=self.external_ip or self.ip,
                    axon_port=self.external_port or self.port,
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to register neuron")
                logging.info(f"Registered as neuron on subnet {target_netuid}")
            else:
                success = target_hetutensor.update_service(
                    netuid=target_netuid,
                    axon_endpoint=self.external_ip or self.ip,
                    axon_port=self.external_port or self.port,
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to update service info")
                logging.info(f"Updated service info on subnet {target_netuid}")

            if target_netuid != self.netuid:
                self.netuid = target_netuid
                logging.info(f"Switched to subnet {target_netuid}")

            self.start()
            return self

        except Exception as e:
            logging.error(f"Failed to serve: {e}")
            raise

class XylemMiddleware(BaseHTTPMiddleware):
    """Middleware for request processing."""

    def __init__(self, app: ASGIApp, xylem: "Xylem"):
        super().__init__(app)
        self.xylem = xylem

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request through middleware."""
        start_time = time.time()
        
        try:
            # Log request
            logging.info(f"Request: {request.method} {request.url.path}")
            
            # Let FastAPI handle the routing
            response = await call_next(request)
            
            # Log response
            logging.info(f"Response: {response.status_code} in {time.time() - start_time:.3f}s")
            
            return response

        except Exception as e:
            logging.error(f"Middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"}
            )
