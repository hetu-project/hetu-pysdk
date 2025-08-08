import asyncio
import contextlib
import copy
import os
import pickle
import typing
from abc import ABC, abstractmethod
from os import listdir
from os.path import join
from typing import Optional, Union

import numpy as np
from hetu.errors import HetuRequestException
from numpy.typing import NDArray
from packaging import version

from hetu import settings
from hetu.utils.btlogging import logging

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
            
        except Exception as e:
            logging.error(f"Error during metagraph sync: {e}")

    def __str__(self) -> str:
        """String representation of metagraph."""
        return f"metagraph(netuid:{self.netuid}, block:{self.block}, network:{self.network})"

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
        }

    def state_dict(self):
        """Get metagraph state dictionary."""
        return {
            "netuid": self.netuid,
            "network": self.network,
            "block": self.block,
            "is_active": self.is_active,
            "hyperparameters": self.hyperparameters,
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
