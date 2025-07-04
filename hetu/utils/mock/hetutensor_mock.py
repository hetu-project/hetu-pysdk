from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from random import randint
from types import SimpleNamespace
from typing import Any, Optional, Union, TypedDict
from unittest.mock import MagicMock, patch

# from async_substrate_interface import SubstrateInterface
from eth_account import Account

import hetu.hetu as hetutensor_module
from hetu.chain_data import (
    NeuronInfo,
    NeuronInfoLite,
    PrometheusInfo,
    AxonInfo,
)
from hetu.errors import ChainQueryError
from hetu.hetu import Hetutensor
from hetu.types import AxonServeCallParams, PrometheusServeCallParams
from hetu.utils import RAOPERTAO, u16_normalized_float
from hetu.utils.balance import Balance

# Mock Testing Constant
__GLOBAL_MOCK_STATE__ = {}


BlockNumber = int


class InfoDict(Mapping):
    @classmethod
    def default(cls):
        raise NotImplementedError

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


@dataclass
class AxonInfoDict(InfoDict):
    block: int
    version: int
    ip: int  # integer representation of ip address
    port: int
    ip_type: int
    protocol: int
    placeholder1: int  # placeholder for future use
    placeholder2: int

    @classmethod
    def default(cls):
        return cls(
            block=0,
            version=0,
            ip=0,
            port=0,
            ip_type=0,
            protocol=0,
            placeholder1=0,
            placeholder2=0,
        )


@dataclass
class PrometheusInfoDict(InfoDict):
    block: int
    version: int
    ip: int  # integer representation of ip address
    port: int
    ip_type: int

    @classmethod
    def default(cls):
        return cls(block=0, version=0, ip=0, port=0, ip_type=0)


@dataclass
class MockHetutensorValue:
    value: Optional[Any]


class MockMapResult:
    records: Optional[list[tuple[MockHetutensorValue, MockHetutensorValue]]]

    def __init__(
        self,
        records: Optional[
            list[
                tuple[Union[Any, MockHetutensorValue], Union[Any, MockHetutensorValue]]
            ]
        ] = None,
    ):
        _records = [
            (
                (
                    MockHetutensorValue(value=record[0]),
                    MockHetutensorValue(value=record[1]),
                )
                # Make sure record is a tuple of MockHetutensorValue (dict with value attr)
                if not (
                    isinstance(record, tuple)
                    and all(
                        isinstance(item, dict) and hasattr(item, "value")
                        for item in record
                    )
                )
                else record
            )
            for record in records
        ]

        self.records = _records

    def __iter__(self):
        return iter(self.records)


class MockSystemState(TypedDict):
    Account: dict[str, dict[int, int]]  # address -> block -> balance


class MockHetutensorState(TypedDict):
    Rho: dict[int, dict[BlockNumber, int]]  # netuid -> block -> rho
    Kappa: dict[int, dict[BlockNumber, int]]  # netuid -> block -> kappa
    Difficulty: dict[int, dict[BlockNumber, int]]  # netuid -> block -> difficulty
    ImmunityPeriod: dict[
        int, dict[BlockNumber, int]
    ]  # netuid -> block -> immunity_period
    ValidatorBatchSize: dict[
        int, dict[BlockNumber, int]
    ]  # netuid -> block -> validator_batch_size
    Active: dict[int, dict[BlockNumber, bool]]  # (netuid, uid), block -> active
    Stake: dict[str, dict[str, dict[int, int]]]  # (hotkey, coldkey) -> block -> stake

    Delegates: dict[str, dict[int, float]]  # address -> block -> delegate_take

    NetworksAdded: dict[int, dict[BlockNumber, bool]]  # netuid -> block -> added


class MockChainState(TypedDict):
    System: MockSystemState
    HetutensorModule: MockHetutensorState


class ReusableCoroutine:
    def __init__(self, coroutine):
        self.coroutine = coroutine

    def __await__(self):
        return self.reset().__await__()

    def reset(self):
        return self.coroutine()


async def _async_block():
    return 1


