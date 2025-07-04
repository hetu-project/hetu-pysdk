# hetu-pysdk

A Python SDK for interacting with the hetu blockchain (Cosmos SDK + EVM), wrapping EVM contract and Cosmos RPC client features. Provides Axon/Dendrite/Synapse communication, EVM JSON-RPC, and ETH-compatible signing/verification.

## Features
- EVM contract interaction via web3.py
- Cosmos RPC client support
- Axon (server) and Dendrite (client) neuron communication
- Synapse: extensible message/data structure for requests
- ETH/EVM-compatible signing and signature verification
- Full support for ETH wallet/address
- Mock/test infrastructure for all core modules
- Custom exceptions and error handling
- Modern, extensible, and type-annotated codebase

## Project Structure

- `hetu/`         — Core SDK modules (axon, dendrite, synapse, chain_api, etc.)
- `chain_api/`    — EVM/Cosmos chain RPC and wallet logic
- `chain_data/`   — Data structures for chain state, neurons, axons, etc.
- `utils/`        — Utilities, logging, networking, versioning, mocks
- `tests/`        — Pytest test cases for all major features
- `contrib/`      — Contributing guidelines, changelog, etc.
- `README.md`    — Project overview and installation instructions


## Installation

### Install from [PyPI](https://pypi.org/project/hetu-pysdk/)

Run

```bash
pip install -U hetu-pysdk
```

### Install from source

1. Clone the Hetu SDK repo.

```bash
git clone https://github.com/hetu-project/hetu-pysdk.git
```

2. `cd` into `hetu-pysdk` directory.

```bash
cd hetu-pysdk
```

3. Create and activate a virtual environment.

```bash
make init-venv
```

4. Install dependencies and the CLI:

To install the SDK, you can use Poetry, which manages dependencies and virtual environments.
Make sure you have Poetry installed, then run:

```bash
pip install -U pip setuptools poetry wheel
poetry install
```

## Usage
### Basic EVM/Cosmos Client

```python
from hetu_pysdk import HetuClient

client = HetuClient(rpc_url="http://localhost:26657", evm_rpc_url="http://localhost:8545")
block_number = client.eth_blockNumber()
balance = client.eth_getBalance(address, "latest")
```

### Axon/Dendrite/Synapse Example
```python
import hetu_pysdk as ht

class EchoSynapse(ht.Synapse):
    input: str
    output: str = None

def echo_forward(syn: EchoSynapse) -> EchoSynapse:
    syn.output = syn.input
    return syn

def verify_echo(syn: EchoSynapse):
    assert isinstance(syn.input, str)

# Create ETH wallet/account
dendrite_wallet = ht.Account.create()
axon_wallet = ht.Account.create()

# Start Axon server
axon = ht.Axon(account=axon_wallet, port=8091)
axon.attach(forward_fn=echo_forward, verify_fn=verify_echo)
axon.serve(netuid=1).start()

# Dendrite client sends request
syn = EchoSynapse(input="hello")
dendrite = ht.Dendrite(account=dendrite_wallet)
response = dendrite.call(ht.AxonInfo(ip="127.0.0.1", port=8091, hotkey=axon_wallet.address), syn)
print(response.output)  # 'hello'
```

### ETH-Compatible Signing & Verification

- All requests are signed using eth_account and encode_defunct (EIP-191).
- Axon verifies signatures using Account.recover_message, matching claimed address.
- Nonce and computed_body_hash included in signature to prevent replay/tampering.

### Testing

```bash
poetry run pytest
```

- All core modules and communication patterns are covered by tests in `tests/`.
- Includes Axon/Dendrite/Synapse integration, EVM RPC, and mock logic.

### Mock/Offline Support

- Mock classes and MagicMock are used for offline/test scenarios.
- See `hetu/utils/mock/hetutensor_mock.py` for mock neuron/chain data.

## License

MIT
