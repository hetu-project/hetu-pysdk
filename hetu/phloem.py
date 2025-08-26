"""Create and initialize Phloem, which handles requests to other neurons."""

import os
import time
import logging
import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List, Union
from collections import defaultdict

from hetu.synapse import Synapse
from hetu.xylem import Xylem

class Phloem:
    """
    The Phloem class provides a client interface for making requests to Xylem servers.
    It handles connection management, request routing, and response processing.
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
        """Initialize the Phloem client.
        
        Args:
            username (str): Wallet username (optional if wallet is provided)
            password (str): Wallet password (deprecated, use wallet parameter instead)
            wallet_path (Optional[str]): Custom wallet path
            netuid (int): Subnet ID to operate on
            network (str): Network name (mainnet, testnet, etc.)
            hetutensor (Optional[Hututensor]): Hetutensor client instance
            wallet (Optional[Account]): Pre-initialized wallet Account object
        """
        # --- Network Configuration ---
        self.netuid = netuid
        self.network = network
        
        # --- Wallet ---
        self.username = username
        self.password = password
        self.wallet_path = wallet_path
        self.wallet = wallet

        # --- Hetutensor ---
        if hetutensor:
            self.hetu = hetutensor
        else:
            from hetu.hetu import Hetutensor
            if wallet:
                self.hetu = Hetutensor(network=self.network, wallet=wallet, log_verbose=True)
            else:
                self.hetu = Hetutensor(network=self.network, username=self.username, wallet_path=self.wallet_path, log_verbose=True)
        
        if wallet:
            self.wallet_address = wallet.address
            logging.info(f"Using pre-initialized wallet: {self.wallet_address}")
        elif self.username and not wallet: # Crucial fix here
            success = self.hetu.set_wallet_from_username(self.username, self.wallet_path)
            if success:
                self.wallet_address = self.hetu.get_wallet_address()
                logging.info(f"Wallet initialized: {self.wallet_address}")
            else:
                logging.warning("Failed to initialize wallet")
                self.wallet_address = None
        else:
            logging.warning("No wallet credentials provided")
            self.wallet_address = None

        # --- Session Management ---
        self._session = None
        self._session_lock = asyncio.Lock()
        
        # Validate validator status
        self._validate_validator_status()

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
                    f"💡 You need to register as a neuron first before using Phloem.\n"
                    f"   Use hetutensor.register_neuron() to register, or use the serve() method.\n"
                    f"   Example: phloem.serve(netuid={self.netuid})"
                )
                logging.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Check if wallet is a validator (not a miner)
            is_validator = self.hetu.is_validator(self.netuid, self.wallet_address)
            if not is_validator:
                error_msg = (
                    f"❌ Wallet {self.wallet_address} is not a validator on subnet {self.netuid}.\n"
                    f"💡 Only validators can use Phloem clients. Miners should use Xylem servers.\n"
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

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    timeout = aiohttp.ClientTimeout(total=30)
                    self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def forward(
        self,
        synapse: Synapse,
        target_xylem: Union[str, Xylem],
        timeout: Optional[float] = None
    ) -> Synapse:
        """Forward a synapse to a target Xylem server.
        
        Args:
            synapse (Synapse): The synapse to forward
            target_xylem (Union[str, Xylem]): Target Xylem server or endpoint URL
            timeout (Optional[float]): Request timeout in seconds
            
        Returns:
            Synapse: Response synapse from the target
        """
        try:
            session = await self._get_session()
            
            # Determine target URL
            if isinstance(target_xylem, Xylem):
                target_url = f"http://{target_xylem.ip}:{target_xylem.port}"
            else:
                target_url = target_xylem
            
            # Get synapse class name for endpoint
            synapse_class = synapse.__class__.__name__
            endpoint_url = f"{target_url}/{synapse_class}"
            
            # Prepare request data
            request_data = synapse.to_dict()
            
            # Make request
            async with session.post(
                endpoint_url,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=timeout or 30)
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    # Update synapse with response data
                    synapse.from_dict(response_data)
                    return synapse
                else:
                    error_text = await response.text()
                    synapse.set_error(f"HTTP {response.status}: {error_text}")
                    return synapse
                    
        except asyncio.TimeoutError:
            synapse.set_error("Request timeout")
            return synapse
        except Exception as e:
            synapse.set_error(f"Request failed: {str(e)}")
            return synapse

    async def forward_to_multiple(
        self,
        synapse: Synapse,
        target_xylems: List[Union[str, Xylem]],
        timeout: Optional[float] = None
    ) -> List[Synapse]:
        """Forward a synapse to multiple Xylem servers concurrently.
        
        Args:
            synapse (Synapse): The synapse to forward
            target_xylems (List[Union[str, Xylem]]): List of target Xylem servers
            timeout (Optional[float]): Request timeout in seconds
            
        Returns:
            List[Synapse]: List of response synapses from all targets
        """
        tasks = []
        for target in target_xylems:
            # Create a copy of the synapse for each target
            synapse_copy = synapse.__class__.from_dict(synapse.to_dict())
            task = self.forward(synapse_copy, target, timeout)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid responses
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Forward request failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results

    def discover_xylem_services(self) -> List[Dict[str, Any]]:
        """Discover available Xylem services from the network.
        
        Returns:
            List[Dict[str, Any]]: List of available Xylem service information
        """
        try:
            # Get metagraph to discover services
            metagraph = self.hetu.get_metagraph(self.netuid)
            if not metagraph:
                logging.warning("Could not get metagraph for service discovery")
                return []
            
            # Extract Xylem service information
            xylem_services = []
            for neuron in metagraph.neurons:
                if hasattr(neuron, 'axon_info') and neuron.axon_info:
                    service_info = {
                        'ip': neuron.axon_info.ip,
                        'port': neuron.axon_info.port,
                        'wallet_address': neuron.wallet_address,
                        'stake': neuron.stake,
                        'is_active': neuron.is_active
                    }
                    xylem_services.append(service_info)
            
            logging.info(f"Discovered {len(xylem_services)} Xylem services")
            return xylem_services
            
        except Exception as e:
            logging.error(f"Failed to discover Xylem services: {e}")
            return []

    def serve(
        self,
        netuid: Optional[int] = None,
        hetutensor: Optional["Hetutensor"] = None,
    ) -> "Phloem":
        """Start serving on network.
        
        Args:
            netuid (Optional[int]): Network ID to serve on (overrides constructor netuid)
            hetutensor (Optional[Hututensor]): Hetutensor client (overrides constructor)
        """
        try:
            target_netuid = netuid if netuid is not None else self.netuid
            target_hetutensor = hetutensor if hetutensor is not None else self.hetu
            
            if not target_hetutensor:
                raise ValueError("No Hetutensor client available")

            if not target_hetutensor.has_wallet():
                raise ValueError("No wallet available")

            wallet_address = target_hetutensor.get_wallet_address()
            is_registered = target_hetutensor.is_neuron(target_netuid, wallet_address)
            
            if not is_registered:
                success = target_hetutensor.register_neuron(
                    netuid=target_netuid,
                    is_validator_role=True,
                    axon_endpoint="",  # Validators don't need axon endpoints
                    axon_port=0,
                    prometheus_endpoint="",
                    prometheus_port=0
                )
                if not success:
                    raise ValueError("Failed to register neuron")
                logging.info(f"Registered as validator on subnet {target_netuid}")
            else:
                logging.info(f"Already registered as validator on subnet {target_netuid}")

            if target_netuid != self.netuid:
                self.netuid = target_netuid
                logging.info(f"Switched to subnet {target_netuid}")

            logging.info(f"Phloem client is now serving on subnet {target_netuid}")
            return self

        except Exception as e:
            logging.error(f"Failed to serve: {e}")
            raise

    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status information.
        
        Returns:
            Dict[str, Any]: Network status information
        """
        try:
            metagraph = self.hetu.get_metagraph(self.netuid)
            if not metagraph:
                return {"error": "Could not get metagraph"}
            
            return {
                "netuid": self.netuid,
                "network": self.network,
                "total_neurons": len(metagraph.neurons),
                "active_neurons": sum(1 for n in metagraph.neurons if n.is_active),
                "total_stake": metagraph.total_stake,
                "current_block": metagraph.block
            }
        except Exception as e:
            return {"error": f"Failed to get network status: {e}"}

    def get_available_services(self) -> List[str]:
        """Get list of available service types from the network.
        
        Returns:
            List[str]: List of available service class names
        """
        try:
            xylem_services = self.discover_xylem_services()
            # This would need to be implemented based on actual service discovery
            # For now, return a placeholder
            return ["MathService", "PingService"]  # Placeholder
        except Exception as e:
            logging.error(f"Failed to get available services: {e}")
            return []

    def get_available_validators(self) -> List[Dict[str, Any]]:
        """Get list of available validators on the subnet.
        
        Returns:
            List[Dict[str, Any]]: List of validator information
        """
        try:
            metagraph = self.hetu.get_metagraph(self.netuid)
            if not metagraph:
                return []
            
            validators = []
            for neuron in metagraph.neurons:
                if neuron.is_validator:
                    validator_info = {
                        'wallet_address': neuron.wallet_address,
                        'stake': neuron.stake,
                        'is_active': neuron.is_active,
                        'last_update': neuron.last_update
                    }
                    validators.append(validator_info)
            
            return validators
        except Exception as e:
            logging.error(f"Failed to get available validators: {e}")
            return []

    def is_network_healthy(self) -> bool:
        """Check if the network is healthy.
        
        Returns:
            bool: True if network is healthy, False otherwise
        """
        try:
            status = self.get_network_status()
            if "error" in status:
                return False
            
            # Basic health checks
            if status.get("total_neurons", 0) == 0:
                return False
            
            if status.get("active_neurons", 0) == 0:
                return False
            
            return True
        except Exception:
            return False

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def __del__(self):
        """Cleanup on deletion."""
        try:
            if hasattr(self, '_session') and self._session and not self._session.closed:
                asyncio.create_task(self.close())
        except Exception:
            pass

    def __str__(self) -> str:
        """String representation."""
        return f"Phloem(netuid={self.netuid}, network={self.network})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Phloem(netuid={self.netuid}, network={self.network}, wallet={self.wallet_address})"