class MockHetutensor(Hetutensor):
    """
    A Mock Hetutensor class for running tests.
    This should mock only methods that make queries to the chain.
    e.g. We mock `Hetutensor.query_hetutensor` instead of all query methods.

    This class will also store a local (mock) state of the chain.
    """

    chain_state: MockChainState
    block_number: int

    @classmethod
    def reset(cls) -> None:
        __GLOBAL_MOCK_STATE__.clear()

        _ = cls()

    def setup(self) -> None:
        if not hasattr(self, "chain_state") or getattr(self, "chain_state") is None:
            self.chain_state = {
                "System": {"Account": {}},
                "Balances": {"ExistentialDeposit": {0: 500}},
                "HetutensorModule": {
                    "NetworksAdded": {},
                    "Rho": {},
                    "Kappa": {},
                    "Difficulty": {},
                    "ImmunityPeriod": {},
                    "ValidatorBatchSize": {},
                    "ValidatorSequenceLength": {},
                    "ValidatorEpochsPerReset": {},
                    "ValidatorEpochLength": {},
                    "MaxAllowedValidators": {},
                    "MinAllowedWeights": {},
                    "MaxWeightLimit": {},
                    "SynergyScalingLawPower": {},
                    "ScalingLawPower": {},
                    "SubnetworkN": {},
                    "MaxAllowedUids": {},
                    "NetworkModality": {},
                    "BlocksSinceLastStep": {},
                    "Tempo": {},
                    "NetworkConnect": {},
                    "EmissionValues": {},
                    "Burn": {},
                    "Active": {},
                    "Uids": {},
                    "Keys": {},
                    "Owner": {},
                    "IsNetworkMember": {},
                    "LastUpdate": {},
                    "Rank": {},
                    "Emission": {},
                    "Incentive": {},
                    "Consensus": {},
                    "Trust": {},
                    "ValidatorTrust": {},
                    "Dividends": {},
                    "PruningScores": {},
                    "ValidatorPermit": {},
                    "Weights": {},
                    "Bonds": {},
                    "Stake": {},
                    "TotalStake": {0: 0},
                    "TotalIssuance": {0: 0},
                    "TotalHotkeyStake": {},
                    "TotalColdkeyStake": {},
                    "TxRateLimit": {0: 0},  # No limit
                    "Delegates": {},
                    "Axons": {},
                    "Prometheus": {},
                    "SubnetOwner": {},
                    "Commits": {},
                    "AdjustmentAlpha": {},
                    "BondsMovingAverage": {},
                },
            }

            self.block_number = 0

            self.network = "mock"
            self.chain_endpoint = "ws://mock_endpoint.bt"
            # use MagicMock directly
            self.substrate = MagicMock()

    def __init__(self, *args, **kwargs) -> None:
        # use MagicMock directly
        mock_substrate_interface = MagicMock()
        with patch.object(
            hetutensor_module,
            "SubstrateInterface",
            return_value=mock_substrate_interface,
        ):
            super().__init__()
            self.__dict__ = __GLOBAL_MOCK_STATE__

            if not hasattr(self, "chain_state") or getattr(self, "chain_state") is None:
                self.setup()

    def get_block_hash(self, block: Optional[int] = None) -> str:
        return "0x" + sha256(str(block).encode()).hexdigest()[:64]

    def create_subnet(self, netuid: int) -> None:
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["NetworksAdded"]:
            # Per Subnet
            hetutensor_state["Rho"][netuid] = {}
            hetutensor_state["Rho"][netuid][0] = 10
            hetutensor_state["Kappa"][netuid] = {}
            hetutensor_state["Kappa"][netuid][0] = 32_767
            hetutensor_state["Difficulty"][netuid] = {}
            hetutensor_state["Difficulty"][netuid][0] = 10_000_000
            hetutensor_state["ImmunityPeriod"][netuid] = {}
            hetutensor_state["ImmunityPeriod"][netuid][0] = 4096
            hetutensor_state["ValidatorBatchSize"][netuid] = {}
            hetutensor_state["ValidatorBatchSize"][netuid][0] = 32
            hetutensor_state["ValidatorSequenceLength"][netuid] = {}
            hetutensor_state["ValidatorSequenceLength"][netuid][0] = 256
            hetutensor_state["ValidatorEpochsPerReset"][netuid] = {}
            hetutensor_state["ValidatorEpochsPerReset"][netuid][0] = 60
            hetutensor_state["ValidatorEpochLength"][netuid] = {}
            hetutensor_state["ValidatorEpochLength"][netuid][0] = 100
            hetutensor_state["MaxAllowedValidators"][netuid] = {}
            hetutensor_state["MaxAllowedValidators"][netuid][0] = 128
            hetutensor_state["MinAllowedWeights"][netuid] = {}
            hetutensor_state["MinAllowedWeights"][netuid][0] = 1024
            hetutensor_state["MaxWeightLimit"][netuid] = {}
            hetutensor_state["MaxWeightLimit"][netuid][0] = 1_000
            hetutensor_state["SynergyScalingLawPower"][netuid] = {}
            hetutensor_state["SynergyScalingLawPower"][netuid][0] = 50
            hetutensor_state["ScalingLawPower"][netuid] = {}
            hetutensor_state["ScalingLawPower"][netuid][0] = 50
            hetutensor_state["SubnetworkN"][netuid] = {}
            hetutensor_state["SubnetworkN"][netuid][0] = 0
            hetutensor_state["MaxAllowedUids"][netuid] = {}
            hetutensor_state["MaxAllowedUids"][netuid][0] = 4096
            hetutensor_state["NetworkModality"][netuid] = {}
            hetutensor_state["NetworkModality"][netuid][0] = 0
            hetutensor_state["BlocksSinceLastStep"][netuid] = {}
            hetutensor_state["BlocksSinceLastStep"][netuid][0] = 0
            hetutensor_state["Tempo"][netuid] = {}
            hetutensor_state["Tempo"][netuid][0] = 99

            # hetutensor_state['NetworkConnect'][netuid] = {}
            # hetutensor_state['NetworkConnect'][netuid][0] = {}
            hetutensor_state["EmissionValues"][netuid] = {}
            hetutensor_state["EmissionValues"][netuid][0] = 0
            hetutensor_state["Burn"][netuid] = {}
            hetutensor_state["Burn"][netuid][0] = 0
            hetutensor_state["Commits"][netuid] = {}

            # Per-UID/Hotkey

            hetutensor_state["Uids"][netuid] = {}
            hetutensor_state["Keys"][netuid] = {}
            hetutensor_state["Owner"][netuid] = {}

            hetutensor_state["LastUpdate"][netuid] = {}
            hetutensor_state["Active"][netuid] = {}
            hetutensor_state["Rank"][netuid] = {}
            hetutensor_state["Emission"][netuid] = {}
            hetutensor_state["Incentive"][netuid] = {}
            hetutensor_state["Consensus"][netuid] = {}
            hetutensor_state["Trust"][netuid] = {}
            hetutensor_state["ValidatorTrust"][netuid] = {}
            hetutensor_state["Dividends"][netuid] = {}
            hetutensor_state["PruningScores"][netuid] = {}
            hetutensor_state["PruningScores"][netuid][0] = {}
            hetutensor_state["ValidatorPermit"][netuid] = {}

            hetutensor_state["Weights"][netuid] = {}
            hetutensor_state["Bonds"][netuid] = {}

            hetutensor_state["Axons"][netuid] = {}
            hetutensor_state["Prometheus"][netuid] = {}

            hetutensor_state["NetworksAdded"][netuid] = {}
            hetutensor_state["NetworksAdded"][netuid][0] = True

            hetutensor_state["AdjustmentAlpha"][netuid] = {}
            hetutensor_state["AdjustmentAlpha"][netuid][0] = 1000

            hetutensor_state["BondsMovingAverage"][netuid] = {}
            hetutensor_state["BondsMovingAverage"][netuid][0] = 1000
        else:
            raise Exception("Subnet already exists")

    def set_difficulty(self, netuid: int, difficulty: int) -> None:
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        hetutensor_state["Difficulty"][netuid][self.block_number] = difficulty

    def _register_neuron(self, netuid: int, hotkey: str, coldkey: str) -> int:
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        subnetwork_n = self._get_most_recent_storage(
            hetutensor_state["SubnetworkN"][netuid]
        )

        if subnetwork_n > 0 and any(
            self._get_most_recent_storage(hetutensor_state["Keys"][netuid][uid])
            == hotkey
            for uid in range(subnetwork_n)
        ):
            # already_registered
            raise Exception("Hotkey already registered")
        else:
            # Not found
            if subnetwork_n >= self._get_most_recent_storage(
                hetutensor_state["MaxAllowedUids"][netuid]
            ):
                # Subnet full, replace neuron randomly
                uid = randint(0, subnetwork_n - 1)
            else:
                # Subnet not full, add new neuron
                # Append as next uid and increment subnetwork_n
                uid = subnetwork_n
                hetutensor_state["SubnetworkN"][netuid][self.block_number] = (
                    subnetwork_n + 1
                )

            hetutensor_state["Stake"][hotkey] = {}
            hetutensor_state["Stake"][hotkey][coldkey] = {}
            hetutensor_state["Stake"][hotkey][coldkey][self.block_number] = 0

            hetutensor_state["Uids"][netuid][hotkey] = {}
            hetutensor_state["Uids"][netuid][hotkey][self.block_number] = uid

            hetutensor_state["Keys"][netuid][uid] = {}
            hetutensor_state["Keys"][netuid][uid][self.block_number] = hotkey

            hetutensor_state["Owner"][hotkey] = {}
            hetutensor_state["Owner"][hotkey][self.block_number] = coldkey

            hetutensor_state["Active"][netuid][uid] = {}
            hetutensor_state["Active"][netuid][uid][self.block_number] = True

            hetutensor_state["LastUpdate"][netuid][uid] = {}
            hetutensor_state["LastUpdate"][netuid][uid][self.block_number] = (
                self.block_number
            )

            hetutensor_state["Rank"][netuid][uid] = {}
            hetutensor_state["Rank"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["Emission"][netuid][uid] = {}
            hetutensor_state["Emission"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["Incentive"][netuid][uid] = {}
            hetutensor_state["Incentive"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["Consensus"][netuid][uid] = {}
            hetutensor_state["Consensus"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["Trust"][netuid][uid] = {}
            hetutensor_state["Trust"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["ValidatorTrust"][netuid][uid] = {}
            hetutensor_state["ValidatorTrust"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["Dividends"][netuid][uid] = {}
            hetutensor_state["Dividends"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["PruningScores"][netuid][uid] = {}
            hetutensor_state["PruningScores"][netuid][uid][self.block_number] = 0.0

            hetutensor_state["ValidatorPermit"][netuid][uid] = {}
            hetutensor_state["ValidatorPermit"][netuid][uid][self.block_number] = False

            hetutensor_state["Weights"][netuid][uid] = {}
            hetutensor_state["Weights"][netuid][uid][self.block_number] = []

            hetutensor_state["Bonds"][netuid][uid] = {}
            hetutensor_state["Bonds"][netuid][uid][self.block_number] = []

            hetutensor_state["Axons"][netuid][hotkey] = {}
            hetutensor_state["Axons"][netuid][hotkey][self.block_number] = {}

            hetutensor_state["Prometheus"][netuid][hotkey] = {}
            hetutensor_state["Prometheus"][netuid][hotkey][self.block_number] = {}

            if hotkey not in hetutensor_state["IsNetworkMember"]:
                hetutensor_state["IsNetworkMember"][hotkey] = {}
            hetutensor_state["IsNetworkMember"][hotkey][netuid] = {}
            hetutensor_state["IsNetworkMember"][hotkey][netuid][self.block_number] = True

            return uid

    @staticmethod
    def _convert_to_balance(balance: Union["Balance", float, int]) -> "Balance":
        if isinstance(balance, float):
            balance = Balance.from_tao(balance)

        if isinstance(balance, int):
            balance = Balance.from_rao(balance)

        return balance

    def force_register_neuron(
        self,
        netuid: int,
        hotkey: str,
        coldkey: str,
        stake: Union["Balance", float, int] = Balance(0),
        balance: Union["Balance", float, int] = Balance(0),
    ) -> int:
        """
        Force register a neuron on the mock chain, returning the UID.
        """
        stake = self._convert_to_balance(stake)
        balance = self._convert_to_balance(balance)

        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        uid = self._register_neuron(netuid=netuid, hotkey=hotkey, coldkey=coldkey)

        hetutensor_state["TotalStake"][self.block_number] = (
            self._get_most_recent_storage(hetutensor_state["TotalStake"]) + stake.rao
        )
        hetutensor_state["Stake"][hotkey][coldkey][self.block_number] = stake.rao

        if balance.rao > 0:
            self.force_set_balance(coldkey, balance)
        self.force_set_balance(coldkey, balance)

        return uid

    def force_set_balance(
        self, ss58_address: str, balance: Union["Balance", float, int] = Balance(0)
    ) -> tuple[bool, Optional[str]]:
        """
        Returns:
            tuple[bool, Optional[str]]: (success, err_msg)
        """
        balance = self._convert_to_balance(balance)

        if ss58_address not in self.chain_state["System"]["Account"]:
            self.chain_state["System"]["Account"][ss58_address] = {
                "data": {"free": {0: 0}}
            }

        old_balance = self.get_balance(ss58_address, self.block_number)
        diff = balance.rao - old_balance.rao

        # Update total issuance
        self.chain_state["HetutensorModule"]["TotalIssuance"][self.block_number] = (
            self._get_most_recent_storage(
                self.chain_state["HetutensorModule"]["TotalIssuance"]
            )
            + diff
        )

        self.chain_state["System"]["Account"][ss58_address] = {
            "data": {"free": {self.block_number: balance.rao}}
        }

        return True, None

    # Alias for force_set_balance
    sudo_force_set_balance = force_set_balance

    def do_block_step(self) -> None:
        self.block_number += 1

        # Doesn't do epoch
        hetutensor_state = self.chain_state["HetutensorModule"]
        for subnet in hetutensor_state["NetworksAdded"]:
            hetutensor_state["BlocksSinceLastStep"][subnet][self.block_number] = (
                self._get_most_recent_storage(
                    hetutensor_state["BlocksSinceLastStep"][subnet]
                )
                + 1
            )

    def _handle_type_default(self, name: str, params: list[object]) -> object:
        defaults_mapping = {
            "TotalStake": 0,
            "TotalHotkeyStake": 0,
            "TotalColdkeyStake": 0,
            "Stake": 0,
        }

        return defaults_mapping.get(name, None)

    def commit(self, wallet: "Account", netuid: int, data: str) -> None:
        uid = self.get_uid_for_hotkey_on_subnet(
            hotkey_ss58=wallet.hotkey.ss58_address,
            netuid=netuid,
        )
        if uid is None:
            raise Exception("Neuron not found")
        hetutensor_state = self.chain_state["HetutensorModule"]
        hetutensor_state["Commits"][netuid].setdefault(self.block_number, {})[uid] = data

    def get_commitment(self, netuid: int, uid: int, block: Optional[int] = None) -> str:
        if block and self.block_number < block:
            raise Exception("Cannot query block in the future")
        block = block or self.block_number

        hetutensor_state = self.chain_state["HetutensorModule"]
        return hetutensor_state["Commits"][netuid][block][uid]

    def query_hetutensor(
        self,
        name: str,
        block: Optional[int] = None,
        params: Optional[list[object]] = None,
    ) -> MockHetutensorValue:
        if params is None:
            params = []
        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        state = self.chain_state["HetutensorModule"][name]
        if state is not None:
            # Use prefix
            if len(params) > 0:
                while state is not None and len(params) > 0:
                    state = state.get(params.pop(0), None)
                    if state is None:
                        return SimpleNamespace(
                            value=self._handle_type_default(name, params)
                        )

            # Use block
            state_at_block = state.get(block, None)
            while state_at_block is None and block > 0:
                block -= 1
                state_at_block = state.get(block, None)
            if state_at_block is not None:
                return SimpleNamespace(value=state_at_block)

            return SimpleNamespace(value=self._handle_type_default(name, params))
        else:
            return SimpleNamespace(value=self._handle_type_default(name, params))

    def query_map_hetutensor(
        self,
        name: str,
        block: Optional[int] = None,
        params: Optional[list[object]] = None,
    ) -> Optional[MockMapResult]:
        """
        Note: Double map requires one param
        """
        if params is None:
            params = []
        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        state = self.chain_state["HetutensorModule"][name]
        if state is not None:
            # Use prefix
            if len(params) > 0:
                while state is not None and len(params) > 0:
                    state = state.get(params.pop(0), None)
                    if state is None:
                        return MockMapResult([])

            # Check if single map or double map
            if len(state.keys()) == 0:
                return MockMapResult([])

            inner = list(state.values())[0]
            # Should have at least one key
            if len(inner.keys()) == 0:
                raise Exception("Invalid state")

            # Check if double map
            if isinstance(list(inner.values())[0], dict):
                # is double map
                raise ChainQueryError("Double map requires one param")

            # Iterate over each key and add value to list, max at block
            records = []
            for key in state:
                result = self._get_most_recent_storage(state[key], block)
                if result is None:
                    continue  # Skip if no result for this key at `block` or earlier

                records.append((key, result))

            return MockMapResult(records)
        else:
            return MockMapResult([])

    def query_constant(
        self, module_name: str, constant_name: str, block: Optional[int] = None
    ) -> Optional[object]:
        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        state: Optional[dict] = self.chain_state.get(module_name, None)
        if state is not None:
            if constant_name in state:
                state = state[constant_name]
            else:
                return None

            # Use block
            state_at_block = self._get_most_recent_storage(state, block)
            if state_at_block is not None:
                return SimpleNamespace(value=state_at_block)

            return state_at_block["data"]["free"]  # Can be None
        else:
            return None

    def get_current_block(self) -> int:
        return self.block_number

    # ==== Balance RPC methods ====

    def get_balance(self, address: str, block: int = None) -> "Balance":
        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        state = self.chain_state["System"]["Account"]
        if state is not None:
            if address in state:
                state = state[address]
            else:
                return Balance(0)

            # Use block
            balance_state = state["data"]["free"]
            state_at_block = self._get_most_recent_storage(
                balance_state, block
            )  # Can be None
            if state_at_block is not None:
                bal_as_int = state_at_block
                return Balance.from_rao(bal_as_int)
            else:
                return Balance(0)
        else:
            return Balance(0)

    # ==== Neuron RPC methods ====

    def neuron_for_uid(
        self, uid: int, netuid: int, block: Optional[int] = None
    ) -> Optional[NeuronInfo]:
        if uid is None:
            return NeuronInfo.get_null_neuron()

        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        if netuid not in self.chain_state["HetutensorModule"]["NetworksAdded"]:
            return None

        neuron_info = self._neuron_subnet_exists(uid, netuid, block)
        if neuron_info is None:
            return None

        else:
            return neuron_info

    def neurons(self, netuid: int, block: Optional[int] = None) -> list[NeuronInfo]:
        if netuid not in self.chain_state["HetutensorModule"]["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        neurons = []
        subnet_n = self._get_most_recent_storage(
            self.chain_state["HetutensorModule"]["SubnetworkN"][netuid], block
        )
        for uid in range(subnet_n):
            neuron_info = self.neuron_for_uid(uid, netuid, block)
            if neuron_info is not None:
                neurons.append(neuron_info)

        return neurons

    @staticmethod
    def _get_most_recent_storage(
        storage: dict[BlockNumber, Any], block_number: Optional[int] = None
    ) -> Any:
        if block_number is None:
            items = list(storage.items())
            items.sort(key=lambda x: x[0], reverse=True)
            if len(items) == 0:
                return None

            return items[0][1]

        else:
            while block_number >= 0:
                if block_number in storage:
                    return storage[block_number]

                block_number -= 1

            return None

    def _get_axon_info(
        self, netuid: int, hotkey: str, block: Optional[int] = None
    ) -> AxonInfoDict:
        # Axons [netuid][hotkey][block_number]
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["Axons"]:
            return AxonInfoDict.default()

        if hotkey not in hetutensor_state["Axons"][netuid]:
            return AxonInfoDict.default()

        result = self._get_most_recent_storage(
            hetutensor_state["Axons"][netuid][hotkey], block
        )
        if not result:
            return AxonInfoDict.default()

        return result

    def _get_prometheus_info(
        self, netuid: int, hotkey: str, block: Optional[int] = None
    ) -> PrometheusInfoDict:
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["Prometheus"]:
            return PrometheusInfoDict.default()

        if hotkey not in hetutensor_state["Prometheus"][netuid]:
            return PrometheusInfoDict.default()

        result = self._get_most_recent_storage(
            hetutensor_state["Prometheus"][netuid][hotkey], block
        )
        if not result:
            return PrometheusInfoDict.default()

        return result

    def _neuron_subnet_exists(
        self, uid: int, netuid: int, block: Optional[int] = None
    ) -> Optional[NeuronInfo]:
        hetutensor_state = self.chain_state["HetutensorModule"]
        if netuid not in hetutensor_state["NetworksAdded"]:
            return None

        if self._get_most_recent_storage(hetutensor_state["SubnetworkN"][netuid]) <= uid:
            return None

        hotkey = self._get_most_recent_storage(hetutensor_state["Keys"][netuid][uid])
        if hotkey is None:
            return None

        axon_info_ = self._get_axon_info(netuid, hotkey, block)

        prometheus_info = self._get_prometheus_info(netuid, hotkey, block)

        coldkey = self._get_most_recent_storage(hetutensor_state["Owner"][hotkey], block)
        active = self._get_most_recent_storage(
            hetutensor_state["Active"][netuid][uid], block
        )
        rank = self._get_most_recent_storage(
            hetutensor_state["Rank"][netuid][uid], block
        )
        emission = self._get_most_recent_storage(
            hetutensor_state["Emission"][netuid][uid], block
        )
        incentive = self._get_most_recent_storage(
            hetutensor_state["Incentive"][netuid][uid], block
        )
        consensus = self._get_most_recent_storage(
            hetutensor_state["Consensus"][netuid][uid], block
        )
        trust = self._get_most_recent_storage(
            hetutensor_state["Trust"][netuid][uid], block
        )
        validator_trust = self._get_most_recent_storage(
            hetutensor_state["ValidatorTrust"][netuid][uid], block
        )
        dividends = self._get_most_recent_storage(
            hetutensor_state["Dividends"][netuid][uid], block
        )
        pruning_score = self._get_most_recent_storage(
            hetutensor_state["PruningScores"][netuid][uid], block
        )
        last_update = self._get_most_recent_storage(
            hetutensor_state["LastUpdate"][netuid][uid], block
        )
        validator_permit = self._get_most_recent_storage(
            hetutensor_state["ValidatorPermit"][netuid][uid], block
        )

        weights = self._get_most_recent_storage(
            hetutensor_state["Weights"][netuid][uid], block
        )
        bonds = self._get_most_recent_storage(
            hetutensor_state["Bonds"][netuid][uid], block
        )

        stake_dict = {
            coldkey: Balance.from_rao(
                self._get_most_recent_storage(
                    hetutensor_state["Stake"][hotkey][coldkey], block
                )
            )
            for coldkey in hetutensor_state["Stake"][hotkey]
        }

        stake = sum(stake_dict.values())

        weights = [[int(weight[0]), int(weight[1])] for weight in weights]
        bonds = [[int(bond[0]), int(bond[1])] for bond in bonds]
        rank = u16_normalized_float(rank)
        emission = emission / RAOPERTAO
        incentive = u16_normalized_float(incentive)
        consensus = u16_normalized_float(consensus)
        trust = u16_normalized_float(trust)
        validator_trust = u16_normalized_float(validator_trust)
        dividends = u16_normalized_float(dividends)
        prometheus_info = PrometheusInfo.from_dict(prometheus_info)
        axon_info_ = AxonInfo.from_neuron_info(
            {"hotkey": hotkey, "coldkey": coldkey, "axon_info": axon_info_}
        )

        neuron_info = NeuronInfo(
            hotkey=hotkey,
            coldkey=coldkey,
            uid=uid,
            netuid=netuid,
            active=active,
            rank=rank,
            emission=emission,
            incentive=incentive,
            consensus=consensus,
            trust=trust,
            validator_trust=validator_trust,
            dividends=dividends,
            pruning_score=pruning_score,
            last_update=last_update,
            validator_permit=validator_permit,
            stake=stake,
            stake_dict=stake_dict,
            total_stake=stake,
            prometheus_info=prometheus_info,
            axon_info=axon_info_,
            weights=weights,
            bonds=bonds,
            is_null=False,
        )

        return neuron_info

    def neurons_lite(
        self, netuid: int, block: Optional[int] = None
    ) -> list[NeuronInfoLite]:
        if netuid not in self.chain_state["HetutensorModule"]["NetworksAdded"]:
            raise Exception("Subnet does not exist")

        neurons = []
        subnet_n = self._get_most_recent_storage(
            self.chain_state["HetutensorModule"]["SubnetworkN"][netuid]
        )
        for uid in range(subnet_n):
            neuron_info = self.neuron_for_uid_lite(uid, netuid, block)
            if neuron_info is not None:
                neurons.append(neuron_info)

        return neurons

    def neuron_for_uid_lite(
        self, uid: int, netuid: int, block: Optional[int] = None
    ) -> Optional[NeuronInfoLite]:
        if uid is None:
            return NeuronInfoLite.get_null_neuron()

        if block:
            if self.block_number < block:
                raise Exception("Cannot query block in the future")

        else:
            block = self.block_number

        if netuid not in self.chain_state["HetutensorModule"]["NetworksAdded"]:
            return None

        neuron_info = self._neuron_subnet_exists(uid, netuid, block)
        if neuron_info is None:
            # TODO Why does this return None here but a null neuron earlier?
            return None

        else:
            return NeuronInfoLite(
                hotkey=neuron_info.hotkey,
                coldkey=neuron_info.coldkey,
                uid=neuron_info.uid,
                netuid=neuron_info.netuid,
                active=neuron_info.active,
                stake=neuron_info.stake,
                stake_dict=neuron_info.stake_dict,
                total_stake=neuron_info.total_stake,
                rank=neuron_info.rank,
                emission=neuron_info.emission,
                incentive=neuron_info.incentive,
                consensus=neuron_info.consensus,
                trust=neuron_info.trust,
                validator_trust=neuron_info.validator_trust,
                dividends=neuron_info.dividends,
                last_update=neuron_info.last_update,
                validator_permit=neuron_info.validator_permit,
                prometheus_info=neuron_info.prometheus_info,
                axon_info=neuron_info.axon_info,
                pruning_score=neuron_info.pruning_score,
                is_null=neuron_info.is_null,
            )

    def get_transfer_fee(
        self, wallet: "Account", dest: str, value: Union["Balance", float, int]
    ) -> "Balance":
        return Balance(700)

    def do_transfer(
        self,
        wallet: "Account",
        dest: str,
        transfer_balance: "Balance",
        wait_for_inclusion: bool = True,
        wait_for_finalization: bool = False,
    ) -> tuple[bool, Optional[str], Optional[str]]:
        bal = self.get_balance(wallet.coldkeypub.ss58_address)
        dest_bal = self.get_balance(dest)
        transfer_fee = self.get_transfer_fee(wallet, dest, transfer_balance)

        existential_deposit = self.get_existential_deposit()

        if bal < transfer_balance + existential_deposit + transfer_fee:
            raise Exception("Insufficient balance")

        # Remove from the free balance
        self.chain_state["System"]["Account"][wallet.coldkeypub.ss58_address]["data"][
            "free"
        ][self.block_number] = (bal - transfer_balance - transfer_fee).rao

        # Add to the free balance
        if dest not in self.chain_state["System"]["Account"]:
            self.chain_state["System"]["Account"][dest] = {"data": {"free": {}}}

        self.chain_state["System"]["Account"][dest]["data"]["free"][
            self.block_number
        ] = (dest_bal + transfer_balance).rao

        return True, None, None

    @staticmethod
    def min_required_stake():
        """
        As the minimum required stake may change, this method allows us to dynamically
        update the amount in the mock without updating the tests
        """
        # valid minimum threshold as of 2024/05/01
        return 100_000_000  # RAO

    def do_serve_prometheus(
        self,
        wallet: "Account",
        call_params: "PrometheusServeCallParams",
        wait_for_inclusion: bool = False,
        wait_for_finalization: bool = True,
    ) -> tuple[bool, Optional[str]]:
        return True, None

    def do_set_weights(
        self,
        wallet: "Account",
        netuid: int,
        uids: int,
        vals: list[int],
        version_key: int,
        wait_for_inclusion: bool = False,
        wait_for_finalization: bool = True,
    ) -> tuple[bool, Optional[str]]:
        return True, None

    def do_serve_axon(
        self,
        wallet: "Account",
        call_params: "AxonServeCallParams",
        wait_for_inclusion: bool = False,
        wait_for_finalization: bool = True,
    ) -> tuple[bool, Optional[str]]:
        return True, None
