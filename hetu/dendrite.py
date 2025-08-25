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
    Only validators can start Dendrite clients.
    """

    def __init__(
        self,
        username: str = None,
        password: str = None,
        wallet_path: Optional[str] = None,
        netuid: int = 1,
        network: str = "mainnet",
        hetutensor = None,
        wallet: Optional["Account"] = None,
    ):
        """Initialize Dendrite

        Args:
            username (str): Wallet username (optional if wallet is provided)
            password (str): Wallet password (deprecated, use wallet parameter instead)
            wallet_path: Wallet path
            netuid (int): Subnet ID to operate on
            network (str): Network name (mainnet, testnet, etc.)
            hetutensor: Hetutensor client instance
            wallet (Optional[Account]): Pre-initialized wallet Account object
        """
        # --- Network Configuration ---
        self.netuid = netuid
        self.network = network
        
        # --- Wallet ---
        self.username = username
        self.password = password  # Deprecated
        self.wallet_path = wallet_path
        
        # Initialize Hetutensor client
        if hetutensor:
            self.hetu = hetutensor
        else:
            from hetu.hetu import Hetutensor
            if wallet:
                # Use pre-initialized wallet
                self.hetu = Hetutensor(
                    network=self.network,
                    wallet=wallet,
                    log_verbose=True
                )
            else:
                # Use username-based initialization
                self.hetu = Hetutensor(
                    network=self.network,
                    username=self.username,
                    wallet_path=self.wallet_path,
                    log_verbose=True
                )
        
        # Initialize wallet if credentials provided
        if wallet:
            # Use pre-initialized wallet - no need to call set_wallet_from_username
            self.wallet_address = wallet.address
            logging.info(f"Using pre-initialized wallet: {self.wallet_address}")
        elif self.username:
            # Only call set_wallet_from_username if no wallet object was provided
            success = self.hetu.set_wallet_from_username(
                self.username, 
                self.wallet_path
            )
            if success:
                self.wallet_address = self.hetu.get_wallet_address()
                logging.info(f"Wallet initialized: {self.wallet_address}")
            else:
                logging.warning("Failed to initialize wallet")
                self.wallet_address = None
        else:
            logging.warning("No wallet credentials provided")
            self.wallet_address = None

        # Validate validator status
        self._validate_validator_status()

        # Basic attributes
        self.uuid = str(uuid.uuid1())
        self.external_ip = get_external_ip()
        self._session: Optional[aiohttp.ClientSession] = None

    def _validate_validator_status(self):
        """Validate that the user is a validator on the specified subnet."""
        if not self.hetu or not self.wallet_address:
            logging.error("Cannot validate validator status: no Hetutensor client or wallet")
            raise RuntimeError("No Hetutensor client or wallet available")
        
        try:
            # Check if wallet is a neuron
            is_neuron = self.hetu.is_neuron(self.netuid, self.wallet_address)
            if not is_neuron:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not registered as a neuron on subnet {self.netuid}.\n"
                    f"💡 You need to register as a neuron first before starting a Dendrite client.\n"
                    f"   Use hetutensor.register_neuron() to register, or use the serve() method.\n"
                    f"   Example: dendrite.serve(netuid={self.netuid})"
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Check if wallet is a validator (not a miner)
            is_validator = self.hetu.is_validator(self.netuid, self.wallet_address)
            if not is_validator:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not a validator on subnet {self.netuid}.\n"
                    f"💡 Only validators can run Dendrite clients. Miners cannot run validation services.\n"
                    f"   You need to register as a validator (not miner) on this subnet.\n"
                    f"   Use hetutensor.register_neuron(is_validator_role=True) to register as a validator."
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Get neuron info for additional validation
            neuron_info = self.hetu.get_neuron_info(self.netuid, self.wallet_address)
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
                
                logging.info(f"✅ Validator validation passed: {self.wallet_address} is an active validator on subnet {self.netuid}")
                logging.info(f"   Stake: {neuron_info.get('stake', 'N/A')}")
                logging.info(f"   Last Update: {neuron_info.get('last_update', 'N/A')}")
            else:
                logging.warning("Could not get detailed neuron info for validation")
                
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise  # Re-raise our custom errors
            logging.error(f"Failed to validate validator status: {e}")
            raise RuntimeError(f"Validator validation failed: {e}")

    def info(self) -> dict:
        """Return client info."""
        info = {
            'uuid': self.uuid,
            'external_ip': self.external_ip,
            'netuid': self.netuid,
            'network': self.network,
            'username': self.username
        }
        
        if self.wallet_address:
            info['wallet_address'] = self.wallet_address
            
        return info

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
        try:
            if hasattr(self, '_session') and self._session and not self._session.closed:
                logging.warning("Dendrite session was not properly closed")
        except Exception:
            pass  # Ignore errors during cleanup

    def serve(
        self,
        netuid: Optional[int] = None,
        hetutensor: Optional["Hetutensor"] = None,
    ) -> "Dendrite":
        """Start serving on network as a validator.
        
        Args:
            netuid (Optional[int]): Network ID to serve on (overrides constructor netuid)
            hetutensor (Optional[Hututensor]): Hetutensor client (overrides constructor)
        """
        try:
            # Use provided parameters or fall back to constructor values
            target_netuid = netuid if netuid is not None else self.netuid
            target_hetutensor = hetutensor if hetutensor is not None else self.hetu
            
            if not target_hetutensor:
                raise ValueError("No Hetutensor client available")

            if not target_hetutensor.has_wallet():
                raise ValueError("No wallet available")

            # Check if already registered
            wallet_address = target_hetutensor.get_wallet_address()
            is_registered = target_hetutensor.is_neuron(target_netuid, wallet_address)
            
            if not is_registered:
                # Register as validator neuron
                success = target_hetutensor.register_neuron(
                    netuid=target_netuid,
                    is_validator_role=True,  # Register as validator
                    axon_endpoint=self.external_ip,
                    axon_port=0,  # Validators don't need axon ports
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to register validator neuron")
                logging.info(f"Registered as validator neuron on subnet {target_netuid}")
            else:
                # Update service info
                success = target_hetutensor.update_service(
                    netuid=target_netuid,
                    axon_endpoint=self.external_ip,
                    axon_port=0,  # Validators don't need axon ports
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to update validator service info")
                logging.info(f"Updated validator service info on subnet {target_netuid}")

            # Update netuid if changed
            if target_netuid != self.netuid:
                self.netuid = target_netuid
                logging.info(f"Switched to subnet {target_netuid}")

            logging.info(f"✅ Dendrite client is now serving as validator on subnet {target_netuid}")
            return self

        except Exception as e:
            logging.error(f"Failed to serve: {e}")
            raise

    def get_network_status(self) -> dict:
        """Get current network status from hetutensor."""
        try:
            if not self.hetu:
                return {"error": "No Hetutensor client available"}
            
            # Get basic network info
            total_subnets = self.hetu.get_total_subnets()
            current_block = self.hetu.get_current_block()
            
            return {
                "total_subnets": total_subnets,
                "current_block": current_block,
                "network": self.network,
                "netuid": self.netuid
            }
        except Exception as e:
            return {"error": f"Failed to get network status: {e}"}

    def get_available_services(self) -> list:
        """Get list of available compute services (axons) from current subnet."""
        try:
            if not self.hetu:
                return []
            
            # Get miners (compute services) from current subnet
            miners = self.hetu.get_subnet_miners(self.netuid)
            return [{"address": addr, "type": "miner"} for addr in miners]
        except Exception as e:
            logging.warning(f"Failed to get available services: {e}")
            return []

    def get_available_validators(self) -> list:
        """Get list of available validators (dendrites) from current subnet."""
        try:
            if not self.hetu:
                return []
            
            # Get validators from current subnet
            validators = self.hetu.get_subnet_validators(self.netuid)
            return [{"address": addr, "type": "validator"} for addr in validators]
        except Exception as e:
            logging.warning(f"Failed to get available validators: {e}")
            return []

    def is_network_healthy(self) -> bool:
        """Check if the network is healthy based on current subnet data."""
        try:
            if not self.hetu:
                return False
            
            # Check if subnet exists and is active
            subnet_exists = self.hetu.is_subnet_exists(self.netuid)
            subnet_active = self.hetu.is_subnet_active(self.netuid)
            
            return subnet_exists and subnet_active
        except Exception as e:
            logging.warning(f"Failed to check network health: {e}")
            return False
