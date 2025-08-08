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

    @contextlib.contextmanager
    def run_in_thread(self):
        """Context manager to run server in a thread."""
        thread = threading.Thread(target=self._wrapper_run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()

    def _wrapper_run(self):
        """Wrapper to set running state."""
        self.run()
        self.is_running = False

    def start(self):
        """Start the server."""
        self.is_running = True
        self.run_in_thread().__enter__()

    def stop(self):
        """Stop the server."""
        if self.is_running:
            self.should_exit = True
            self.is_running = False

class Axon:
    """
    The Axon class provides a FastAPI-based HTTP server for handling network requests.
    It supports basic authentication, request prioritization, and health checks.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        wallet_path: Optional[str] = None,
        port: Optional[int] = None,
        ip: Optional[str] = None,
        external_ip: Optional[str] = None,
        external_port: Optional[int] = None,
        max_workers: Optional[int] = None,
        trace: bool = False,
    ):
        """Initialize the Axon server.
        
        Args:
            username (Optional[str]): Wallet username
            password (Optional[str]): Wallet password
            wallet_path (Optional[str]): Custom wallet path
            port (Optional[int]): Server port
            ip (Optional[str]): Server IP
            external_ip (Optional[str]): External IP for NAT
            external_port (Optional[int]): External port for NAT
            max_workers (Optional[int]): Max thread pool workers
            trace (bool): Enable trace logging
        """
        # --- Server Config ---
        self.ip = ip or os.getenv("HOST_IP", "127.0.0.1")
        self.port = port or int(os.getenv("PORT", "8091"))
        self.external_ip = external_ip or os.getenv("EXTERNAL_IP")
        self.external_port = external_port or int(os.getenv("EXTERNAL_PORT", "0"))
        self.max_workers = max_workers or int(os.getenv("MAX_WORKERS", "10"))
        self.trace = trace

        # --- Wallet ---
        self.username = username
        self.password = password
        self.wallet_path = wallet_path

        # --- Server ---
        self.started = False
        self.thread_pool = PriorityThreadPoolExecutor(max_workers=self.max_workers)
        self.forward_fn = None
        self.blacklist_fn = None
        self.priority_fn = None
        self.verify_fn = None

        # --- FastAPI ---
        self.app = FastAPI()
        self.app.add_middleware(
            AxonMiddleware,
            axon=self
        )

        # --- Default endpoints ---
        @self.app.post("/ping")
        def ping(r: Synapse) -> Synapse:
            """Basic health check endpoint."""
            r.completion = "pong"
            return r

    def info(self) -> dict:
        """Return server info."""
        return {
            'ip': self.ip,
            'port': self.port,
            'external_ip': self.external_ip,
            'external_port': self.external_port,
            'started': self.started
        }

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

        async def endpoint(*args, **kwargs):
            """Main endpoint that forwards requests to handler function."""
            try:
                return await self.forward_fn(*args, **kwargs)
            except Exception as e:
                logging.error(f"Forward function error: {e}")
                return Synapse(completion="Error processing request")

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
        self.stop()

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
            self.started = True
        return self

    def stop(self) -> "Axon":
        """Stop the server."""
        if self.started and hasattr(self, 'fast_server'):
            self.fast_server.stop()
            self.started = False
        return self

    def serve(
        self,
        netuid: int,
        hetutensor: Optional["Hetutensor"] = None,
    ) -> "Axon":
        """Start serving on network.
        
        Args:
            netuid (int): Network ID to serve on
            hetutensor (Optional[Hetutensor]): Hetutensor client
        """
        try:
            if not hetutensor:
                from hetu.hetu import Hetutensor
                hetutensor = Hetutensor(
                    username=self.username,
                    password=self.password,
                    wallet_path=self.wallet_path
                )

            if not hetutensor.has_wallet():
                raise ValueError("No wallet available")

            # Check if already registered
            is_registered = hetutensor.is_neuron(netuid, hetutensor.get_wallet_address())
            
            if not is_registered:
                # Register as neuron
                success = hetutensor.register_neuron(
                    netuid=netuid,
                    is_validator_role=False,
                    axon_endpoint=self.external_ip or self.ip,
                    axon_port=self.external_port or self.port,
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to register neuron")
            else:
                # Update service info
                success = hetutensor.update_service(
                    netuid=netuid,
                    axon_endpoint=self.external_ip or self.ip,
                    axon_port=self.external_port or self.port,
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to update service info")

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
            
            # Add request info
            synapse.request_ip = request.client.host
            synapse.request_headers = dict(request.headers)
            
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
