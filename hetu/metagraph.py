import asyncio
import contextlib
import copy
import os
import pickle
import typing
from abc import ABC, abstractmethod
from os import listdir
from os.path import join
from typing import Optional, Union, List

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
    """

    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional[Union["AsyncHetutensor", "Hetutensor"]] = None,
    ):
        """Initialize metagraph with basic attributes."""
        self.netuid = netuid
        self.network = network
        self.hetutensor = hetutensor
        self.should_sync = sync
        
        # Basic attributes
        self.block = 0
        
        # Subnet specific
        self.is_active = False
        self.hyperparameters = {}
        
        # Neuron collections
        self.axons: List[NeuronInfo] = []      # Miner neurons (non-validator)
        self.dendrites: List[NeuronInfo] = []  # Validator neurons

        if sync and hetutensor:
            self.sync()

    def sync(self):
        """Synchronize metagraph with current network state."""
        if not self.hetutensor:
            return

        try:
            # Get current block
            self.block = self.hetutensor.get_current_block()
            
            # Get subnet info
            subnet_info = self.hetutensor.get_subnet_info(self.netuid)
            if subnet_info:
                self.is_active = subnet_info.is_active
                
            # Get hyperparameters
            self.hyperparameters = self.hetutensor.get_subnet_hyperparams(self.netuid)
            
            # Sync neurons (axons and dendrites)
            self._sync_neurons()
            
        except Exception as e:
            logging.error(f"Error during metagraph sync: {e}")

    def _sync_neurons(self):
        """Synchronize neuron information and separate into axons and dendrites."""
        try:
            # Get all neurons in the subnet
            neuron_addresses = self.hetutensor.get_subnet_neurons(self.netuid)
            
            # Clear existing collections
            self.axons.clear()
            self.dendrites.clear()
            
            # Process each neuron
            for address in neuron_addresses:
                neuron_info = self.hetutensor.get_neuron_info(self.netuid, address)
                if neuron_info:
                    # Create NeuronInfo object
                    neuron = NeuronInfo(
                        hotkey=address,
                        coldkey=neuron_info.get("account", ""),
                        uid=0,  # Will be set if available
                        netuid=self.netuid,
                        active=neuron_info.get("is_active", False),
                        stake=neuron_info.get("stake", 0),
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
                        axon_info=AxonInfo(
                            version=1,
                            ip=neuron_info.get("axon_endpoint", "0.0.0.0"),
                            port=neuron_info.get("axon_port", 0),
                            ip_type=4,  # IPv4
                            hotkey=address,
                            coldkey=neuron_info.get("account", ""),
                            protocol=4
                        ) if neuron_info.get("axon_endpoint") else None,
                        is_null=False
                    )
                    
                    # Separate into axons (miners) and dendrites (validators)
                    if neuron_info.get("is_validator", False):
                        self.dendrites.append(neuron)
                    else:
                        self.axons.append(neuron)
            
            logging.info(f"Synced {len(self.axons)} axons (miners) and {len(self.dendrites)} dendrites (validators) for subnet {self.netuid}")
            
        except Exception as e:
            logging.error(f"Error syncing neurons: {e}")

    def get_axons(self) -> List[NeuronInfo]:
        """Get list of miner neurons (axons)."""
        return self.axons

    def get_dendrites(self) -> List[NeuronInfo]:
        """Get list of validator neurons (dendrites)."""
        return self.dendrites

    def get_neuron_by_address(self, address: str) -> Optional[NeuronInfo]:
        """Get neuron by hotkey address."""
        for neuron in self.axons + self.dendrites:
            if neuron.hotkey == address:
                return neuron
        return None

    def get_neuron_by_uid(self, uid: int) -> Optional[NeuronInfo]:
        """Get neuron by UID."""
        for neuron in self.axons + self.dendrites:
            if neuron.uid == uid:
                return neuron
        return None

    def __str__(self) -> str:
        """String representation of metagraph."""
        return f"metagraph(netuid:{self.netuid}, block:{self.block}, network:{self.network}, axons:{len(self.axons)}, dendrites:{len(self.dendrites)})"

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
            "axon_count": len(self.axons),
            "dendrite_count": len(self.dendrites),
        }

    def state_dict(self):
        """Get metagraph state dictionary."""
        return {
            "netuid": self.netuid,
            "network": self.network,
            "block": self.block,
            "is_active": self.is_active,
            "hyperparameters": self.hyperparameters,
            "axons": [axon.__dict__ for axon in self.axons],
            "dendrites": [dendrite.__dict__ for dendrite in self.dendrites],
        }

class Metagraph(MetagraphMixin):
    """Synchronous metagraph implementation."""
    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional["Hetutensor"] = None,
    ):
        super().__init__(netuid, network, lite, sync, hetutensor)

class AsyncMetagraph(MetagraphMixin):
    """Placeholder for async metagraph implementation."""
    def __init__(
        self,
        netuid: int,
        network: str = settings.DEFAULT_NETWORK,
        lite: bool = True,
        sync: bool = True,
        hetutensor: Optional["AsyncHetutensor"] = None,
    ):
        super().__init__(netuid, network, lite, sync, hetutensor)
