"""
client.py

Defines HetuClient for interacting with the hetu blockchain (cosmos-sdk + EVM).
- EVM contract interaction via web3.py
- Cosmos RPC client via requests/grpc
"""

from web3 import Web3
import requests

class HetuClient:
    """
    HetuClient provides methods to interact with the hetu blockchain, including EVM and Cosmos RPC features.
    """

    def __init__(self, rpc_url: str, evm_rpc_url: str):
        """
        Initialize the HetuClient.
        :param rpc_url: Cosmos RPC endpoint URL
        :param evm_rpc_url: EVM-compatible RPC endpoint URL
        """
        self.rpc_url = rpc_url
        self.evm_rpc_url = evm_rpc_url
        self.web3 = Web3(Web3.HTTPProvider(evm_rpc_url))

    def get_cosmos_status(self):
        """
        Get status from the Cosmos RPC endpoint.
        :return: JSON response from /status endpoint
        """
        resp = requests.get(f"{self.rpc_url}/status")
        resp.raise_for_status()
        return resp.json()

    def get_evm_block_number(self):
        """
        Get the latest block number from the EVM endpoint.
        :return: Latest block number
        """
        return self.web3.eth.block_number
