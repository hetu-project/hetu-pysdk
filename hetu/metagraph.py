import asyncio
import contextlib
import copy
import os
import pickle
import typing
import time
from abc import ABC, abstractmethod
from os import listdir
from os.path import join
from typing import Optional, Union, List, Dict, Any

import numpy as np
from hetu.errors import HetuRequestException
from numpy.typing import NDArray
from packaging import version

from hetu import settings
from hetu.utils.btlogging import logging
from hetu.chain_data import NeuronInfo, AxonInfo

# For annotation purposes
if typing.TYPE_CHECKING:
    from hetu.hetu import Hetutensor
    from hetu.async_hetutensor import AsyncHetutensor

class MetagraphMixin(ABC):
    """
    The metagraph class represents the neural graph that forms the backbone of the Hetuchain network.
    
    This class maintains the state of the network by tracking various attributes of subnets.

    Args:
        netuid (int): Network unique identifier
        network (str): Network name

    Attributes:
        netuid (int): Network unique identifier
        network (str): Network name
        block (int): Current block number
        is_active (bool): Whether subnet is active
        hyperparameters (dict): Subnet hyperparameters
        axons (List[NeuronInfo]): List of miner neurons (non-validator)
        dendrites (List[NeuronInfo]): List of validator neurons
        last_sync (float): Timestamp of last sync
        sync_interval (float): Minimum interval between syncs
    """

    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional[Union["AsyncHetutensor", "Hetutensor"]] = None,
        sync_interval: float = 5.0,  # 5 seconds minimum between syncs
    ):
        """Initialize metagraph with basic attributes."""
        self.netuid = netuid
        self.network = network
        self.hetutensor = hetutensor
        self.should_sync = sync
        self.sync_interval = sync_interval
        
        # Basic attributes
        self.block = 0
        self.last_sync = 0.0
        
        # Subnet specific
        self.is_active = False
        self.hyperparameters = {}
        
        # Neuron collections
        self.xylems: List[NeuronInfo] = []      # Miner neurons (non-validator)
        self.phloems: List[NeuronInfo] = []  # Validator neurons
        
        # Cached data for performance
        self._neuron_cache: Dict[str, NeuronInfo] = {}
        self._cache_timestamp = 0.0
        self._cache_duration = 30.0  # 30 seconds cache duration

        if sync and hetutensor:
            self.sync()

    def sync(self, force: bool = False):
        """
        Synchronize metagraph with current network state.
        
        Args:
            force (bool): Force sync even if within sync interval
        """
        if not self.hetutensor:
            logging.warning("No Hetutensor client available for sync")
            return

        current_time = time.time()
        
        # Check if we need to sync
        if not force and (current_time - self.last_sync) < self.sync_interval:
            logging.debug(f"Sync skipped, last sync was {current_time - self.last_sync:.1f}s ago")
            return

        try:
            logging.info(f"Starting metagraph sync for subnet {self.netuid}")
            
            # Get current block
            self.block = self.hetutensor.get_current_block()
            logging.debug(f"Current block: {self.block}")
            
            # Get subnet info
            subnet_info = self.hetutensor.get_subnet_info(self.netuid)
            if subnet_info:
                self.is_active = subnet_info.is_active
                logging.debug(f"Subnet {self.netuid} active: {self.is_active}")
            else:
                logging.warning(f"Could not get subnet info for {self.netuid}")
                
            # Get hyperparameters
            self.hyperparameters = self.hetutensor.get_subnet_hyperparams(self.netuid) or {}
            logging.debug(f"Hyperparameters: {len(self.hyperparameters)} params")
            
            # Sync neurons (axons and dendrites)
            self._sync_neurons()
            
            # Update sync timestamp
            self.last_sync = current_time
            logging.info(f"Metagraph sync completed for subnet {self.netuid}")
            
        except Exception as e:
            logging.error(f"Error during metagraph sync: {e}")
            import traceback
            logging.error(f"Sync traceback: {traceback.format_exc()}")

    def _sync_neurons(self):
        """Synchronize neuron information and separate into axons and dendrites."""
        try:
            # Get all neurons in the subnet
            neuron_addresses = self.hetutensor.get_subnet_neurons(self.netuid)
            logging.debug(f"Found {len(neuron_addresses)} neurons in subnet {self.netuid}")
            
            if not neuron_addresses:
                logging.warning(f"No neurons found in subnet {self.netuid}")
                self.xylems.clear()
                self.phloems.clear()
                return
            
            # Clear existing collections
            self.xylems.clear()
            self.phloems.clear()
            self._neuron_cache.clear()
            
            # Process each neuron
            for address in neuron_addresses:
                try:
                    neuron_info = self.hetutensor.get_neuron_info(self.netuid, address)
                    if neuron_info:
                        # Create NeuronInfo object
                        neuron = self._create_neuron_info(address, neuron_info)
                        
                        # Only add neuron if creation was successful
                        if neuron is not None:
                            # Cache the neuron
                            self._neuron_cache[address] = neuron
                            
                            # Separate into xylems (miners) and phloems (validators)
                            if neuron_info.get("is_validator", False):
                                self.phloems.append(neuron)
                            else:
                                self.xylems.append(neuron)
                        else:
                            logging.warning(f"Failed to create NeuronInfo for {address}")
                    else:
                        logging.warning(f"Could not get neuron info for {address}")
                        
                except Exception as e:
                    logging.error(f"Error processing neuron {address}: {e}")
                    continue
            
            logging.info(f"Synced {len(self.xylems)} xylems (miners) and {len(self.phloems)} phloems (validators) for subnet {self.netuid}")
            
            # Update cache timestamp
            self._cache_timestamp = time.time()
            
        except Exception as e:
            logging.error(f"Error syncing neurons: {e}")
            import traceback
            logging.error(f"Neuron sync traceback: {traceback.format_exc()}")

    def _create_neuron_info(self, address: str, neuron_info: Dict[str, Any]) -> NeuronInfo:
        """Create NeuronInfo object from raw neuron data."""
        try:
            from hetu.utils.balance import Balance
            
            # Extract axon info if available
            axon_info = None
            if neuron_info.get("axon_endpoint") and neuron_info.get("axon_port"):
                axon_info = AxonInfo(
                    version=1,
                    ip=neuron_info.get("axon_endpoint", "0.0.0.0"),
                    port=neuron_info.get("axon_port", 0),
                    ip_type=4,  # IPv4
                    hotkey=address,
                    coldkey=neuron_info.get("account", ""),
                    protocol=4
                )
            
            # Create stake information
            stake_amount = neuron_info.get("stake", 0)
            stake_balance = Balance(stake_amount)
            
            # Create stake_dict (mapping of coldkey to amount staked)
            stake_dict = {}
            if neuron_info.get("account"):
                stake_dict[neuron_info.get("account")] = stake_balance
            
            # Create NeuronInfo
            neuron = NeuronInfo(
                hotkey=address,
                coldkey=neuron_info.get("account", ""),
                uid=0,  # Will be set if available
                netuid=self.netuid,
                active=neuron_info.get("is_active", False),
                stake=stake_balance,
                stake_dict=stake_dict,
                total_stake=stake_balance,
                        rank=0.0,
                        emission=0.0,
                        incentive=0.0,
                        consensus=0.0,
                        trust=0.0,
                        validator_trust=0.0,
                        dividends=0.0,
                        last_update=neuron_info.get("last_update", 0),
                        validator_permit=neuron_info.get("is_validator", False),
                        weights=[],
                        bonds=[],
                        pruning_score=0,
                        prometheus_info=None,
                axon_info=axon_info,
                        is_null=False
                    )
            
            return neuron
            
        except Exception as e:
            logging.error(f"Error creating NeuronInfo for {address}: {e}")
            # Return a minimal neuron info
            try:
                from hetu.utils.balance import Balance
                return NeuronInfo(
                    hotkey=address,
                    coldkey="",
                    uid=0,
                    netuid=self.netuid,
                    active=False,
                    stake=Balance(0),
                    stake_dict={},
                    total_stake=Balance(0),
                    rank=0.0,
                    emission=0.0,
                    incentive=0.0,
                    consensus=0.0,
                    trust=0.0,
                    validator_trust=0.0,
                    dividends=0.0,
                    last_update=0,
                    validator_permit=False,
                    weights=[],
                    bonds=[],
                    pruning_score=0,
                    prometheus_info=None,
                    axon_info=None,
                    is_null=True
                )
            except Exception as fallback_error:
                logging.error(f"Failed to create fallback NeuronInfo: {fallback_error}")
                # Return None if we can't even create a fallback
                return None

    def get_xylems(self, force_sync: bool = False) -> List[NeuronInfo]:
        """
        Get list of miner neurons (xylems).
        
        Args:
            force_sync (bool): Force sync before returning axons
            
        Returns:
            List[NeuronInfo]: List of xylem neurons
        """
        if force_sync:
            self.sync(force=True)
        return self.xylems

    def get_phloems(self, force_sync: bool = False) -> List[NeuronInfo]:
        """
        Get list of validator neurons (phloems).
        
        Args:
            force_sync (bool): Force sync before returning dendrites
            
        Returns:
            List[NeuronInfo]: List of phloem neurons
        """
        if force_sync:
            self.sync(force=True)
        return self.phloems

    def get_active_xylems(self, force_sync: bool = False) -> List[NeuronInfo]:
        """
        Get list of active miner neurons (xylems).
        
        Args:
            force_sync (bool): Force sync before returning axons
            
        Returns:
            List[NeuronInfo]: List of active xylem neurons
        """
        xylems = self.get_xylems(force_sync)
        return [xylem for xylem in xylems if xylem.active]

    def get_active_phloems(self, force_sync: bool = False) -> List[NeuronInfo]:
        """
        Get list of active validator neurons (phloems).
        
        Args:
            force_sync (bool): Force sync before returning dendrites
            
        Returns:
            List[NeuronInfo]: List of active phloem neurons
        """
        phloems = self.get_phloems(force_sync)
        return [phloem for phloem in phloems if phloem.active]

    def get_neuron_by_address(self, address: str, force_sync: bool = False) -> Optional[NeuronInfo]:
        """
        Get neuron by hotkey address.
        
        Args:
            address (str): Neuron hotkey address
            force_sync (bool): Force sync before looking up neuron
            
        Returns:
            Optional[NeuronInfo]: Neuron info if found, None otherwise
        """
        if force_sync:
            self.sync(force=True)
        
        # Check cache first
        if address in self._neuron_cache:
            return self._neuron_cache[address]
        
        # Search in xylems and phloems
        for neuron in self.xylems + self.phloems:
            if neuron.hotkey == address:
                return neuron
        return None

    def get_neuron_by_uid(self, uid: int, force_sync: bool = False) -> Optional[NeuronInfo]:
        """
        Get neuron by UID.
        
        Args:
            uid (int): Neuron UID
            force_sync (bool): Force sync before looking up neuron
            
        Returns:
            Optional[NeuronInfo]: Neuron info if found, None otherwise
        """
        if force_sync:
            self.sync(force=True)
        
        for neuron in self.xylems + self.phloems:
            if neuron.uid == uid:
                return neuron
        return None

    def get_neurons_with_xylem_endpoints(self, force_sync: bool = False) -> List[NeuronInfo]:
        """
        Get neurons that have valid xylem endpoints.
        
        Args:
            force_sync (bool): Force sync before returning neurons
            
        Returns:
            List[NeuronInfo]: List of neurons with xylem endpoints
        """
        if force_sync:
            self.sync(force=True)
        
        neurons_with_endpoints = []
        for neuron in self.xylems + self.phloems:
            if neuron.axon_info and neuron.axon_info.ip and neuron.axon_info.port > 0:
                neurons_with_endpoints.append(neuron)
        
        return neurons_with_endpoints

    def get_xylem_endpoints(self, force_sync: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of xylem endpoints with their information.
        
        Args:
            force_sync (bool): Force sync before returning endpoints
            
        Returns:
            List[Dict[str, Any]]: List of endpoint information
        """
        xylems = self.get_active_xylems(force_sync)
        endpoints = []
        
        for xylem in xylems:
            if xylem.axon_info and xylem.axon_info.ip and xylem.axon_info.port > 0:
                endpoints.append({
                    "address": xylem.hotkey,
                    "ip": xylem.axon_info.ip,
                    "port": xylem.axon_info.port,
                    "stake": xylem.stake,
                    "active": xylem.active,
                    "last_update": xylem.last_update
                })
        
        return endpoints

    def get_phloem_endpoints(self, force_sync: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of phloem endpoints with their information.
        
        Args:
            force_sync (bool): Force sync before returning endpoints
            
        Returns:
            List[Dict[str, Any]]: List of endpoint information
        """
        phloems = self.get_active_phloems(force_sync)
        endpoints = []
        
        for phloem in phloems:
            if phloem.axon_info and phloem.axon_info.ip and phloem.axon_info.port > 0:
                endpoints.append({
                    "address": phloem.hotkey,
                    "ip": phloem.axon_info.ip,
                    "port": phloem.axon_info.port,
                    "stake": phloem.stake,
                    "active": phloem.active,
                    "last_update": phloem.last_update
                })
        
        return endpoints

    def get_subnet_summary(self, force_sync: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive subnet summary.
        
        Args:
            force_sync (bool): Force sync before returning summary
            
        Returns:
            Dict[str, Any]: Subnet summary information
        """
        if force_sync:
            self.sync(force=True)
        
        total_stake = sum(neuron.stake for neuron in self.xylems + self.phloems)
        active_xylems = len(self.get_active_xylems())
        active_phloems = len(self.get_active_phloems())
        
        return {
            "netuid": self.netuid,
            "network": self.network,
            "block": self.block,
            "is_active": self.is_active,
            "total_neurons": len(self.xylems) + len(self.phloems),
            "total_xylems": len(self.xylems),
            "total_phloems": len(self.phloems),
            "active_xylems": active_xylems,
            "active_phloems": active_phloems,
            "total_stake": total_stake,
            "last_sync": self.last_sync,
            "hyperparameters": self.hyperparameters
        }

    def is_cache_valid(self) -> bool:
        """Check if the cached data is still valid."""
        return (time.time() - self._cache_timestamp) < self._cache_duration

    def clear_cache(self):
        """Clear the neuron cache."""
        self._neuron_cache.clear()
        self._cache_timestamp = 0.0

    def __str__(self) -> str:
        """String representation of metagraph."""
        return f"metagraph(netuid:{self.netuid}, block:{self.block}, network:{self.network}, xylems:{len(self.xylems)}, phloems:{len(self.phloems)})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()

    def metadata(self) -> dict:
        """Get metagraph metadata."""
        return {
            "netuid": self.netuid,
            "block": self.block,
            "network": self.network,
            "version": settings.__version__,
            "xylem_count": len(self.xylems),
            "phloem_count": len(self.phloems),
            "last_sync": self.last_sync,
            "cache_valid": self.is_cache_valid(),
        }

    def state_dict(self):
        """Get metagraph state dictionary."""
        return {
            "netuid": self.netuid,
            "network": self.network,
            "block": self.block,
            "is_active": self.is_active,
            "hyperparameters": self.hyperparameters,
            "xylems": [xylem.__dict__ for xylem in self.xylems],
            "phloems": [phloem.__dict__ for phloem in self.phloems],
            "last_sync": self.last_sync,
            "cache_timestamp": self._cache_timestamp,
        }

    def get_next_epoch_block(self, force_sync: bool = False) -> Optional[int]:
        """
        Get the next block number when epoch should run.
        
        Args:
            force_sync (bool): Force sync before calculating
            
        Returns:
            Optional[int]: Next epoch block number, or None if calculation fails
        """
        if force_sync:
            self.sync(force=True)
        
        try:
            # Get current block
            current_block = self.block
            if current_block == 0:
                self.sync(force=True)
                current_block = self.block
                if current_block == 0:
                    return None
            
            # Get tempo from hyperparameters
            tempo = self.hyperparameters.get("tempo")
            if tempo is None:
                return None
            
            # Calculate next epoch block
            # Find the next block that satisfies: (block + netuid + 1) % (tempo + 1) == 0
            current_result = (current_block + self.netuid + 1) % (tempo + 1)
            if current_result == 0:
                # We're already at an epoch block
                next_epoch_block = current_block + (tempo + 1)
            else:
                # Calculate blocks until next epoch
                blocks_until_epoch = (tempo + 1) - current_result
                next_epoch_block = current_block + blocks_until_epoch
            
            # Use simple logging check instead of getLogger
            if hasattr(logging, 'DEBUG') and logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"Next epoch calculation for subnet {self.netuid}:")
                logging.debug(f"  Current block: {current_block}")
                logging.debug(f"  Next epoch block: {next_epoch_block}")
                logging.debug(f"  Blocks until next epoch: {next_epoch_block - current_block}")
            
            return next_epoch_block
            
        except Exception as e:
            logging.error(f"Error calculating next epoch block for subnet {self.netuid}: {e}")
            return None

    def get_epoch_info(self, force_sync: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive epoch information.
        
        Args:
            force_sync (bool): Force sync before getting info
            
        Returns:
            Optional[Dict[str, Any]]: Epoch information including timing details
        """
        if force_sync:
            self.sync(force=True)
        
        try:
            current_block = self.block
            tempo = self.hyperparameters.get("tempo")
            
            if current_block == 0 or tempo is None:
                return None
            
            # Calculate current epoch status
            current_result = (current_block + self.netuid + 1) % (tempo + 1)
            is_epoch_block = current_result == 0
            
            # Calculate next epoch block
            if is_epoch_block:
                next_epoch_block = current_block + (tempo + 1)
                blocks_until_epoch = 0
            else:
                blocks_until_epoch = (tempo + 1) - current_result
                next_epoch_block = current_block + blocks_until_epoch
            
            epoch_info = {
                "netuid": self.netuid,
                "current_block": current_block,
                "tempo": tempo,
                "is_epoch_block": is_epoch_block,
                "current_result": current_result,
                "next_epoch_block": next_epoch_block,
                "blocks_until_epoch": blocks_until_epoch,
                "formula": f"({current_block} + {self.netuid} + 1) % ({tempo} + 1) = {current_result}",
                "should_run_epoch": is_epoch_block
            }
            
            return epoch_info
            
        except Exception as e:
            logging.error(f"Error getting epoch info for subnet {self.netuid}: {e}")
            return None

class Metagraph(MetagraphMixin):
    """Synchronous metagraph implementation."""
    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional["Hetutensor"] = None,
        sync_interval: float = 5.0,
    ):
        super().__init__(netuid, network, lite, sync, hetutensor, sync_interval)

class AsyncMetagraph(MetagraphMixin):
    """Placeholder for async metagraph implementation."""
    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional["AsyncHetutensor"] = None,
        sync_interval: float = 5.0,
    ):
        super().__init__(netuid, network, lite, sync, hetutensor, sync_interval)
