from typing import Optional, Union, TYPE_CHECKING

from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor
from hetu.hetu import Hetutensor as _Hetutensor
from .chain import Chain as _Chain
from .commitments import Commitments as _Commitments
from .delegates import Delegates as _Delegates
from .extrinsics import Extrinsics as _Extrinsics
from .metagraphs import Metagraphs as _Metagraphs
from .neurons import Neurons as _Neurons
from .queries import Queries as _Queries
from .staking import Staking as _Staking
from .subnets import Subnets as _Subnets
from .utils import add_legacy_methods as _add_classic_fields
from .wallets import Wallets as _Wallets

if TYPE_CHECKING:
    from hetu.config import Config


class HetutensorApi:
    """Hetutensor API class.

    Arguments:
        network: The network to connect to. Defaults to `None` -> "finney".
        config: Hetutensor configuration object. Defaults to `None`.
        legacy_methods: If `True`, all methods from the Hetutensor class will be added to the root level of this class.
        fallback_endpoints: List of fallback endpoints to use if default or provided network is not available. Defaults to `None`.
        retry_forever: Whether to retry forever on connection errors. Defaults to `False`.
        log_verbose: Enables or disables verbose logging.
        mock: Whether this is a mock instance. Mainly just for use in testing.

    Example:
        # sync version
        import hetu_pysdk as ht

        hetutensor = ht.HetutensorApi()
        print(hetutensor.block)
        print(hetutensor.delegates.get_delegate_identities())
        hetutensor.chain.tx_rate_limit()

        # async version
        import hetu_pysdk as ht

        hetutensor = ht.HetutensorApi(async_hetutensor=True)
        async with hetutensor:
            print(await hetutensor.block)
            print(await hetutensor.delegates.get_delegate_identities())
            print(await hetutensor.chain.tx_rate_limit())

        # using `legacy_methods`
        import hetu_pysdk as ht

        hetutensor = ht.HetutensorApi(legacy_methods=True)
        print(hetutensor.bonds(0))

        # using `fallback_endpoints` or `retry_forever`
        import hetu_pysdk as ht

        hetutensor = ht.HetutensorApi(
            network="finney",
            fallback_endpoints=["wss://localhost:9945", "wss://some-other-endpoint:9945"],
            retry_forever=True,
        )
        print(hetutensor.block)
    """

    def __init__(
        self,
        network: Optional[str] = None,
        config: Optional["Config"] = None,
        async_hetutensor: bool = False,
        legacy_methods: bool = False,
        fallback_endpoints: Optional[list[str]] = None,
        retry_forever: bool = False,
        log_verbose: bool = False,
        mock: bool = False,
    ):
        self.network = network
        self._fallback_endpoints = fallback_endpoints
        self._retry_forever = retry_forever
        self._mock = mock
        self.log_verbose = log_verbose
        self.is_async = async_hetutensor
        self._config = config

        # assigned only for async instance
        self.initialize = None
        self._hetutensor = self._get_hetutensor()

        # fix naming collision
        self._neurons = _Neurons(self._hetutensor)

        # define empty fields
        self.substrate = self._hetutensor.substrate
        self.chain_endpoint = self._hetutensor.chain_endpoint
        self.close = self._hetutensor.close
        self.config = self._hetutensor.config
        self.setup_config = self._hetutensor.setup_config
        self.help = self._hetutensor.help

        self.determine_block_hash = self._hetutensor.determine_block_hash
        self.encode_params = self._hetutensor.encode_params
        self.sign_and_send_extrinsic = self._hetutensor.sign_and_send_extrinsic
        self.start_call = self._hetutensor.start_call
        self.wait_for_block = self._hetutensor.wait_for_block

        # adds all Hetutensor methods into main level os HetutensorApi class
        if legacy_methods:
            _add_classic_fields(self)

    def _get_hetutensor(self) -> Union["_Hetutensor", "_AsyncHetutensor"]:
        """Returns the hetutensor instance based on the provided config and hetutensor type flag."""
        if self.is_async:
            _hetutensor = _AsyncHetutensor(
                network=self.network,
                config=self._config,
                log_verbose=self.log_verbose,
                fallback_endpoints=self._fallback_endpoints,
                retry_forever=self._retry_forever,
                _mock=self._mock,
            )
            self.initialize = _hetutensor.initialize
            return _hetutensor
        else:
            return _Hetutensor(
                network=self.network,
                config=self._config,
                log_verbose=self.log_verbose,
                fallback_endpoints=self._fallback_endpoints,
                retry_forever=self._retry_forever,
                _mock=self._mock,
            )

    def _determine_chain_endpoint(self) -> str:
        """Determines the connection and mock flag."""
        if self._mock:
            return "Mock"
        return self.substrate.url

    def __str__(self):
        return (
            f"<Network: {self.network}, "
            f"Chain: {self._determine_chain_endpoint()}, "
            f"{'Async version' if self.is_async else 'Sync version'}>"
        )

    def __repr__(self):
        return self.__str__()

    def __enter__(self):
        if self.is_async:
            raise NotImplementedError(
                "Async version of HetutensorApi cannot be used with sync context manager."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_async:
            raise NotImplementedError(
                "Async version of HetutensorApi cannot be used with sync context manager."
            )
        self.close()

    async def __aenter__(self):
        if not self.is_async:
            raise NotImplementedError(
                "Sync version of HetutensorApi cannot be used with async context manager."
            )
        return await self._hetutensor.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.is_async:
            raise NotImplementedError(
                "Sync version of HetutensorApi cannot be used with async context manager."
            )
        await self.substrate.close()

    @classmethod
    def add_args(cls, parser):
        _Hetutensor.add_args(parser)

    @property
    def block(self):
        """Returns current chain block number."""
        return self._hetutensor.block

    @property
    def chain(self):
        """Property of interaction with chain methods."""
        return _Chain(self._hetutensor)

    @property
    def commitments(self):
        """Property to access commitments methods."""
        return _Commitments(self._hetutensor)

    @property
    def delegates(self):
        """Property to access delegates methods."""
        return _Delegates(self._hetutensor)

    @property
    def extrinsics(self):
        """Property to access extrinsics methods."""
        return _Extrinsics(self._hetutensor)

    @property
    def metagraphs(self):
        """Property to access metagraphs methods."""
        return _Metagraphs(self._hetutensor)

    @property
    def neurons(self):
        """Property to access neurons methods."""
        return self._neurons

    @neurons.setter
    def neurons(self, value):
        """Setter for neurons property."""
        self._neurons = value

    @property
    def queries(self):
        """Property to access hetutensor queries methods."""
        return _Queries(self._hetutensor)

    @property
    def staking(self):
        """Property to access staking methods."""
        return _Staking(self._hetutensor)

    @property
    def subnets(self):
        """Property of interaction with subnets methods."""
        return _Subnets(self._hetutensor)

    @property
    def wallets(self):
        """Property of interaction methods with cold/hotkeys, and balances, etc."""
        return _Wallets(self._hetutensor)
