# Changelog

## [Unreleased]
- Initial release: hetu-pysdk Python SDK
- Support for EVM (web3.py) and Cosmos RPC interaction
- Axon (server) / Dendrite (client) / Synapse (message) communication framework
- Complete removal of Bittensor/Subtensor/substrate logic, fully replaced with hetu/ETH/EVM-compatible implementation
- ETH wallet/address support, signing and verification based on eth_account and encode_defunct (EIP-191)
- Full ETH-compatible Axon/Dendrite/Synapse communication, strict signature and verification
- Support for computed_body_hash to prevent replay and tampering
- chain_api/chain_data modules for EVM/Cosmos chain data structures and RPC
- Mock/test infrastructure with MagicMock and local/offline test support
- Robust exception handling and custom error types
- pytest test cases covering Axon/Dendrite/Synapse, EVM RPC, mock, and more
- All documentation and comments use hetu/ETH/EVM context
- Modern code structure with full type annotations
