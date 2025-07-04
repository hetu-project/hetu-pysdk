from hetu.metagraph import AsyncMetagraph
from hetu.types import HetutensorMixin
from hetu.utils.balance import Balance
from hetu.utils.btlogging import logging

class AsyncHetutensor(HetutensorMixin):
    """
    Thin layer for interacting with the Hetu EVM blockchain asynchronously. All methods are EVM-compatible mocks or stubs.
    """

    def __init__(
        self,
        network=None,
        config=None,
        log_verbose=False,
        fallback_endpoints=None,
        retry_forever=False,
        _mock=False,
    ):
        self.network = network or "hetu-local"
        self._config = config
        self.log_verbose = log_verbose
        self.chain_endpoint = "http://localhost:8545"  # Default mock endpoint
        if self.log_verbose:
            logging.info(
                f"Connected to {self.network} network at {self.chain_endpoint} (EVM mock mode, async)."
            )

    async def close(self):
        pass

    async def initialize(self):
        if self.log_verbose:
            logging.info(
                f"[magenta]Connecting to Hetu EVM:[/magenta] [blue]{self}[/blue][magenta]...[/magenta]"
            )
        return self

    async def __aenter__(self):
        if self.log_verbose:
            logging.info(
                f"[magenta]Connecting to Hetu EVM:[/magenta] [blue]{self}[/blue][magenta]...[/magenta]"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ===================== EVM/ETH Mock Query Methods =====================

    async def query_constant(self, *args, **kwargs):
        return None

    async def query_map(self, *args, **kwargs):
        return {}

    async def query_module(self, *args, **kwargs):
        return None

    async def query_runtime_api(self, *args, **kwargs):
        return None

    async def state_call(self, *args, **kwargs):
        return {}

    # ===================== EVM/ETH Mock Blockchain Info =====================

    @property
    async def block(self):
        return await self.get_current_block()

    async def get_current_block(self):
        return 0

    async def get_block_hash(self, block=None):
        return "0x0000000000000000000000000000000000000000000000000000000000000000"

    async def determine_block_hash(self, *args, **kwargs):
        return None

    # ===================== EVM/ETH Mock Subnet/Neuron/Stake =====================

    async def all_subnets(self, *args, **kwargs):
        return []

    async def get_all_subnets_info(self, *args, **kwargs):
        return []

    async def get_balance(self, *args, **kwargs):
        return Balance(0)

    async def get_balances(self, *addresses, **kwargs):
        return {address: Balance(0) for address in addresses}

    async def get_hyperparameter(self, *args, **kwargs):
        return None

    async def get_metagraph_info(self, *args, **kwargs):
        return None

    async def get_all_metagraphs_info(self, *args, **kwargs):
        return []

    async def get_stake(self, *args, **kwargs):
        return Balance(0)

    async def get_stake_for_coldkey(self, *args, **kwargs):
        return []

    async def get_stake_for_hotkey(self, *args, **kwargs):
        return Balance(0)

    async def get_subnet_info(self, *args, **kwargs):
        return None

    async def get_subnets(self, *args, **kwargs):
        return []

    async def get_total_subnets(self, *args, **kwargs):
        return 0

    async def get_uid_for_hotkey_on_subnet(self, *args, **kwargs):
        return None

    async def is_hotkey_registered(self, *args, **kwargs):
        return False

    async def is_hotkey_registered_any(self, *args, **kwargs):
        return False

    async def is_hotkey_registered_on_subnet(self, *args, **kwargs):
        return False

    async def is_subnet_active(self, *args, **kwargs):
        return False

    async def metagraph(self, *args, **kwargs):
        return AsyncMetagraph()

    # ===================== EVM/ETH Mock Extrinsics =====================

    async def add_stake(self, *args, **kwargs):
        return True

    async def add_stake_multiple(self, *args, **kwargs):
        return True

    async def burned_register(self, *args, **kwargs):
        return True

    async def commit(self, *args, **kwargs):
        return True

    set_commitment = commit

    async def move_stake(self, *args, **kwargs):
        return True

    async def register(self, *args, **kwargs):
        return True

    async def register_subnet(self, *args, **kwargs):
        return True

    async def reveal_weights(self, *args, **kwargs):
        return True, ""

    async def root_register(self, *args, **kwargs):
        return True

    async def root_set_weights(self, *args, **kwargs):
        return True

    async def set_weights(self, *args, **kwargs):
        return True, ""

    async def serve_axon(self, *args, **kwargs):
        return True

    async def start_call(self, *args, **kwargs):
        return True, ""

    async def swap_stake(self, *args, **kwargs):
        return True

    async def transfer(self, *args, **kwargs):
        return True

    async def transfer_stake(self, *args, **kwargs):
        return True

    async def unstake(self, *args, **kwargs):
        return True

    async def unstake_multiple(self, *args, **kwargs):
        return True
