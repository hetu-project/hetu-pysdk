from typing import TYPE_CHECKING, Any, Optional, Union
from numpy.typing import NDArray
from web3 import Web3, HTTPProvider

from hetu.axon import Axon
from hetu.chain_data import (
    DynamicInfo,
    MetagraphInfo,
    StakeInfo,
    SubnetInfo,
    NeuronInfo,
    NeuronInfoLite,
)
from hetu.config import Config
from hetu.settings import NETWORKS, NETWORK_MAP
from hetu.metagraph import Metagraph
from hetu.types import HetutensorMixin
from hetu.utils.balance import Balance
from hetu.utils.btlogging import logging

if TYPE_CHECKING:
    from eth_account.account import Account  # ETH wallet


class Hetutensor(HetutensorMixin):
    """
    Thin layer for interacting with the Hetu EVM blockchain. All methods are EVM-compatible mocks or stubs.
    """

    def __init__(
        self,
        network: Optional[str] = None,
        config: Optional["Config"] = None,
        log_verbose: bool = False,
        fallback_endpoints: Optional[list[str]] = None,
        retry_forever: bool = False,
        _mock: bool = False,
    ):
        """
        Initializes an instance of the HetuClient class for EVM/ETH networks.
        """
        self.network = network or "local"
        self._config = config
        self.log_verbose = log_verbose
        if network in NETWORKS:
            self.chain_endpoint = NETWORK_MAP[network]
        else:
            self.chain_endpoint = "http://localhost:8545"  # Default mock endpoint
        self.web3 = Web3(HTTPProvider(self.chain_endpoint))
        if self.log_verbose:
            logging.info(
                f"Connected to {self.network} network at {self.chain_endpoint} (EVM mock mode)."
            )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Closes the client connection (mock, does nothing)."""
        pass

    # ===================== EVM/ETH Mock Query Methods =====================

    def query_constant(
        self, module_name: str, constant_name: str, block: Optional[int] = None
    ) -> Optional[Any]:
        """Mock: Returns None for any constant query."""
        return None

    def query_map(
        self,
        module: str,
        name: str,
        block: Optional[int] = None,
        params: Optional[list] = None,
    ) -> dict:
        """Mock: Returns empty dict for any map query."""
        return {}

    def query_module(
        self,
        module: str,
        name: str,
        block: Optional[int] = None,
        params: Optional[list] = None,
    ) -> Optional[Any]:
        """Mock: Returns None for any module query."""
        return None

    def query_runtime_api(
        self,
        runtime_api: str,
        method: str,
        params: Optional[Union[list[Any], dict[str, Any]]] = None,
        block: Optional[int] = None,
    ) -> Any:
        """Mock: Returns None for any runtime API query."""
        return None

    def state_call(self, method: str, data: str, block: Optional[int] = None) -> dict:
        """Mock: Returns empty dict for any state call."""
        return {}

    # ===================== EVM/ETH Mock Blockchain Info =====================

    @property
    def block(self) -> int:
        return self.get_current_block()

    def get_current_block(self) -> int:
        """Returns the latest block number using web3."""
        try:
            return self.web3.eth.block_number
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.block_number failed: {e}")
            return 0

    def get_block_hash(self, block: Optional[int] = None) -> str:
        """Returns the block hash for a given block number using web3."""
        try:
            if block is None:
                block = self.get_current_block()
            block_obj = self.web3.eth.get_block(block)
            return block_obj.hash.hex()
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.get_block({block}) failed: {e}")
            return "0x" + "0" * 64

    def determine_block_hash(self, block: Optional[int]) -> Optional[str]:
        """Mock: Returns None for block hash determination."""
        return None

    # ===================== EVM/ETH Mock Subnet/Neuron/Stake =====================

    def all_subnets(self, block: Optional[int] = None) -> Optional[list[DynamicInfo]]:
        return []

    def get_all_subnets_info(self, block: Optional[int] = None) -> list[SubnetInfo]:
        return []

    def get_balance(self, address: str, block: Optional[int] = None) -> Balance:
        """Returns the ETH balance for an address using web3."""
        try:
            block_param = block if block is not None else 'latest'
            balance_wei = self.web3.eth.get_balance(address, block_identifier=block_param)
            return Balance(balance_wei)
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.get_balance({address}) failed: {e}")
            return Balance(0)

    def get_balances(
        self, *addresses: str, block: Optional[int] = None
    ) -> dict[str, Balance]:
        return {address: Balance(0) for address in addresses}

    def get_hyperparameter(
        self, param_name: str, netuid: int, block: Optional[int] = None
    ) -> Optional[Any]:
        return None

    def get_metagraph_info(
        self, netuid: int, block: Optional[int] = None
    ) -> Optional[MetagraphInfo]:
        return None

    def get_all_metagraphs_info(
        self, block: Optional[int] = None
    ) -> list[MetagraphInfo]:
        return []

    def get_stake(
        self,
        coldkey_ss58: str,
        hotkey_ss58: str,
        netuid: int,
        block: Optional[int] = None,
    ) -> Balance:
        return Balance(0)

    def get_stake_for_coldkey(
        self, coldkey_ss58: str, block: Optional[int] = None
    ) -> list[StakeInfo]:
        return []

    def get_stake_for_hotkey(
        self, hotkey_ss58: str, netuid: int, block: Optional[int] = None
    ) -> Balance:
        return Balance(0)

    def get_subnet_info(
        self, netuid: int, block: Optional[int] = None
    ) -> Optional[SubnetInfo]:
        return None

    def get_subnets(self, block: Optional[int] = None) -> list[int]:
        return []

    def get_total_subnets(self, block: Optional[int] = None) -> Optional[int]:
        return 0

    def get_uid_for_hotkey_on_subnet(
        self, hotkey_ss58: str, netuid: int, block: Optional[int] = None
    ) -> Optional[int]:
        return None

    def is_hotkey_registered(
        self,
        hotkey_ss58: str,
        netuid: Optional[int] = None,
        block: Optional[int] = None,
    ) -> bool:
        return False

    def is_hotkey_registered_any(
        self, hotkey_ss58: str, block: Optional[int] = None
    ) -> bool:
        return False

    def is_hotkey_registered_on_subnet(
        self, hotkey_ss58: str, netuid: int, block: Optional[int] = None
    ) -> bool:
        return False

    def is_subnet_active(self, netuid: int, block: Optional[int] = None) -> bool:
        return False

    def metagraph(
        self, netuid: int, lite: bool = True, block: Optional[int] = None
    ) -> Metagraph:
        return Metagraph()

    def neurons(self, netuid: int, block: Optional[int] = None) -> list["NeuronInfo"]:
        """
        Mock: Retrieves a list of all neurons within a specified subnet of the Hetu network.
        Arguments:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
        Returns:
            A list of NeuronInfo objects (mock: returns empty list).
        """
        return []

    def neurons_lite(self, netuid: int, block: Optional[int] = None) -> list["NeuronInfoLite"]:
        """
        Mock: Retrieves a list of neurons in a 'lite' format from a specific subnet of the Hetu network.
        Arguments:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
        Returns:
            A list of NeuronInfoLite objects (mock: returns empty list).
        """
        return []

    # ===================== EVM/ETH Mock Extrinsics =====================

    def add_stake(
        self,
        wallet: "Account",
        hotkey_ss58: Optional[str] = None,
        netuid: Optional[int] = None,
        amount: Optional[Balance] = None,
        **kwargs,
    ) -> bool:
        return True

    def add_stake_multiple(
        self,
        wallet: "Account",
        hotkey_ss58s: list[str],
        netuids: list[int],
        amounts: Optional[list[Balance]] = None,
        **kwargs,
    ) -> bool:
        return True

    def burned_register(self, wallet: "Account", netuid: int, **kwargs) -> bool:
        return True

    def commit(
        self, wallet: "Account", netuid: int, data: str, period: Optional[int] = None
    ) -> bool:
        return True

    set_commitment = commit

    def move_stake(
        self,
        wallet: "Account",
        origin_hotkey: str,
        origin_netuid: int,
        destination_hotkey: str,
        destination_netuid: int,
        amount: Balance,
        **kwargs,
    ) -> bool:
        return True

    def register(self, wallet: "Account", netuid: int, **kwargs) -> bool:
        return True

    def register_subnet(self, wallet: "Account", **kwargs) -> bool:
        return True

    def reveal_weights(
        self,
        wallet: "Account",
        netuid: int,
        uids: Union[NDArray, list],
        weights: Union[NDArray, list],
        salt: Union[NDArray, list],
        **kwargs,
    ) -> tuple[bool, str]:
        return True, ""

    def root_register(self, wallet: "Account", **kwargs) -> bool:
        return True

    def root_set_weights(
        self, wallet: "Account", netuids: list[int], weights: list[float], **kwargs
    ) -> bool:
        return True

    def set_weights(
        self,
        wallet: "Account",
        netuid: int,
        uids: Union[NDArray, list],
        weights: Union[NDArray, list],
        **kwargs,
    ) -> tuple[bool, str]:
        return True, ""

    def serve_axon(self, netuid: int, axon: Axon, **kwargs) -> bool:
        return True

    def start_call(self, wallet: "Account", netuid: int, **kwargs) -> tuple[bool, str]:
        return True, ""

    def swap_stake(
        self,
        wallet: "Account",
        hotkey_ss58: str,
        origin_netuid: int,
        destination_netuid: int,
        amount: Balance,
        **kwargs,
    ) -> bool:
        return True

    def transfer(self, wallet: "Account", dest: str, amount: Balance, **kwargs) -> bool:
        """Sends a raw ETH transaction using web3 (needs wallet private key)."""
        try:
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            tx = {
                'to': dest,
                'value': int(amount),
                'gas': kwargs.get('gas', 21000),
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.web3.eth.chain_id,
            }
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
            if self.log_verbose:
                logging.info(f"Sent tx: {tx_hash.hex()}")
            return True
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3 transfer failed: {e}")
            return False

    def get_transaction_receipt(self, tx_hash: str) -> Optional[dict]:
        try:
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt) if receipt else None
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.get_transaction_receipt({tx_hash}) failed: {e}")
            return None

    def get_transaction_count(self, address: str, block: Optional[int] = None) -> int:
        try:
            block_param = block if block is not None else 'latest'
            return self.web3.eth.get_transaction_count(address, block_identifier=block_param)
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.get_transaction_count({address}) failed: {e}")
            return 0

    def call(self, to: str, data: str, block: Optional[int] = None) -> Optional[str]:
        try:
            tx = {'to': to, 'data': data}
            block_param = block if block is not None else 'latest'
            result = self.web3.eth.call(tx, block_identifier=block_param)
            return result.hex() if isinstance(result, bytes) else result
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.call({to}, {data}) failed: {e}")
            return None

    def estimate_gas(self, to: str, data: str, value: int = 0, from_addr: Optional[str] = None) -> int:
        try:
            tx = {'to': to, 'data': data, 'value': value}
            if from_addr:
                tx['from'] = from_addr
            return self.web3.eth.estimate_gas(tx)
        except Exception as e:
            if self.log_verbose:
                logging.error(f"web3.eth.estimate_gas({to}) failed: {e}")
            return 0
