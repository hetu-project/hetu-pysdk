from hetu.metagraph import AsyncMetagraph
from hetu.types import HetutensorMixin
from hetu.utils.balance import Balance
from hetu.utils.btlogging import logging
from hetu.chain_data import EVMSubnetInfo
from typing import Optional, Union, Any, List
from hetu.settings import NETWORKS, NETWORK_MAP

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
        username=None,
        password=None,
        wallet_path=None,
    ):
        self.network = network or "local"
        self._config = config
        self.log_verbose = log_verbose
        if network in NETWORKS:
            self.chain_endpoint = NETWORK_MAP[network]
        else:
            self.chain_endpoint = "http://161.97.161.133:8545"  # Default mock endpoint
        if self.log_verbose:
            logging.info(
                f"Connected to {self.network} network at {self.chain_endpoint} (EVM mock mode, async)."
            )
        
        # Initialize contracts
        self._init_contract()
        
        # Initialize wallet
        self._init_wallet(username, password, wallet_path)

    def _init_wallet(self, username=None, password=None, wallet_path=None):
        """
        Initialize wallet
        
        Args:
            username (Optional[str]): Wallet username
            password (Optional[str]): Wallet password
            wallet_path (Optional[str]): Wallet path
        """
        from hetu.utils.wallet import unlock_wallet
        
        self.wallet = None
        self.wallet_name = None
        self.wallet_path = wallet_path
        
        if username and password:
            # Try to unlock wallet with provided credentials
            try:
                self.wallet = unlock_wallet(username, password, wallet_path)
                self.wallet_name = username
                if self.log_verbose:
                    logging.info(f"Unlocked wallet: {self.wallet.address}")
            except Exception as e:
                if self.log_verbose:
                    logging.error(f"Failed to unlock wallet with provided credentials: {e}")
                raise e

    def _init_contract(self):
        """
        Initialize Hetu smart contracts
        Load all contract ABIs and addresses
        """
        import json
        import os
        from web3 import AsyncWeb3, Web3
        from web3.providers import AsyncHTTPProvider
        
        # Contract address configuration
        self.contract_addresses = {
            "WHETU_TOKEN": "0x10Fc0865C678B3727c842812bE004af3661FA5Ee",
            "AMM_FACTORY": "0x9aA413fD38582d9aAD6328dd034504F322ea624B", 
            "GLOBAL_STAKING": "0x24a9Cc5d0Baa1b9a049DA81b615A53ad8e2d3b9E",
            "SUBNET_MANAGER": "0x591C3103a983Cb92FE4254f8D1a7CC7710B8A0E5",
            "NEURON_MANAGER": "0x756a874E457756fff16446ef85384FfE8aEf65b0"
        }
        
        # Web3 instance - using async version
        self.web3 = AsyncWeb3(
            AsyncHTTPProvider(self.chain_endpoint)
        )
        
        # Contract ABI file paths
        contracts_dir = os.path.join(os.path.dirname(__file__), "..", "contracts")
        abi_files = {
            "WHETU_TOKEN": "WHETU.abi",
            "AMM_FACTORY": "SubnetAMM.abi", 
            "GLOBAL_STAKING": "GlobalStaking.abi",
            "SUBNET_MANAGER": "SubnetManager.abi",
            "NEURON_MANAGER": "NeuronManager.abi"
        }
        
        # Initialize contract instances
        self.contracts = {}
        
        for contract_name, abi_file in abi_files.items():
            try:
                abi_path = os.path.join(contracts_dir, abi_file)
                if os.path.exists(abi_path):
                    with open(abi_path, 'r') as f:
                        abi = json.load(f)
                    
                    contract_address = self.contract_addresses[contract_name]
                    contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(contract_address),
                        abi=abi
                    )
                    
                    self.contracts[contract_name] = contract
                    
                    if self.log_verbose:
                        logging.info(f"✅ Initialized contract: {contract_name} at {contract_address}")
                        
                else:
                    if self.log_verbose:
                        logging.warning(f"⚠️ ABI file not found: {abi_path}")
                        
            except Exception as e:
                if self.log_verbose:
                    logging.error(f"❌ Failed to initialize contract {contract_name}: {e}")
        
        # Add direct attributes for convenience
        self.whetu_token = self.contracts.get("WHETU_TOKEN")
        self.subnet_manager = self.contracts.get("SUBNET_MANAGER")
        self.neuron_manager = self.contracts.get("NEURON_MANAGER")
        self.global_staking = self.contracts.get("GLOBAL_STAKING")
        self.amm_factory = self.contracts.get("AMM_FACTORY")

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

    async def get_subnets(self, *args, **kwargs):
        return []

    async def get_total_subnets(self, block=None) -> int:
        """Returns the total number of subnets using the subnet manager contract."""
        try:
            if self.subnet_manager:
                # Get total number of subnets from contract
                total_networks = await self._contract_call(
                    self.subnet_manager,
                    "totalNetworks",
                    []
                )
                if self.log_verbose:
                    logging.info(f"Total subnets from contract: {total_networks}")
                return total_networks
            else:
                if self.log_verbose:
                    logging.warning("Subnet manager contract not initialized")
                return 0
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get total subnets: {e}")
        return 0

    async def get_subnet_info(self, netuid: int, block=None) -> Optional[EVMSubnetInfo]:
        """
        Returns subnet information for a given netuid using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[EVMSubnetInfo]: Subnet information if found, None otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None

            # Call contract's getSubnetDetails function
            result = await self._contract_call(
                self.subnet_manager,
                "getSubnetDetails",
                [netuid]
            )
            
            if self.log_verbose:
                logging.info(f"Raw subnet details for netuid {netuid}: {result}")
            
            # Parse returned results
            subnet_info_tuple = result[0]
            market_data = (result[1], result[2], result[3], result[4])
            
            # Create object using EVMSubnetInfo.from_contract_data
            evm_subnet_info = EVMSubnetInfo.from_contract_data(subnet_info_tuple, market_data)
            
            if self.log_verbose:
                logging.info(f"Created EVMSubnetInfo for netuid {netuid}:")
                logging.info(f"  name: {evm_subnet_info.name}")
                logging.info(f"  description: {evm_subnet_info.description}")
                logging.info(f"  owner: {evm_subnet_info.owner}")
                logging.info(f"  is_active: {evm_subnet_info.is_active}")
            
            return evm_subnet_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet info for netuid {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    async def get_all_subnets_info(self, block=None) -> list[EVMSubnetInfo]:
        """
        Returns information for all subnets using the subnet manager contract.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[EVMSubnetInfo]: List of all subnet information.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return []
            
            # Get next netuid as upper limit
            next_netuid = await self.get_next_netuid(block)
            if self.log_verbose:
                logging.info(f"Next netuid: {next_netuid}")
            
            if next_netuid == 0:
                if self.log_verbose:
                    logging.info("No subnets found (next_netuid is 0)")
                return []
            
            subnet_info_list = []
            
            # Iterate through all possible netuids from 0 to next_netuid-1
            for netuid in range(next_netuid):
                try:
                    if self.log_verbose:
                        logging.info(f"Checking netuid {netuid}...")
                    
                    # Check if subnet exists
                    if await self.is_subnet_exists(netuid, block):
                        subnet_info = await self.get_subnet_info(netuid, block)
                        if subnet_info:
                            subnet_info_list.append(subnet_info)
                            if self.log_verbose:
                                logging.info(f"Added subnet {netuid}: {subnet_info.name}")
                        else:
                            if self.log_verbose:
                                logging.warning(f"Subnet {netuid} exists but failed to get info")
                    else:
                        if self.log_verbose:
                            logging.info(f"Subnet {netuid} does not exist")
                            
                except Exception as e:
                    if self.log_verbose:
                        logging.error(f"Failed to get info for subnet {netuid}: {e}")
                    continue
            
            if self.log_verbose:
                logging.info(f"Retrieved info for {len(subnet_info_list)} subnets")
            
            return subnet_info_list
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get all subnets info: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return []

    async def is_subnet_exists(self, netuid: int, block=None) -> bool:
        """
        Checks if a subnet exists using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the subnet exists, False otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            # Call contract's subnetExists function
            result = await self._contract_call(
                self.subnet_manager,
                "subnetExists",
                [netuid]
            )
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} exists: {result}")
            
            return result
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if subnet {netuid} exists: {e}")
            return False

    async def is_subnet_active(self, netuid: int, block=None) -> bool:
        """
        Checks if a subnet is active using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the subnet is active, False otherwise.
        """
        try:
            # Get subnet info
            subnet_info = await self.get_subnet_info(netuid, block)
            if subnet_info:
                is_active = subnet_info.is_active
                if self.log_verbose:
                    logging.info(f"Subnet {netuid} active status: {is_active}")
                return is_active
            else:
                if self.log_verbose:
                    logging.warning(f"No subnet info found for netuid {netuid}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if subnet {netuid} is active: {e}")
            return False

    async def get_user_subnets(self, user_address: str, block=None) -> list[int]:
        """
        Returns a list of subnet IDs that a user owns or participates in.
        
        Args:
            user_address (str): The user's wallet address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[int]: List of subnet IDs.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return []
            
            # Call contract's getUserSubnets function
            result = await self._contract_call(
                self.subnet_manager,
                "getUserSubnets",
                [user_address]
            )
            
            if self.log_verbose:
                logging.info(f"User {user_address} subnets: {result}")
            
            return result
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get user subnets for {user_address}: {e}")
            return []

    async def get_subnet_params(self, netuid: int, block=None) -> Optional[dict]:
        """
        Returns subnet parameters for a given netuid.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Subnet parameters if found, None otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # Call contract's getSubnetParams function
            result = await self._contract_call(
                self.subnet_manager,
                "getSubnetParams",
                [netuid]
            )
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} params: {result}")
            
            # Parse parameters
            if result and len(result) >= 2:
                params = {
                    "min_lock": result[0],
                    "rate_limit": result[1]
                }
                return params
            else:
                return None
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet params for netuid {netuid}: {e}")
            return None

    async def get_subnet_hyperparams(self, netuid: int, block=None) -> Optional[dict]:
        """
        Returns subnet hyperparameters for a given netuid.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Subnet hyperparameters if found, None otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # Call contract's getSubnetHyperparams function
            result = await self._contract_call(
                self.subnet_manager,
                "getSubnetHyperparams",
                [netuid]
            )
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} hyperparams: {result}")
            
            # Parse hyperparameters
            if result and len(result) >= 3:
                hyperparams = {
                    "max_neurons": result[0],
                    "max_validators": result[1],
                    "min_stake": result[2]
                }
                return hyperparams
            else:
                return None
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet hyperparams for netuid {netuid}: {e}")
            return None

    async def get_next_netuid(self, block=None) -> int:
        """
        Returns the next available netuid for subnet registration.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            int: The next available netuid.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return 0
            
            # Call contract's nextNetuid function
            result = await self._contract_call(
                self.subnet_manager,
                "nextNetuid",
                []
            )
            
            if self.log_verbose:
                logging.info(f"Next netuid: {result}")
            
            return result
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get next netuid: {e}")
            return 0

    async def _contract_call(self, contract, function_name: str, args: list = None) -> Any:
        """
        Helper method to make async contract calls.
        
        Args:
            contract: The contract instance
            function_name (str): The function name to call
            args (list): The arguments to pass to the function
            
        Returns:
            Any: The result of the contract call
        """
        try:
            args = args or []
            function = getattr(contract.functions, function_name)
            tx = await function(*args).call()
            return tx
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Contract call failed for {function_name}: {e}")
            raise e
