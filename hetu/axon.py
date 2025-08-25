"""Create and initialize Axon, which services the forward and backward requests from other neurons."""

import os
import time
import uvicorn
import logging
import asyncio
import threading
import contextlib
from typing import Optional, Callable, Any, Union
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from fastapi import FastAPI

from hetu.utils.priority import PriorityThreadPoolExecutor
from hetu.synapse import Synapse

class FastAPIThreadedServer(uvicorn.Server):
    """
    The FastAPIThreadedServer class runs the FastAPI application in a separate thread.
    This allows the Axon server to handle HTTP requests concurrently.
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

class Axon:
    """
    The Axon class provides a FastAPI-based HTTP server for handling network requests.
    It supports basic authentication, request prioritization, and health checks.
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
        """Initialize the Axon server.
        
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
        self.forward_fn = None
        self.blacklist_fn = None
        self.priority_fn = None
        self.verify_fn = None

        # --- Hetutensor ---
        self.hetutensor = hetutensor
        self.wallet_address = None
        
        # Initialize Hetutensor if not provided
        if not self.hetutensor:
            self._init_hetutensor()
        
        # Validate miner status
        self._validate_miner_status()

        # --- FastAPI ---
        self.app = FastAPI()
        self.app.add_middleware(
            AxonMiddleware,
            axon=self
        )

        # --- Default endpoints ---
        @self.app.post("/ping")
        def ping():
            """Basic health check endpoint."""
            return {"completion": "pong", "status": "ok"}

        @self.app.get("/ping")
        def ping_get():
            """GET ping endpoint for simple health check."""
            return {"completion": "pong", "status": "ok"}

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
                    f"💡 You need to register as a neuron first before starting an Axon server.\n"
                    f"   Use hetutensor.register_neuron() to register, or use the serve() method.\n"
                    f"   Example: axon.serve(netuid={self.netuid})"
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Check if wallet is a miner (not a validator)
            is_miner = self.hetutensor.is_miner(self.netuid, self.wallet_address)
            if not is_miner:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not a miner on subnet {self.netuid}.\n"
                    f"💡 Only miners can run Axon servers. Validators cannot run compute services.\n"
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
            'username': self.username
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
    ) -> "Axon":
        """Attach handler functions to the server.
        
        Args:
            forward_fn (Callable): Main request handler
            blacklist_fn (Optional[Callable]): Function to check if request should be blacklisted
            priority_fn (Optional[Callable]): Function to determine request priority
            verify_fn (Optional[Callable]): Function to verify request
        """
        self.forward_fn = forward_fn
        self.blacklist_fn = blacklist_fn
        self.priority_fn = priority_fn
        self.verify_fn = verify_fn

        async def endpoint(request: Request):
            """Main endpoint that forwards requests to handler function."""
            try:
                if not self.forward_fn:
                    return {"completion": "No forward function attached", "status_code": 500}
                
                # Get request body
                body = await request.json()
                
                # Create Synapse object
                synapse = Synapse.from_dict(body)
                
                # Call forward function
                result = await self.forward_fn(synapse)
                
                # If the result is a Synapse object, check status code and return appropriate response
                if hasattr(result, 'to_dict'):
                    synapse_dict = result.to_dict()
                    status_code = synapse_dict.get('status_code', 200)
                    
                    # If there's an error, return error response with proper status code
                    if synapse_dict.get('error'):
                        return JSONResponse(
                            status_code=status_code,
                            content=synapse_dict
                        )
                    
                    # Return success response
                    return synapse_dict
                else:
                    return result
                    
            except Exception as e:
                logging.error(f"Forward function error: {e}")
                return {"completion": f"Error processing request: {e}", "status_code": 500}

        self.app.add_api_route("/", endpoint, methods=["POST"])
        return self

    async def verify_body_integrity(self, request: Request):
        """Verify request body integrity."""
        try:
            body = await request.body()
            if not body:
                return False
            return True
        except Exception as e:
            logging.error(f"Body integrity check failed: {e}")
            return False

    def to_string(self):
        """Get string representation."""
        return self.__str__()

    def __str__(self) -> str:
        """String representation."""
        return f"Axon({self.ip}:{self.port})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Axon(ip:{self.ip}, port:{self.port}, external_ip:{self.external_ip}, external_port:{self.external_port})"

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if hasattr(self, 'started') and self.started:
                self.stop()
        except Exception:
            pass  # Ignore errors during cleanup

    def start(self) -> "Axon":
        """Start the server."""
        if not self.started:
            log_level = "trace" if self.trace else "info"
            self.fast_config = uvicorn.Config(
                self.app,
                host=self.ip,
                port=self.port,
                log_level=log_level
            )
            self.fast_server = FastAPIThreadedServer(config=self.fast_config)
            self.fast_server.start()
            
            # Wait for server to fully start
            max_wait = 10  # Max wait 10 seconds
            wait_time = 0
            while not self.fast_server.started and wait_time < max_wait:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self.fast_server.started:
                self.started = True
                logging.info(f"Axon server started successfully on {self.ip}:{self.port}")
            else:
                logging.error("Axon server failed to start within timeout")
                raise RuntimeError("Server startup timeout")
                
        return self

    def stop(self) -> "Axon":
        """Stop the server."""
        if self.started and hasattr(self, 'fast_server'):
            self.fast_server.stop()
            self.started = False
        return self

    def serve(
        self,
        netuid: Optional[int] = None,
        hetutensor: Optional["Hetutensor"] = None,
    ) -> "Axon":
        """Start serving on network.
        
        Args:
            netuid (Optional[int]): Network ID to serve on (overrides constructor netuid)
            hetutensor (Optional[Hututensor]): Hetutensor client (overrides constructor)
        """
        try:
            # Use provided parameters or fall back to constructor values
            target_netuid = netuid if netuid is not None else self.netuid
            target_hetutensor = hetutensor if hetutensor is not None else self.hetutensor
            
            if not target_hetutensor:
                raise ValueError("No Hetutensor client available")

            if not target_hetutensor.has_wallet():
                raise ValueError("No wallet available")

            # Check if already registered
            wallet_address = target_hetutensor.get_wallet_address()
            is_registered = target_hetutensor.is_neuron(target_netuid, wallet_address)
            
            if not is_registered:
                # Register as neuron
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
                # Update service info
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

            # Update metagraph if netuid changed
            if target_netuid != self.netuid:
                self.netuid = target_netuid
                # self._init_metagraph() # Removed as per edit hint
                logging.info(f"Switched to subnet {target_netuid}")

            # Start server
            self.start()
            return self

        except Exception as e:
            logging.error(f"Failed to serve: {e}")
            raise

    async def default_verify(self, synapse: "Synapse"):
        """Default verification - always passes."""
        return True

def create_error_response(synapse: "Synapse") -> "JSONResponse":
    """Create error response from synapse."""
    status_code = getattr(synapse, "status_code", 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": synapse.completion if hasattr(synapse, "completion") else "Unknown error"
        }
    )

def log_and_handle_error(
    synapse: "Synapse",
    exception: Exception,
    status_code: Optional[int] = None,
    start_time: Optional[float] = None,
) -> "Synapse":
    """Log error and update synapse."""
    error_msg = str(exception)
    logging.error(f"Error processing request: {error_msg}")
    
    synapse.completion = error_msg
    if status_code:
        synapse.status_code = status_code
        
    if start_time:
        synapse.process_time = time.time() - start_time
        
    return synapse

class AxonMiddleware(BaseHTTPMiddleware):
    """Middleware for request processing."""

    def __init__(self, app: ASGIApp, axon: "Axon"):
        super().__init__(app)
        self.axon = axon

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request through middleware."""
        start_time = time.time()
        
        try:
            # Skip body validation for ping endpoint
            if request.url.path == "/ping":
                return await call_next(request)
            
            # Check body
            if not await self.axon.verify_body_integrity(request):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request body"}
                )

            # Create synapse
            synapse = await self.preprocess(request)
            
            # Run verification
            if self.axon.verify_fn:
                try:
                    await self.verify(synapse)
                except Exception as e:
                    return create_error_response(
                        log_and_handle_error(synapse, e, 401, start_time)
                    )

            # Check blacklist
            if self.axon.blacklist_fn:
                try:
                    await self.blacklist(synapse)
                except Exception as e:
                    return create_error_response(
                        log_and_handle_error(synapse, e, 403, start_time)
                    )

            # Get priority
            priority = 0.0
            if self.axon.priority_fn:
                try:
                    priority = await self.priority(synapse)
                except Exception as e:
                    logging.warning(f"Priority error (using 0.0): {e}")

            # Process request
            return await self.run(synapse, call_next, request)

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"}
            )

    async def preprocess(self, request: Request) -> "Synapse":
        """Create synapse from request."""
        try:
            # Get request data
            body = await request.json()
            
            # Create synapse
            synapse = Synapse.from_dict(body)
            
            # Note: Do not add non-existent attributes to avoid validation errors
            # synapse.request_ip = request.client.host
            # synapse.request_headers = dict(request.headers)
            
            return synapse
            
        except Exception as e:
            raise ValueError(f"Failed to process request: {e}")

    async def verify(self, synapse: "Synapse"):
        """Run verification."""
        if not await self.axon.verify_fn(synapse):
            raise ValueError("Verification failed")

    async def blacklist(self, synapse: "Synapse"):
        """Check blacklist."""
        if await self.axon.blacklist_fn(synapse):
            raise ValueError("Request blacklisted")

    async def priority(self, synapse: "Synapse") -> float:
        """Get request priority."""
        return await self.axon.priority_fn(synapse)

    async def run(
        self,
        synapse: "Synapse",
        call_next: RequestResponseEndpoint,
        request: Request,
    ) -> Response:
        """Process request through handler."""
        try:
            # Call handler
            response = await call_next(request)
            
            # Convert to synapse response
            return await self.synapse_to_response(
                synapse,
                time.time(),
                response_override=response
            )
            
        except Exception as e:
            return create_error_response(
                log_and_handle_error(synapse, e, 500)
            )

    @classmethod
    async def synapse_to_response(
        cls,
        synapse: "Synapse",
        start_time: float,
        *,
        response_override: Optional[Response] = None
    ) -> Response:
        """Convert synapse to response."""
        if response_override is not None:
            return response_override
            
        synapse.process_time = time.time() - start_time
        
        status_code = getattr(synapse, "status_code", 200)
        return JSONResponse(
            status_code=status_code,
            content=synapse.to_dict()
        )

    def get_network_status(self) -> dict:
        """Get current network status from metagraph."""
        # Removed as per edit hint
        return {"error": "Network status not available in this simplified Axon"}

    def get_available_services(self) -> list:
        """Get list of available compute services (axons) from metagraph."""
        # Removed as per edit hint
        return []

    def get_available_validators(self) -> list:
        """Get list of available validators (dendrites) from metagraph."""
        # Removed as per edit hint
        return []

    def sync_metagraph(self, force: bool = False):
        """Sync metagraph with current network state."""
        # Removed as per edit hint
        logging.warning("sync_metagraph is not available in this simplified Axon")

    def is_network_healthy(self) -> bool:
        """Check if the network is healthy based on metagraph data."""
        # Removed as per edit hint
        return False
