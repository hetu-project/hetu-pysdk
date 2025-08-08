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
    EVMSubnetInfo,
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
        username: Optional[str] = None,
        password: Optional[str] = None,
        wallet_path: Optional[str] = None,
    ):
        """
        Initializes an instance of the HetuClient class for EVM/ETH networks.
        
        Args:
            network (Optional[str]): Network name.
            config (Optional[Config]): Configuration object.
            log_verbose (bool): Enable verbose logging.
            fallback_endpoints (Optional[list[str]]): Fallback endpoints.
            retry_forever (bool): Retry forever on connection errors.
            _mock (bool): Enable mock mode.
            username (Optional[str]): Wallet username/name.
            password (Optional[str]): Wallet password.
            wallet_path (Optional[str]): Custom wallet path.
        """
        self.network = network or "local"
        self._config = config
        self.log_verbose = log_verbose
        if network in NETWORKS:
            self.chain_endpoint = NETWORK_MAP[network]
        else:
            self.chain_endpoint = "http://161.97.161.133:8545"  # Default mock endpoint
        self.web3 = Web3(HTTPProvider(self.chain_endpoint))
        if self.log_verbose:
            logging.info(
                f"Connected to {self.network} network at {self.chain_endpoint} (EVM mock mode)."
            )
        
        # 初始化合约
        self._init_contract()
        
        # 初始化钱包
        self._init_wallet(username, password, wallet_path)

    def _init_wallet(self, username: Optional[str] = None, password: Optional[str] = None, wallet_path: Optional[str] = None):
        """
        初始化钱包
        
        Args:
            username (Optional[str]): 钱包用户名
            password (Optional[str]): 钱包密码
            wallet_path (Optional[str]): 钱包路径
        """
        from hetu.utils.wallet import unlock_wallet
        
        self.wallet = None
        self.wallet_name = None
        self.wallet_path = wallet_path
        
        if username and password:
            # 使用提供的用户名和密码解锁钱包
            try:
                self.wallet = unlock_wallet(username, password, wallet_path)
                self.wallet_name = username
                if self.log_verbose:
                    logging.info(f"Unlocked wallet: {self.wallet.address}")
            except Exception as e:
                if self.log_verbose:
                    logging.error(f"Failed to unlock wallet with provided credentials: {e}")
                raise e

    def set_wallet_from_username(self, username: str, password: str, wallet_path: Optional[str] = None) -> bool:
        """
        通过用户名和密码设置钱包
        
        Args:
            username (str): 钱包用户名
            password (str): 钱包密码
            wallet_path (Optional[str]): 钱包路径
            
        Returns:
            bool: 是否成功设置钱包
        """
        from hetu.utils.wallet import unlock_wallet
        
        try:
            self.wallet = unlock_wallet(username, password, wallet_path or self.wallet_path)
            self.wallet_name = username
            if self.log_verbose:
                logging.info(f"Set wallet from username: {self.wallet.address}")
            return True
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to set wallet from username: {e}")
            return False

    def set_wallet_from_private_key(self, private_key: str, wallet_name: Optional[str] = None) -> bool:
        """
        通过私钥设置钱包
        
        Args:
            private_key (str): 私钥（十六进制格式）
            wallet_name (Optional[str]): 钱包名称（可选）
            
        Returns:
            bool: 是否成功设置钱包
        """
        from eth_account import Account
        
        try:
            self.wallet = Account.from_key(private_key)
            self.wallet_name = wallet_name or f"imported_{self.wallet.address[:8]}"
            if self.log_verbose:
                logging.info(f"Set wallet from private key: {self.wallet.address}")
            return True
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to set wallet from private key: {e}")
            return False

    def clear_wallet(self):
        """
        清除当前钱包设置
        """
        self.wallet = None
        self.wallet_name = None
        if self.log_verbose:
            logging.info("Wallet cleared")

    def has_wallet(self) -> bool:
        """
        检查是否有设置的钱包
        
        Returns:
            bool: 是否有钱包
        """
        return self.wallet is not None

    def get_wallet_address(self) -> Optional[str]:
        """
        获取钱包地址
        
        Returns:
            Optional[str]: 钱包地址，如果没有设置则返回None
        """
        return self.wallet.address if self.wallet else None

    # ===================== Neuron Management Methods =====================

    def get_neuron_info(self, netuid: int, account: str, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns neuron information for a specific account on a subnet.
        
        Args:
            netuid (int): The subnet ID.
            account (str): The neuron account address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Neuron information.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return None
            
            # 调用合约的getNeuronInfo函数
            result = self.neuron_manager.functions.getNeuronInfo(netuid, account).call()
            
            if self.log_verbose:
                logging.info(f"Raw neuron info for {account} on netuid {netuid}: {result}")
            
            # 解析返回的结果 - 根据ABI中的NeuronInfo结构体
            # result[0] = account
            # result[1] = netuid  
            # result[2] = isActive
            # result[3] = isValidator
            # result[4] = stake
            # result[5] = registrationBlock
            # result[6] = lastUpdate
            # result[7] = axonEndpoint
            # result[8] = axonPort
            # result[9] = prometheusEndpoint
            # result[10] = prometheusPort
            
            neuron_info = {
                "account": result[0],
                "netuid": result[1],
                "is_active": result[2],
                "is_validator": result[3],
                "stake": result[4],
                "registration_block": result[5],
                "last_update": result[6],
                "axon_endpoint": result[7],
                "axon_port": result[8],
                "prometheus_endpoint": result[9],
                "prometheus_port": result[10]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed neuron info:")
                logging.info(f"  account: {neuron_info['account']}")
                logging.info(f"  netuid: {neuron_info['netuid']}")
                logging.info(f"  is_active: {neuron_info['is_active']}")
                logging.info(f"  is_validator: {neuron_info['is_validator']}")
                logging.info(f"  stake: {neuron_info['stake']}")
            
            return neuron_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get neuron info for {account} on netuid {netuid}: {e}")
            return None

    def get_subnet_neuron_count(self, netuid: int, block: Optional[int] = None) -> Optional[int]:
        """
        Returns the number of neurons in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Number of neurons.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return None
            
            # 调用合约的getSubnetNeuronCount函数
            count = self.neuron_manager.functions.getSubnetNeuronCount(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} neuron count: {count}")
            
            return count
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet neuron count for netuid {netuid}: {e}")
            return None

    def get_subnet_neurons(self, netuid: int, block: Optional[int] = None) -> list[str]:
        """
        Returns all neuron addresses in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[str]: List of neuron addresses.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return []
            
            # 调用合约的getNeuronList函数
            neurons = self.neuron_manager.functions.getNeuronList(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} neurons: {neurons}")
            
            return neurons
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet neurons for netuid {netuid}: {e}")
            return []

    def get_subnet_validator_count(self, netuid: int, block: Optional[int] = None) -> Optional[int]:
        """
        Returns the number of validators in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Number of validators.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return None
            
            # 调用合约的getSubnetValidatorCount函数
            count = self.neuron_manager.functions.getSubnetValidatorCount(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} validator count: {count}")
            
            return count
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet validator count for netuid {netuid}: {e}")
            return None

    def get_subnet_validators(self, netuid: int, block: Optional[int] = None) -> list[str]:
        """
        Returns all validator addresses in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[str]: List of validator addresses.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return []
            
            # 调用合约的getSubnetValidators函数
            validators = self.neuron_manager.functions.getSubnetValidators(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} validators: {validators}")
            
            return validators
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet validators for netuid {netuid}: {e}")
            return []

    def is_neuron(self, netuid: int, account: str, block: Optional[int] = None) -> bool:
        """
        Checks if an account is a neuron in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            account (str): The account address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the account is a neuron, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            # 调用合约的isNeuron函数
            is_neuron = self.neuron_manager.functions.isNeuron(netuid, account).call()
            
            if self.log_verbose:
                logging.info(f"Is neuron {account} on netuid {netuid}: {is_neuron}")
            
            return is_neuron
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if {account} is neuron on netuid {netuid}: {e}")
            return False

    def is_validator(self, netuid: int, account: str, block: Optional[int] = None) -> bool:
        """
        Checks if an account is a validator in a subnet.
        
        Args:
            netuid (int): The subnet ID.
            account (str): The account address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the account is a validator, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            # 调用合约的isValidator函数
            is_validator = self.neuron_manager.functions.isValidator(netuid, account).call()
            
            if self.log_verbose:
                logging.info(f"Is validator {account} on netuid {netuid}: {is_validator}")
            
            return is_validator
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if {account} is validator on netuid {netuid}: {e}")
            return False

    def can_register_neuron(self, user: str, netuid: int, is_validator_role: bool, block: Optional[int] = None) -> bool:
        """
        Checks if a user can register as a neuron.
        
        Args:
            user (str): The user address.
            netuid (int): The subnet ID.
            is_validator_role (bool): Whether the user wants to register as a validator.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the user can register, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            # ABI中没有canRegisterNeuron函数，暂时返回False
            if self.log_verbose:
                logging.warning(f"canRegisterNeuron function not available in ABI, returning False for {user} on netuid {netuid}")
            
            return False
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if {user} can register neuron on netuid {netuid}: {e}")
            return False

    def register_neuron(self, netuid: int, is_validator_role: bool, axon_endpoint: str, axon_port: int, 
                       prometheus_endpoint: str, prometheus_port: int, **kwargs) -> bool:
        """
        Registers a neuron on a subnet.
        
        Args:
            netuid (int): The subnet ID.
            is_validator_role (bool): Whether to register as a validator.
            axon_endpoint (str): The axon endpoint.
            axon_port (int): The axon port.
            prometheus_endpoint (str): The prometheus endpoint.
            prometheus_port (int): The prometheus port.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if registration was successful, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            if not self.wallet:
                if self.log_verbose:
                    logging.error("No wallet set. Please set a wallet first.")
                return False
            
            if self.log_verbose:
                logging.info(f"Registering neuron on netuid {netuid}")
                logging.info(f"  Validator role: {is_validator_role}")
                logging.info(f"  Axon endpoint: {axon_endpoint}:{axon_port}")
                logging.info(f"  Prometheus endpoint: {prometheus_endpoint}:{prometheus_port}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(self.wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 500000)
            tx = self.neuron_manager.functions.registerNeuronWithStakeAllocation(
                netuid, 0, is_validator_role, axon_endpoint, axon_port, prometheus_endpoint, prometheus_port
            ).build_transaction({
                "from": self.wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, self.wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Register neuron transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
                logging.info(f"Receipt block number: {receipt.blockNumber}")
                logging.info(f"Gas used: {receipt.gasUsed}")
                if hasattr(receipt, 'logs') and receipt.logs:
                    logging.info(f"Receipt logs: {receipt.logs}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Neuron registration successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Neuron registration failed in block {receipt.blockNumber}")
                    logging.error(f"Receipt: {receipt}")
                    # 尝试解析错误信息
                    try:
                        # 检查是否有错误日志
                        if hasattr(receipt, 'logs') and receipt.logs:
                            for log in receipt.logs:
                                logging.error(f"Error log: {log}")
                    except Exception as parse_error:
                        logging.error(f"Failed to parse error logs: {parse_error}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to register neuron: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def deregister_neuron(self, netuid: int, **kwargs) -> bool:
        """
        Deregisters a neuron from a subnet.
        
        Args:
            netuid (int): The subnet ID.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if deregistration was successful, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            if not self.wallet:
                if self.log_verbose:
                    logging.error("No wallet set. Please set a wallet first.")
                return False
            
            if self.log_verbose:
                logging.info(f"Deregistering neuron from netuid {netuid}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(self.wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.neuron_manager.functions.deregisterNeuron(netuid).build_transaction({
                "from": self.wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, self.wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Deregister neuron transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Neuron deregistration successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Neuron deregistration failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to deregister neuron: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def update_service(self, netuid: int, axon_endpoint: str, axon_port: int, 
                      prometheus_endpoint: str, prometheus_port: int, **kwargs) -> bool:
        """
        Updates neuron service information.
        
        Args:
            netuid (int): The subnet ID.
            axon_endpoint (str): The axon endpoint.
            axon_port (int): The axon port.
            prometheus_endpoint (str): The prometheus endpoint.
            prometheus_port (int): The prometheus port.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            if not self.neuron_manager:
                if self.log_verbose:
                    logging.error("Neuron manager contract not initialized")
                return False
            
            if not self.wallet:
                if self.log_verbose:
                    logging.error("No wallet set. Please set a wallet first.")
                return False
            
            if self.log_verbose:
                logging.info(f"Updating service for netuid {netuid}")
                logging.info(f"  Axon endpoint: {axon_endpoint}:{axon_port}")
                logging.info(f"  Prometheus endpoint: {prometheus_endpoint}:{prometheus_port}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(self.wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.neuron_manager.functions.updateNeuronService(
                netuid, axon_endpoint, axon_port, prometheus_endpoint, prometheus_port
            ).build_transaction({
                "from": self.wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, self.wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Update service transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Service update successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Service update failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to update service: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _init_contract(self):
        """
        初始化Hetu智能合约
        加载所有合约的ABI和地址
        """
        import json
        import os
        
        # 合约地址配置
        self.contract_addresses = {
            "WHETU_TOKEN": "0x10Fc0865C678B3727c842812bE004af3661FA5Ee",
            "AMM_FACTORY": "0x9aA413fD38582d9aAD6328dd034504F322ea624B", 
            "GLOBAL_STAKING": "0x24a9Cc5d0Baa1b9a049DA81b615A53ad8e2d3b9E",
            "SUBNET_MANAGER": "0x591C3103a983Cb92FE4254f8D1a7CC7710B8A0E5",
            "NEURON_MANAGER": "0x756a874E457756fff16446ef85384FfE8aEf65b0"
        }
        
        # 合约ABI文件路径
        contracts_dir = os.path.join(os.path.dirname(__file__), "..", "contracts")
        abi_files = {
            "WHETU_TOKEN": "WHETU.abi",
            "AMM_FACTORY": "SubnetAMM.abi", 
            "GLOBAL_STAKING": "GlobalStaking.abi",
            "SUBNET_MANAGER": "SubnetManager.abi",
            "NEURON_MANAGER": "NeuronManager.abi"
        }
        
        # 初始化合约实例
        self.contracts = {}
        
        for contract_name, abi_file in abi_files.items():
            try:
                abi_path = os.path.join(contracts_dir, abi_file)
                if os.path.exists(abi_path):
                    with open(abi_path, 'r') as f:
                        abi = json.load(f)
                    
                    contract_address = self.contract_addresses[contract_name]
                    contract = self.web3.eth.contract(
                        address=contract_address,
                        abi=abi
                    )
                    
                    self.contracts[contract_name] = contract
                    
                    if self.log_verbose:
                        logging.info(f"✅ 初始化合约: {contract_name} at {contract_address}")
                        
                else:
                    if self.log_verbose:
                        logging.warning(f"⚠️ ABI文件不存在: {abi_path}")
                        
            except Exception as e:
                if self.log_verbose:
                    logging.error(f"❌ 初始化合约 {contract_name} 失败: {e}")
        
        # 为方便访问，添加直接属性
        self.whetu_token = self.contracts.get("WHETU_TOKEN")
        self.subnet_manager = self.contracts.get("SUBNET_MANAGER")
        self.neuron_manager = self.contracts.get("NEURON_MANAGER")
        self.global_staking = self.contracts.get("GLOBAL_STAKING")
        self.amm_factory = self.contracts.get("AMM_FACTORY")

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

    def get_all_subnets_info(self, block: Optional[int] = None) -> list[EVMSubnetInfo]:
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
            
            # 获取下一个netuid作为上限
            next_netuid = self.get_next_netuid(block)
            if self.log_verbose:
                logging.info(f"Next netuid: {next_netuid}")
            
            if next_netuid == 0:
                if self.log_verbose:
                    logging.info("No subnets found (next_netuid is 0)")
                return []
            
            subnet_info_list = []
            
            # 遍历从0到next_netuid-1的所有可能netuid
            for netuid in range(next_netuid):
                try:
                    if self.log_verbose:
                        logging.info(f"Checking netuid {netuid}...")
                    
                    # 检查子网是否存在
                    if self.is_subnet_exists(netuid, block):
                        subnet_info = self.get_subnet_info(netuid, block)
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
    ) -> Optional[EVMSubnetInfo]:
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
            
            # 调用合约的getSubnetDetails函数
            result = self.subnet_manager.functions.getSubnetDetails(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Raw subnet details for netuid {netuid}: {result}")
            
            # 解析返回的结果
            # result[0] 是 subnetInfo 结构体
            # result[1] 是 currentPrice
            # result[2] 是 totalVolume  
            # result[3] 是 hetuReserve
            # result[4] 是 alphaReserve
            
            subnet_info_tuple = result[0]
            market_data = (result[1], result[2], result[3], result[4])
            
            # 使用EVMSubnetInfo.from_contract_data创建对象
            evm_subnet_info = EVMSubnetInfo.from_contract_data(subnet_info_tuple, market_data)
            
            if self.log_verbose:
                logging.info(f"Created EVMSubnetInfo for netuid {netuid}:")
                logging.info(f"  name: {evm_subnet_info.name}")
                logging.info(f"  description: {evm_subnet_info.description}")
                logging.info(f"  owner: {evm_subnet_info.owner}")
                logging.info(f"  is_active: {evm_subnet_info.is_active}")
                logging.info(f"  locked_amount: {evm_subnet_info.locked_amount}")
                logging.info(f"  burned_amount: {evm_subnet_info.burned_amount}")
                logging.info(f"  current_price: {evm_subnet_info.current_price}")
                logging.info(f"  total_volume: {evm_subnet_info.total_volume}")
            
            return evm_subnet_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet info for netuid {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_subnets(self, block: Optional[int] = None) -> list[int]:
        """
        Returns a list of all subnet IDs using the subnet manager contract.
        Skips netuid 0 (root subnet) and returns IDs starting from 1.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[int]: List of subnet IDs, starting from 1 up to and including total_subnets-1.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return []
            
            # Get total subnets
            total_subnets = self.get_total_subnets(block)
            if total_subnets <= 1:  # If only root subnet exists
                if self.log_verbose:
                    logging.info("No non-root subnets found")
                return []
            
            # Return list from 1 to total_subnets (inclusive)
            subnet_ids = list(range(1, total_subnets + 1))
            
            if self.log_verbose:
                logging.info(f"Found {len(subnet_ids)} non-root subnets: {subnet_ids}")
            
            return subnet_ids
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnets: {e}")
            return []

    def get_total_subnets(self, block: Optional[int] = None) -> Optional[int]:
        """Returns the total number of subnets using the subnet manager contract."""
        try:
            if self.subnet_manager:
                # 使用合约调用获取总子网数
                total_networks = self.subnet_manager.functions.totalNetworks().call()
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
        """
        Checks if a subnet is active using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the subnet is active, False otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            # 获取子网信息
            subnet_info = self.get_subnet_info(netuid, block)
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

    def register_subnet(
        self, 
        wallet: "Account", 
        name: str = None,
        description: str = None,
        token_name: str = None,
        token_symbol: str = None,
        gas_limit: int = 10000000,  # 增加到1000万gas
        **kwargs
    ) -> bool:
        """
        Register a new subnet using the subnet manager contract.
        
        Args:
            wallet: The wallet account to use for registration
            name: Subnet name
            description: Subnet description  
            token_name: Token name for the subnet
            token_symbol: Token symbol for the subnet
            gas_limit: Gas limit for the transaction
            **kwargs: Additional arguments
            
        Returns:
            bool: True if registration was successful, False otherwise
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            # 设置默认值
            name = name or kwargs.get('name', 'Default Subnet')
            description = description or kwargs.get('description', 'A default subnet')
            token_name = token_name or kwargs.get('token_name', 'Default Token')
            token_symbol = token_symbol or kwargs.get('token_symbol', 'DT')
            
            if self.log_verbose:
                logging.info(f"Registering subnet: {name}")
                logging.info(f"Description: {description}")
                logging.info(f"Token: {token_name} ({token_symbol})")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            tx = self.subnet_manager.functions.registerNetwork(
                name, description, token_name, token_symbol
            ).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 估算gas使用量
            try:
                estimated_gas = self.subnet_manager.functions.registerNetwork(
                    name, description, token_name, token_symbol
                ).estimate_gas({
                    "from": wallet.address,
                })
                if self.log_verbose:
                    logging.info(f"Estimated gas: {estimated_gas}")
                    logging.info(f"Gas limit: {gas_limit}")
                    if estimated_gas > gas_limit:
                        logging.warning(f"Estimated gas ({estimated_gas}) exceeds gas limit ({gas_limit})")
            except Exception as gas_error:
                if self.log_verbose:
                    logging.warning(f"Failed to estimate gas: {gas_error}")
            
            if self.log_verbose:
                logging.info(f"Transaction built: {tx}")
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
                logging.info(f"Receipt block number: {receipt.blockNumber}")
                logging.info(f"Gas used: {receipt.gasUsed}")
                if hasattr(receipt, 'logs') and receipt.logs:
                    logging.info(f"Receipt logs: {receipt.logs}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Subnet registration successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Subnet registration failed in block {receipt.blockNumber}")
                    logging.error(f"Receipt: {receipt}")
                    # 尝试解析错误信息
                    try:
                        # 检查是否有错误日志
                        if hasattr(receipt, 'logs') and receipt.logs:
                            for log in receipt.logs:
                                logging.error(f"Error log: {log}")
                    except Exception as parse_error:
                        logging.error(f"Failed to parse error logs: {parse_error}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to register subnet: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

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
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
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

    def query_raw_checkpoint_list(self, grpc_endpoint: str, request) -> object:
        """
        Calls the RawCheckpointList gRPC method on the hetu.checkpointing.v1.Query service.
        Args:
            grpc_endpoint (str): gRPC server address, e.g. 'localhost:9090'.
            request: QueryRawCheckpointListRequest protobuf message.
        Returns:
            QueryRawCheckpointListResponse protobuf message.
        """
        import grpc
        from hetu.cosmos.hetu.checkpointing.v1 import query_pb2_grpc

        with grpc.insecure_channel(grpc_endpoint) as channel:
            stub = query_pb2_grpc.QueryStub(channel)
            response = stub.RawCheckpointList(request)
            return response

    def get_network_params(self, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns current network parameters using the subnet manager contract.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Network parameters including minLock, lastLock, lastLockBlock, rateLimit, etc.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # 调用合约的getNetworkParams函数
            result = self.subnet_manager.functions.getNetworkParams().call()
            
            if self.log_verbose:
                logging.info(f"Network params: {result}")
            
            # 解析返回的结果
            # result[0] = minLock
            # result[1] = lastLock  
            # result[2] = lastLockBlock
            # result[3] = rateLimit
            # result[4] = reductionInterval
            # result[5] = totalNets
            # result[6] = nextId
            
            params = {
                "min_lock": result[0],
                "last_lock": result[1],
                "last_lock_block": result[2],
                "rate_limit": result[3],
                "reduction_interval": result[4],
                "total_networks": result[5],
                "next_netuid": result[6]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed network params:")
                logging.info(f"  min_lock: {params['min_lock']}")
                logging.info(f"  last_lock: {params['last_lock']}")
                logging.info(f"  last_lock_block: {params['last_lock_block']}")
                logging.info(f"  rate_limit: {params['rate_limit']}")
                logging.info(f"  total_networks: {params['total_networks']}")
                logging.info(f"  next_netuid: {params['next_netuid']}")
            
            return params
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get network params: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_network_lock_cost(self, block: Optional[int] = None) -> Optional[int]:
        """
        Returns the current network lock cost using the subnet manager contract.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Current lock cost in wei.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # 调用合约的getNetworkLockCost函数
            lock_cost = self.subnet_manager.functions.getNetworkLockCost().call()
            
            if self.log_verbose:
                logging.info(f"Network lock cost: {lock_cost}")
            
            return lock_cost
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get network lock cost: {e}")
            return None

    def get_next_netuid(self, block: Optional[int] = None) -> Optional[int]:
        """
        Returns the next available netuid using the subnet manager contract.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Next available netuid.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # 调用合约的getNextNetuid函数
            next_netuid = self.subnet_manager.functions.getNextNetuid().call()
            
            if self.log_verbose:
                logging.info(f"Next netuid: {next_netuid}")
            
            return next_netuid
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get next netuid: {e}")
            return None

    def get_subnet_hyperparams(self, netuid: int, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns subnet hyperparameters using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Subnet hyperparameters.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # 调用合约的getSubnetHyperparams函数
            result = self.subnet_manager.functions.getSubnetHyperparams(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Raw hyperparams for netuid {netuid}: {result}")
            
            # 解析返回的结构体
            # result是一个包含21个字段的元组
            hyperparams = {
                "rho": result[0],
                "kappa": result[1],
                "immunity_period": result[2],
                "tempo": result[3],
                "max_validators": result[4],
                "activity_cutoff": result[5],
                "max_allowed_uids": result[6],
                "max_allowed_validators": result[7],
                "min_allowed_weights": result[8],
                "max_weights_limit": result[9],
                "base_burn_cost": result[10],
                "current_difficulty": result[11],
                "target_regs_per_interval": result[12],
                "max_regs_per_block": result[13],
                "weights_rate_limit": result[14],
                "registration_allowed": result[15],
                "commit_reveal_enabled": result[16],
                "commit_reveal_period": result[17],
                "serving_rate_limit": result[18],
                "validator_threshold": result[19],
                "neuron_threshold": result[20]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed hyperparams for netuid {netuid}:")
                logging.info(f"  rho: {hyperparams['rho']}")
                logging.info(f"  kappa: {hyperparams['kappa']}")
                logging.info(f"  max_validators: {hyperparams['max_validators']}")
                logging.info(f"  registration_allowed: {hyperparams['registration_allowed']}")
            
            return hyperparams
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet hyperparams for netuid {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_subnet_params(self, netuid: int, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns subnet parameters using the subnet manager contract.
        
        Args:
            netuid (int): The unique identifier of the subnet.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Subnet parameters.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return None
            
            # 调用合约的getSubnetParams函数
            result = self.subnet_manager.functions.getSubnetParams(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Raw subnet params for netuid {netuid}: {result}")
            
            # 解析返回的结果
            # result是一个包含多个字段的元组，对应SubnetTypes.SubnetHyperparams结构体
            subnet_params = {
                "rho": result[0],
                "kappa": result[1], 
                "immunity_period": result[2],
                "tempo": result[3],
                "max_validators": result[4],
                "activity_cutoff": result[5],
                "max_allowed_uids": result[6],
                "max_allowed_validators": result[7],
                "min_allowed_weights": result[8],
                "max_weights_limit": result[9],
                "base_burn_cost": result[10],
                "current_difficulty": result[11],
                "target_regs_per_interval": result[12],
                "max_regs_per_block": result[13],
                "weights_rate_limit": result[14],
                "registration_allowed": result[15],
                "commit_reveal_enabled": result[16],
                "commit_reveal_period": result[17],
                "serving_rate_limit": result[18],
                "validator_threshold": result[19],
                "neuron_threshold": result[20]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed subnet params for netuid {netuid}:")
                logging.info(f"  rho: {subnet_params['rho']}")
                logging.info(f"  kappa: {subnet_params['kappa']}")
                logging.info(f"  immunity_period: {subnet_params['immunity_period']}")
                logging.info(f"  tempo: {subnet_params['tempo']}")
                logging.info(f"  max_validators: {subnet_params['max_validators']}")
                logging.info(f"  activity_cutoff: {subnet_params['activity_cutoff']}")
                logging.info(f"  registration_allowed: {subnet_params['registration_allowed']}")
                logging.info(f"  commit_reveal_enabled: {subnet_params['commit_reveal_enabled']}")
            
            return subnet_params
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet params for netuid {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_user_subnets(self, user_address: str, block: Optional[int] = None) -> list[int]:
        """
        Returns all subnets owned by a user using the subnet manager contract.
        
        Args:
            user_address (str): The user's address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            list[int]: List of subnet IDs owned by the user.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return []
            
            # 调用合约的getUserSubnets函数
            subnet_ids = self.subnet_manager.functions.getUserSubnets(user_address).call()
            
            if self.log_verbose:
                logging.info(f"User {user_address} owns subnets: {subnet_ids}")
            
            return subnet_ids
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get user subnets for {user_address}: {e}")
            return []

    def is_subnet_exists(self, netuid: int, block: Optional[int] = None) -> bool:
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
            
            # 调用合约的subnetExists函数
            exists = self.subnet_manager.functions.subnetExists(netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet {netuid} exists: {exists}")
            
            return exists
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if subnet {netuid} exists: {e}")
            return False

    def activate_subnet(self, wallet: "Account", netuid: int, **kwargs) -> bool:
        """
        Activates a subnet using the subnet manager contract.
        
        Args:
            wallet: The wallet account to use for activation.
            netuid (int): The unique identifier of the subnet.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if activation was successful, False otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Activating subnet {netuid}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.subnet_manager.functions.activateSubnet(netuid).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 估算gas使用量
            try:
                estimated_gas = self.subnet_manager.functions.activateSubnet(netuid).estimate_gas({
                    "from": wallet.address,
                })
                if self.log_verbose:
                    logging.info(f"Estimated gas: {estimated_gas}")
                    if estimated_gas > gas_limit:
                        logging.warning(f"Estimated gas ({estimated_gas}) exceeds gas limit ({gas_limit})")
            except Exception as gas_error:
                if self.log_verbose:
                    logging.warning(f"Failed to estimate gas: {gas_error}")
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Activation transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Subnet {netuid} activation successful")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Subnet {netuid} activation failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to activate subnet {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def reset_network_lock_state(self, wallet: "Account", **kwargs) -> bool:
        """
        Resets the network lock state using the subnet manager contract (owner only).
        
        Args:
            wallet: The wallet account to use (must be owner).
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if reset was successful, False otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info("Resetting network lock state")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 100000)
            tx = self.subnet_manager.functions.resetNetworkLockState().build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Reset transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("Network lock state reset successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("Network lock state reset failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to reset network lock state: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def update_network_params(self, wallet: "Account", min_lock: int, rate_limit: int, reduction_interval: int, **kwargs) -> bool:
        """
        Updates network parameters using the subnet manager contract (owner only).
        
        Args:
            wallet: The wallet account to use (must be owner).
            min_lock (int): New minimum lock amount.
            rate_limit (int): New rate limit.
            reduction_interval (int): New reduction interval.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            if not self.subnet_manager:
                if self.log_verbose:
                    logging.error("Subnet manager contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Updating network params: min_lock={min_lock}, rate_limit={rate_limit}, reduction_interval={reduction_interval}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.subnet_manager.functions.updateNetworkParams(min_lock, rate_limit, reduction_interval).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Update transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("Network params update successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("Network params update failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to update network params: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    # ===================== Global Staking Methods =====================

    def get_stake_info(self, user_address: str, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns stake information for a user using the global staking contract.
        
        Args:
            user_address (str): The user's address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Stake information including totalStaked, totalAllocated, etc.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 调用合约的getStakeInfo函数
            result = self.global_staking.functions.getStakeInfo(user_address).call()
            
            if self.log_verbose:
                logging.info(f"Stake info for {user_address}: {result}")
            
            # 解析返回的结果
            # result[0] = totalStaked
            # result[1] = totalAllocated
            # result[2] = availableForAllocation
            # result[3] = lastUpdateBlock
            # result[4] = pendingRewards
            
            stake_info = {
                "total_staked": result[0],
                "total_allocated": result[1],
                "available_for_allocation": result[2],
                "last_update_block": result[3],
                "pending_rewards": result[4]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed stake info for {user_address}:")
                logging.info(f"  total_staked: {stake_info['total_staked']}")
                logging.info(f"  total_allocated: {stake_info['total_allocated']}")
                logging.info(f"  available_for_allocation: {stake_info['available_for_allocation']}")
                logging.info(f"  pending_rewards: {stake_info['pending_rewards']}")
            
            return stake_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get stake info for {user_address}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_subnet_allocation(self, user_address: str, netuid: int, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns subnet allocation information for a user using the global staking contract.
        
        Args:
            user_address (str): The user's address.
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Subnet allocation information.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 调用合约的getSubnetAllocation函数
            result = self.global_staking.functions.getSubnetAllocation(user_address, netuid).call()
            
            if self.log_verbose:
                logging.info(f"Subnet allocation for {user_address} on netuid {netuid}: {result}")
            
            # 解析返回的结果 - 根据ABI文件，返回的是SubnetAllocation结构体
            # result[0] = allocated
            # result[1] = cost  
            # result[2] = lastUpdateBlock
            
            allocation_info = {
                "allocated": result[0],
                "cost": result[1],
                "last_update_block": result[2]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed subnet allocation:")
                logging.info(f"  allocated: {allocation_info['allocated']}")
                logging.info(f"  cost: {allocation_info['cost']}")
                logging.info(f"  last_update_block: {allocation_info['last_update_block']}")
            
            return allocation_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get subnet allocation for {user_address} on netuid {netuid}: {e}")
            return None

    def get_available_stake(self, user_address: str, netuid: int, block: Optional[int] = None) -> Optional[int]:
        """
        Returns available stake for a user on a specific subnet.
        
        Args:
            user_address (str): The user's address.
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Available stake amount.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 调用合约的getAvailableStake函数 - 只接受user_address参数
            available_stake = self.global_staking.functions.getAvailableStake(user_address).call()
            
            if self.log_verbose:
                logging.info(f"Available stake for {user_address} on netuid {netuid}: {available_stake}")
            
            return available_stake
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get available stake for {user_address} on netuid {netuid}: {e}")
            return None

    def get_effective_stake(self, user_address: str, netuid: int, block: Optional[int] = None) -> Optional[int]:
        """
        Returns effective stake for a user on a specific subnet.
        Note: This function is not available in the current ABI, so we'll use getSubnetAllocation instead.
        
        Args:
            user_address (str): The user's address.
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Effective stake amount.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 使用getSubnetAllocation函数替代
            allocation = self.get_subnet_allocation(user_address, netuid, block)
            if allocation:
                effective_stake = allocation.get('allocated', 0)
                if self.log_verbose:
                    logging.info(f"Effective stake for {user_address} on netuid {netuid}: {effective_stake}")
                return effective_stake
            else:
                if self.log_verbose:
                    logging.warning(f"No allocation found for {user_address} on netuid {netuid}")
                return 0
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get effective stake for {user_address} on netuid {netuid}: {e}")
            return None

    def get_locked_stake(self, user_address: str, netuid: int, block: Optional[int] = None) -> Optional[int]:
        """
        Returns locked stake for a user on a specific subnet.
        Note: This function is not available in the current ABI, so we'll return 0 for now.
        
        Args:
            user_address (str): The user's address.
            netuid (int): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Locked stake amount.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 当前ABI中没有getLockedStake函数，暂时返回0
            if self.log_verbose:
                logging.warning(f"getLockedStake function not available in current ABI for {user_address} on netuid {netuid}")
            
            return 0
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get locked stake for {user_address} on netuid {netuid}: {e}")
            return None

    def get_total_staked(self, block: Optional[int] = None) -> Optional[int]:
        """
        Returns total staked amount across all users.
        
        Args:
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: Total staked amount.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 调用合约的getTotalStaked函数
            total_staked = self.global_staking.functions.getTotalStaked().call()
            
            if self.log_verbose:
                logging.info(f"Total staked: {total_staked}")
            
            return total_staked
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get total staked: {e}")
            return None

    def get_user_stake_info(self, user_address: str, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns user stake information including allocated subnets.
        
        Args:
            user_address (str): The user's address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: User stake information.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return None
            
            # 调用合约的getUserStakeInfo函数
            result = self.global_staking.functions.getUserStakeInfo(user_address).call()
            
            if self.log_verbose:
                logging.info(f"User stake info for {user_address}: {result}")
            
            # 解析返回的结果
            # result[0] = totalStaked_
            # result[1] = availableForAllocation
            # result[2] = allocatedSubnets
            
            user_stake_info = {
                "total_staked": result[0],
                "available_for_allocation": result[1],
                "allocated_subnets": result[2]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed user stake info:")
                logging.info(f"  total_staked: {user_stake_info['total_staked']}")
                logging.info(f"  available_for_allocation: {user_stake_info['available_for_allocation']}")
                logging.info(f"  allocated_subnets: {user_stake_info['allocated_subnets']}")
            
            return user_stake_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get user stake info for {user_address}: {e}")
            return None

    def can_become_neuron(self, user_address: str, netuid: int, required_amount: int, block: Optional[int] = None) -> bool:
        """
        Checks if a user can become a neuron on a specific subnet.
        
        Args:
            user_address (str): The user's address.
            netuid (int): The subnet ID.
            required_amount (int): The required stake amount.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the user can become a neuron, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            # 调用合约的canBecomeNeuron函数
            can_become = self.global_staking.functions.canBecomeNeuron(user_address, netuid, required_amount).call()
            
            if self.log_verbose:
                logging.info(f"Can become neuron for {user_address} on netuid {netuid}: {can_become}")
            
            return can_become
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check if {user_address} can become neuron on netuid {netuid}: {e}")
            return False

    def has_participation_eligibility(self, user_address: str, block: Optional[int] = None) -> bool:
        """
        Checks if a user has participation eligibility.
        
        Args:
            user_address (str): The user's address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            bool: True if the user has participation eligibility, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            # 调用合约的hasParticipationEligibility函数
            has_eligibility = self.global_staking.functions.hasParticipationEligibility(user_address).call()
            
            if self.log_verbose:
                logging.info(f"Participation eligibility for {user_address}: {has_eligibility}")
            
            return has_eligibility
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to check participation eligibility for {user_address}: {e}")
            return False

    # ===================== WHETU Token Methods =====================

    def get_whetu_balance(self, address: str, block: Optional[int] = None) -> Optional[int]:
        """
        Returns WHETU token balance for an address.
        
        Args:
            address (str): The address to check.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: WHETU token balance.
        """
        try:
            if not self.whetu_token:
                if self.log_verbose:
                    logging.error("WHETU token contract not initialized")
                return None
            
            # 调用合约的balanceOf函数
            balance = self.whetu_token.functions.balanceOf(address).call()
            
            if self.log_verbose:
                logging.info(f"WHETU balance for {address}: {balance}")
            
            return balance
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get WHETU balance for {address}: {e}")
            return None

    def get_whetu_allowance(self, owner: str, spender: str, block: Optional[int] = None) -> Optional[int]:
        """
        Returns WHETU token allowance for a spender.
        
        Args:
            owner (str): The token owner's address.
            spender (str): The spender's address.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[int]: WHETU token allowance.
        """
        try:
            if not self.whetu_token:
                if self.log_verbose:
                    logging.error("WHETU token contract not initialized")
                return None
            
            # 调用合约的allowance函数
            allowance = self.whetu_token.functions.allowance(owner, spender).call()
            
            if self.log_verbose:
                logging.info(f"WHETU allowance for {spender} from {owner}: {allowance}")
            
            return allowance
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get WHETU allowance for {spender} from {owner}: {e}")
            return None

    def approve_whetu(self, wallet: "Account", spender: str, amount: int, **kwargs) -> bool:
        """
        Approves WHETU token spending for a spender.
        
        Args:
            wallet: The wallet account to use.
            spender (str): The spender's address.
            amount (int): The amount to approve.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if approval was successful, False otherwise.
        """
        try:
            if not self.whetu_token:
                if self.log_verbose:
                    logging.error("WHETU token contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Approving {amount} WHETU for {spender}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 100000)
            tx = self.whetu_token.functions.approve(spender, amount).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Approval transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("WHETU approval successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("WHETU approval failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to approve WHETU: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    # ===================== Staking Operations =====================

    def add_global_stake(self, wallet: "Account", amount: int, **kwargs) -> bool:
        """
        Adds global stake using the global staking contract.
        
        Args:
            wallet: The wallet account to use.
            amount (int): The amount to stake.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if staking was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Adding global stake: {amount}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.global_staking.functions.addGlobalStake(amount).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Add global stake transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("Global stake addition successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("Global stake addition failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to add global stake: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def remove_global_stake(self, wallet: "Account", amount: int, **kwargs) -> bool:
        """
        Removes global stake using the global staking contract.
        
        Args:
            wallet: The wallet account to use.
            amount (int): The amount to unstake.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if unstaking was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Removing global stake: {amount}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.global_staking.functions.removeGlobalStake(amount).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Remove global stake transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("Global stake removal successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("Global stake removal failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to remove global stake: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def allocate_to_subnet(self, wallet: "Account", netuid: int, amount: int, **kwargs) -> bool:
        """
        Allocates stake to a specific subnet.
        
        Args:
            wallet: The wallet account to use.
            netuid (int): The subnet ID.
            amount (int): The amount to allocate.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if allocation was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info(f"Allocating {amount} to subnet {netuid}")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 200000)
            tx = self.global_staking.functions.allocateToSubnet(netuid, amount).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Allocate to subnet transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Allocation to subnet {netuid} successful")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Allocation to subnet {netuid} failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to allocate to subnet {netuid}: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def lock_subnet_stake(self, wallet: "Account", netuid: int, amount: int, **kwargs) -> bool:
        """
        Locks stake for a subnet (currently not supported by the contract).
        
        Args:
            wallet: The wallet account to use.
            netuid (int): The subnet ID.
            amount (int): The amount to lock.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if locking was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.warning(f"Lock subnet stake function not supported by the contract")
                logging.warning(f"Netuid: {netuid}, Amount: {amount}")
            
            # 这个功能在当前合约中不存在
            return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to lock subnet stake: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def unlock_subnet_stake(self, wallet: "Account", netuid: int, amount: int, **kwargs) -> bool:
        """
        Unlocks stake for a subnet (currently not supported by the contract).
        
        Args:
            wallet: The wallet account to use.
            netuid (int): The subnet ID.
            amount (int): The amount to unlock.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if unlocking was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.warning(f"Unlock subnet stake function not supported by the contract")
                logging.warning(f"Netuid: {netuid}, Amount: {amount}")
            
            # 这个功能在当前合约中不存在
            return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to unlock subnet stake: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def claim_rewards(self, wallet: "Account", **kwargs) -> bool:
        """
        Claims rewards from the global staking contract.
        
        Args:
            wallet: The wallet account to use.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if claiming was successful, False otherwise.
        """
        try:
            if not self.global_staking:
                if self.log_verbose:
                    logging.error("Global staking contract not initialized")
                return False
            
            if self.log_verbose:
                logging.info("Claiming rewards")
            
            # 获取nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # 构建交易
            gas_limit = kwargs.get('gas_limit', 150000)
            tx = self.global_staking.functions.claimRewards().build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # 签名交易
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Claim rewards transaction sent: {tx_hash.hex()}")
            
            # 等待交易收据
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if self.log_verbose:
                logging.info(f"Transaction receipt: {receipt}")
                logging.info(f"Receipt status: {receipt.status}")
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info("Rewards claiming successful")
                return True
            else:
                if self.log_verbose:
                    logging.error("Rewards claiming failed")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to claim rewards: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    # ===================== AMM Methods =====================

    def get_amm_contract_address(self, netuid: Optional[int] = None, pool_address: Optional[str] = None) -> Optional[str]:
        """
        Get AMM contract address either from netuid or directly from pool_address.
        Only one of netuid or pool_address should be provided.
        
        Args:
            netuid (Optional[int]): The subnet ID.
            pool_address (Optional[str]): The AMM pool contract address.
            
        Returns:
            Optional[str]: The AMM contract address if found, None otherwise.
        """
        if netuid is not None and pool_address is not None:
            if self.log_verbose:
                logging.error("Only one of netuid or pool_address should be provided")
            return None
            
        if netuid is not None:
            # Get subnet info to find AMM contract address
            subnet_info = self.get_subnet_info(netuid)
            if subnet_info is None:
                if self.log_verbose:
                    logging.error(f"Failed to get subnet info for netuid {netuid}")
                return None
            return subnet_info.amm_pool  # 修改这里，使用正确的属性名
        
        return pool_address

    def get_amm_pool_info(self, pool_address: Optional[str] = None, netuid: Optional[int] = None, block: Optional[int] = None) -> Optional[dict]:
        """
        Returns information about an AMM pool.
        
        Args:
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Pool information if found, None otherwise.
        """
        try:
            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return None

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            # Get pool info
            result = amm_contract.functions.getPoolInfo().call()
            
            if self.log_verbose:
                logging.info(f"Raw pool info for {amm_address}: {result}")
            
            # Parse pool info according to the ABI
            pool_info = {
                "_mechanism": result[0],
                "_subnetTAO": result[1],
                "_subnetAlphaIn": result[2],
                "_subnetAlphaOut": result[3],
                "_currentPrice": result[4],
                "_movingPrice": result[5],
                "_totalVolume": result[6],
                "_minimumLiquidity": result[7]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed pool info: {pool_info}")
            
            return pool_info
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get pool info: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_swap_preview(self, pool_address: Optional[str] = None, netuid: Optional[int] = None, amount_in: int = 0, is_hetu_to_alpha: bool = True, block: Optional[int] = None) -> Optional[dict]:
        """
        Get preview of swap outcome.
        
        Args:
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            amount_in (int): Amount of input token.
            is_hetu_to_alpha (bool): True if swapping HETU for Alpha, False otherwise.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Swap preview information if successful, None otherwise.
        """
        try:
            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return None

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            # Get swap preview
            result = amm_contract.functions.getSwapPreview(amount_in, is_hetu_to_alpha).call()
            
            if self.log_verbose:
                logging.info(f"Raw swap preview for {amm_address}: {result}")
            
            # Parse preview info according to the ABI
            preview = {
                "amount_out": result[0],
                "price_impact": result[1],
                "new_price": result[2],
                "is_liquidity_sufficient": result[3]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed swap preview: {preview}")
            
            return preview
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get swap preview: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def swap_hetu_for_alpha(self, wallet: "Account", pool_address: Optional[str] = None, netuid: Optional[int] = None, hetu_amount_in: int = 0, alpha_amount_out_min: int = 0, **kwargs) -> bool:
        """
        Swap HETU tokens for Alpha tokens.
        
        Args:
            wallet (Account): The wallet to perform the swap from.
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            hetu_amount_in (int): Amount of HETU to swap.
            alpha_amount_out_min (int): Minimum amount of Alpha to receive.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if swap was successful, False otherwise.
        """
        try:
            if not wallet:
                if self.log_verbose:
                    logging.error("No wallet provided")
                return False

            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return False

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            if self.log_verbose:
                logging.info(f"Swapping {hetu_amount_in} HETU for minimum {alpha_amount_out_min} Alpha")
            
            # Get nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # Build transaction
            gas_limit = kwargs.get('gas_limit', 300000)
            tx = amm_contract.functions.swapHetuForAlpha(
                hetu_amount_in,
                alpha_amount_out_min
            ).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # Sign transaction
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Swap transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Swap successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Swap failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to swap HETU for Alpha: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def swap_alpha_for_hetu(self, wallet: "Account", pool_address: Optional[str] = None, netuid: Optional[int] = None, alpha_amount_in: int = 0, hetu_amount_out_min: int = 0, **kwargs) -> bool:
        """
        Swap Alpha tokens for HETU tokens.
        
        Args:
            wallet (Account): The wallet to perform the swap from.
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            alpha_amount_in (int): Amount of Alpha to swap.
            hetu_amount_out_min (int): Minimum amount of HETU to receive.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if swap was successful, False otherwise.
        """
        try:
            if not wallet:
                if self.log_verbose:
                    logging.error("No wallet provided")
                return False

            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return False

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            if self.log_verbose:
                logging.info(f"Swapping {alpha_amount_in} Alpha for minimum {hetu_amount_out_min} HETU")
            
            # Get nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # Build transaction
            gas_limit = kwargs.get('gas_limit', 300000)
            tx = amm_contract.functions.swapAlphaForHetu(
                alpha_amount_in,
                hetu_amount_out_min
            ).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # Sign transaction
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Swap transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Swap successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Swap failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to swap Alpha for HETU: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def inject_liquidity(self, wallet: "Account", pool_address: Optional[str] = None, netuid: Optional[int] = None, hetu_amount: int = 0, alpha_amount: int = 0, **kwargs) -> bool:
        """
        Inject liquidity into AMM pool.
        
        Args:
            wallet (Account): The wallet to inject liquidity from.
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            hetu_amount (int): Amount of HETU to inject.
            alpha_amount (int): Amount of Alpha to inject.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if injection was successful, False otherwise.
        """
        try:
            if not wallet:
                if self.log_verbose:
                    logging.error("No wallet provided")
                return False

            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return False

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            if self.log_verbose:
                logging.info(f"Injecting {hetu_amount} HETU and {alpha_amount} Alpha")
            
            # Get nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # Build transaction
            gas_limit = kwargs.get('gas_limit', 300000)
            tx = amm_contract.functions.injectLiquidity(
                hetu_amount,
                alpha_amount
            ).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # Sign transaction
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Inject liquidity transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Liquidity injection successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Liquidity injection failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to inject liquidity: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def withdraw_liquidity(self, wallet: "Account", pool_address: Optional[str] = None, netuid: Optional[int] = None, hetu_amount: int = 0, alpha_amount: int = 0, **kwargs) -> bool:
        """
        Withdraw liquidity from AMM pool.
        
        Args:
            wallet (Account): The wallet to withdraw liquidity to.
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            hetu_amount (int): Amount of HETU to withdraw.
            alpha_amount (int): Amount of Alpha to withdraw.
            **kwargs: Additional arguments.
            
        Returns:
            bool: True if withdrawal was successful, False otherwise.
        """
        try:
            if not wallet:
                if self.log_verbose:
                    logging.error("No wallet provided")
                return False

            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return False

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            if self.log_verbose:
                logging.info(f"Withdrawing {hetu_amount} HETU and {alpha_amount} Alpha")
            
            # Get nonce
            nonce = self.web3.eth.get_transaction_count(wallet.address)
            
            # Build transaction
            gas_limit = kwargs.get('gas_limit', 300000)
            tx = amm_contract.functions.withdrawLiquidity(
                hetu_amount,
                alpha_amount
            ).build_transaction({
                "from": wallet.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.web3.eth.gas_price,
            })
            
            # Sign transaction
            signed = self.web3.eth.account.sign_transaction(tx, wallet.key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
            
            if self.log_verbose:
                logging.info(f"Withdraw liquidity transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                if self.log_verbose:
                    logging.info(f"Liquidity withdrawal successful in block {receipt.blockNumber}")
                return True
            else:
                if self.log_verbose:
                    logging.error(f"Liquidity withdrawal failed in block {receipt.blockNumber}")
                return False
                
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to withdraw liquidity: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def get_pool_statistics(self, pool_address: Optional[str] = None, netuid: Optional[int] = None, block: Optional[int] = None) -> Optional[dict]:
        """
        Get pool statistics.
        
        Args:
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Pool statistics if successful, None otherwise.
        """
        try:
            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return None

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            # Get statistics using getStatistics instead of getPoolStatistics
            result = amm_contract.functions.getStatistics().call()
            
            if self.log_verbose:
                logging.info(f"Raw pool statistics for {amm_address}: {result}")
            
            # Parse statistics according to the ABI
            statistics = {
                "total_volume": result[0],
                "current_price": result[1],
                "moving_price": result[2],
                "price_update_block": result[3],
                "total_liquidity": result[4]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed pool statistics: {statistics}")
            
            return statistics
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get pool statistics: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def get_pool_health(self, pool_address: Optional[str] = None, netuid: Optional[int] = None, block: Optional[int] = None) -> Optional[dict]:
        """
        Get pool health metrics.
        
        Args:
            pool_address (Optional[str]): The AMM pool contract address.
            netuid (Optional[int]): The subnet ID.
            block (Optional[int]): The blockchain block number for the query.
            
        Returns:
            Optional[dict]: Pool health metrics if successful, None otherwise.
        """
        try:
            # Get AMM contract address
            amm_address = self.get_amm_contract_address(netuid, pool_address)
            if not amm_address:
                if self.log_verbose:
                    logging.error("Failed to get AMM contract address")
                return None

            # Create AMM contract instance
            amm_contract = self.web3.eth.contract(
                address=amm_address,
                abi=self.amm_factory.abi
            )
            
            # Get health metrics
            result = amm_contract.functions.getPoolHealth().call()
            
            if self.log_verbose:
                logging.info(f"Raw pool health for {amm_address}: {result}")
            
            # Parse health metrics according to the ABI
            health = {
                "is_healthy": result[0],
                "status": result[1],
                "liquidity_ratio": result[2]
            }
            
            if self.log_verbose:
                logging.info(f"Parsed pool health: {health}")
            
            return health
            
        except Exception as e:
            if self.log_verbose:
                logging.error(f"Failed to get pool health: {e}")
                import traceback
                logging.error(f"Full traceback: {traceback.format_exc()}")
            return None
