"""
The Hetutensor Compatibility Module is designed to ensure seamless integration and functionality with legacy versions of
the Hetutensor framework, specifically up to and including version 7.3.0. This module addresses changes and deprecated
features in recent versions, allowing users to maintain compatibility with older systems and projects.
"""

import importlib
import sys

from eth_account import Account

from hetu import settings
from hetu.async_hetutensor import AsyncHetutensor
from hetu.xylem import Xylem
from hetu.chain_data import (
    AxonInfo,
    ChainIdentity,
    DelegateInfo,
    DelegateInfoLite,
    DynamicInfo,
    IPInfo,
    MetagraphInfo,
    MetagraphInfoEmissions,
    MetagraphInfoParams,
    MetagraphInfoPool,
    NeuronInfo,
    NeuronInfoLite,
    PrometheusInfo,
    ProposalCallData,
    ProposalVoteData,
    SelectiveMetagraphIndex,
    StakeInfo,
    SubnetHyperparameters,
    SubnetIdentity,
    SubnetInfo,
    SubnetState,
    WeightCommitInfo,
)
from hetu.config import Config
from hetu.phloem import Phloem
from hetu.errors import (
    BlacklistedException,
    ChainConnectionError,
    ChainError,
    ChainQueryError,
    ChainTransactionError,
    DelegateTakeTooHigh,
    DelegateTakeTooLow,
    DelegateTxRateLimitExceeded,
    DuplicateChild,
    HotKeyAccountNotExists,
    IdentityError,
    InternalServerError,
    InvalidChild,
    InvalidRequestNameError,
    MetadataError,
    NominationError,
    NonAssociatedColdKey,
    NotDelegateError,
    NotEnoughStakeToSetChildkeys,
    NotRegisteredError,
    NotVerifiedException,
    PostProcessException,
    PriorityException,
    ProportionOverflow,
    RegistrationError,
    RegistrationNotPermittedOnRootSubnet,
    RunException,
    StakeError,
    SubNetworkDoesNotExist,
    SynapseDendriteNoneException,
    SynapseParsingError,
    TooManyChildren,
    TransferError,
    TxRateLimitExceeded,
    UnknownSynapseError,
    UnstakeError,
)
from hetu.metagraph import Metagraph
from hetu.settings import BLOCKTIME
from hetu.stream import StreamingSynapse
from hetu.hetu import Hetutensor
from hetu.chain_api import HetutensorApi
from hetu.synapse import TerminalInfo, Synapse
from hetu.tensor import Tensor
from hetu.threadpool import PriorityThreadPoolExecutor
from hetu.utils import (
    ss58_to_vec_u8,
    version_checking,
    strtobool,
    get_explorer_url_for_network,
    ss58_address_to_bytes,
    u16_normalized_float,
    u64_normalized_float,
    get_hash,
)
from hetu.utils.balance import Balance
from hetu.utils.balance import tao, rao
from hetu.utils.btlogging import logging
from hetu.utils.mock.hetutensor_mock import MockHetutensor
from hetu.utils.subnets import SubnetsAPI


# Backwards compatibility with previous hetutensor versions.
async_hetutensor = AsyncHetutensor
xylem = Xylem
config = Config
phloem = Phloem
metagraph = Metagraph
hetutensor = Hetutensor
synapse = Synapse

# Makes the `hetu.utils.mock` subpackage available as `hetutensor.mock` for backwards compatibility.
mock_subpackage = importlib.import_module("hetu.utils.mock")
sys.modules["hetutensor.mock"] = mock_subpackage

# Logging helpers.
def trace(on: bool = True):
    """
    Enables or disables trace logging.
    Args:
        on (bool): If True, enables trace logging. If False, disables trace logging.
    """
    logging.set_trace(on)


def debug(on: bool = True):
    """
    Enables or disables debug logging.
    Args:
        on (bool): If True, enables debug logging. If False, disables debug logging.
    """
    logging.set_debug(on)


def warning(on: bool = True):
    """
    Enables or disables warning logging.
    Args:
        on (bool): If True, enables warning logging. If False, disables warning logging and sets default (WARNING) level.
    """
    logging.set_warning(on)


def info(on: bool = True):
    """
    Enables or disables info logging.
    Args:
        on (bool): If True, enables info logging. If False, disables info logging and sets default (WARNING) level.
    """
    logging.set_info(on)


__all__ = [
    "Account",
    "settings",
    "AsyncHetutensor",
    "Xylem",
    "AxonInfo",
    "ChainIdentity",
    "DelegateInfo",
    "DelegateInfoLite",
    "DynamicInfo",
    "IPInfo",
    "MetagraphInfo",
    "MetagraphInfoEmissions",
    "MetagraphInfoParams",
    "MetagraphInfoPool",
    "NeuronInfo",
    "NeuronInfoLite",
    "PrometheusInfo",
    "ProposalCallData",
    "ProposalVoteData",
    "SelectiveMetagraphIndex",
    "StakeInfo",
    "SubnetHyperparameters",
    "SubnetIdentity",
    "SubnetInfo",
    "SubnetState",
    "WeightCommitInfo",
    "Config",
    "Phloem",
    "BlacklistedException",
    "ChainConnectionError",
    "ChainError",
    "ChainQueryError",
    "ChainTransactionError",
    "DelegateTakeTooHigh",
    "DelegateTakeTooLow",
    "DelegateTxRateLimitExceeded",
    "DuplicateChild",
    "HotKeyAccountNotExists",
    "IdentityError",
    "InternalServerError",
    "InvalidChild",
    "InvalidRequestNameError",
    "MetadataError",
    "NominationError",
    "NonAssociatedColdKey",
    "NotDelegateError",
    "NotEnoughStakeToSetChildkeys",
    "NotRegisteredError",
    "NotVerifiedException",
    "PostProcessException",
    "PriorityException",
    "ProportionOverflow",
    "RegistrationError",
    "RegistrationNotPermittedOnRootSubnet",
    "RunException",
    "StakeError",
    "SubNetworkDoesNotExist",
    "SynapseDendriteNoneException",
    "SynapseParsingError",
    "TooManyChildren",
    "TransferError",
    "TxRateLimitExceeded",
    "UnknownSynapseError",
    "UnstakeError",
    "Metagraph",
    "BLOCKTIME",
    "StreamingSynapse",
    "Hetutensor",
    "HetutensorApi",
    "TerminalInfo",
    "Synapse",
    "Tensor",
    "PriorityThreadPoolExecutor",
    "ss58_to_vec_u8",
    "version_checking",
    "strtobool",
    "get_explorer_url_for_network",
    "ss58_address_to_bytes",
    "u16_normalized_float",
    "u64_normalized_float",
    "get_hash",
    "Balance",
    "tao",
    "rao",
    "logging",
    "MockHetutensor",
    "SubnetsAPI",
    "async_hetutensor",
    "xylem",
    "config",
    "phloem",
    "metagraph",
    "hetutensor",
    "synapse",
    "trace",
    "debug",
    "warning",
    "info",
    "mock_subpackage",
]
