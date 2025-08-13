from __future__ import annotations

import asyncio
import time
import uuid
import logging
from typing import Any, AsyncGenerator, Optional, Union, Type

import aiohttp
from eth_account import Account
from eth_account.messages import encode_defunct
from pydantic import BaseModel

from hetu.axon import Axon
from hetu.synapse import Synapse

# Error mapping
DENDRITE_ERROR_MAPPING = {
    aiohttp.ClientConnectorError: ("503", "Service unavailable"),
    asyncio.TimeoutError: ("408", "Request timeout"),
    aiohttp.ClientPayloadError: ("400", "Payload error"),
    aiohttp.ClientError: ("500", "Client error"),
    aiohttp.ServerTimeoutError: ("504", "Server timeout error"),
    aiohttp.ServerDisconnectedError: ("503", "Service disconnected"),
}
DENDRITE_DEFAULT_ERROR = ("422", "Failed to parse response")

def get_external_ip() -> str:
    """Get external IP address (simplified version)"""
    try:
        import socket
        # Create a UDP connection to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

class Dendrite:
    """
    Dendrite is an HTTP client used to send requests to Axon servers.
    It supports synchronous and asynchronous operations, including basic request validation and error handling.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        wallet_path: Optional[str] = None,
        hetutensor = None
    ):
        """Initialize Dendrite

        Args:
            username: Wallet username
            password: Wallet password
            wallet_path: Wallet path
            hetutensor: Hetutensor client instance
        """
        # Initialize Hetutensor client
        if hetutensor:
            self.hetu = hetutensor
        else:
            from hetu.hetu import Hetutensor
            self.hetu = Hetutensor(
                username=username,
                password=password,
                wallet_path=wallet_path
            )

        # Basic attributes
        self.uuid = str(uuid.uuid1())
        self.external_ip = get_external_ip()
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    async def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def query(
        self,
        axons: Union[list[Axon], Axon],
        synapse: Synapse = Synapse(),
        timeout: float = 12.0,
        run_async: bool = True
    ) -> Union[Synapse, list[Synapse]]:
        """Send request to one or more Axons

        Args:
            axons: Target Axon or list of Axons
            synapse: Request data
            timeout: Timeout in seconds
            run_async: Whether to process multiple requests in parallel

        Returns:
            Single response or list of responses
        """
        is_list = isinstance(axons, list)
        if not is_list:
            axons = [axons]

        async def process_request(target_axon: Axon) -> Synapse:
            """Process a single request"""
            # Build request URL
            url = f"http://{target_axon.ip}:{target_axon.port}/"
            
            # Prepare request data
            request_synapse = synapse.model_copy()
            request_synapse.timeout = timeout
            
            # Add signature
            if self.hetu.has_wallet():
                message = f"{self.uuid}.{self.hetu.get_wallet_address()}.{url}"
                signable = encode_defunct(text=message)
                signature = self.hetu.wallet.sign_message(signable).signature
                request_synapse.signature = f"0x{signature.hex()}"

            try:
                # Send request
                async with (await self.session).post(
                    url=url,
                    json=request_synapse.model_dump(),
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    # Process response
                    json_response = await response.json()
                    
                    if response.status == 200:
                        # Successful response
                        return request_synapse.__class__(**json_response)
                    else:
                        # Error response
                        request_synapse.error = json_response.get("error", "Unknown error")
                        request_synapse.status_code = response.status
                        return request_synapse

            except Exception as e:
                # Handle error
                error_code, error_msg = DENDRITE_ERROR_MAPPING.get(
                    type(e), DENDRITE_DEFAULT_ERROR
                )
                request_synapse.error = f"{error_msg}: {str(e)}"
                request_synapse.status_code = int(error_code)
                return request_synapse

        # Process requests
        if run_async and len(axons) > 1:
            # Process multiple requests in parallel
            responses = await asyncio.gather(
                *(process_request(axon) for axon in axons)
            )
        else:
            # Process requests sequentially
            responses = []
            for axon in axons:
                responses.append(await process_request(axon))

        # Return result
        return responses[0] if len(responses) == 1 and not is_list else responses

    async def close(self):
        """Close session"""
        if self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        """Async context manager exit"""
        await self.close()

    def __del__(self):
        """Destructor"""
        if self._session and not self._session.closed:
            logging.warning("Dendrite session was not properly closed")
