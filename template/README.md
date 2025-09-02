# Hetu Template Package

This template package provides pre-built Hetu miners and validators, demonstrating how to create and use Hetu network services.

## 🏗️ Architecture Overview

```
template/
├── __init__.py          # Package initialization file
├── protocol.py          # Protocol layer - Synapse class definitions
├── math_miner.py        # Math service miner template
├── math_validator.py    # Math service validator template
└── README.md            # This document
```

## 🔌 Protocol Layer

`protocol.py` defines the communication protocol between miners and validators:

### Available Synapse Classes

- **`MathSumSynapse`**: Addition service
  - Input parameters: `x`, `y` (float)
  - Result property: `sum_result` (x + y)

- **`MathProductSynapse`**: Multiplication service
  - Input parameters: `x`, `y` (float)
  - Result property: `product_result` (x × y)

### Protocol Layer Features

```python
from template.protocol import (
    create_synapse,
    get_available_services,
    SERVICE_TYPES
)

# Get available services list
services = get_available_services()  # ['addition', 'multiplication']

# Create Synapse instance
synapse = create_synapse("addition", x=5.0, y=3.0)
```

## ⛏️ Miner Template

`math_miner.py` provides a complete miner service template:

### Features

- Uses Synapse classes defined in the protocol layer
- Automatically attaches services to Xylem server
- Graceful error handling
- Detailed logging

### Usage

```python
from template import MathMiner
from hetu.utils.wallet import unlock_wallet

# Unlock wallet
wallet = unlock_wallet("your_wallet_name")

# Create miner
miner = MathMiner(
    wallet=wallet,
    netuid=1,
    network="mainnet",
    port=8091,
    ip="127.0.0.1"
)

# Start service
await miner.start()
```

### Configuration Options

- `wallet`: Pre-initialized wallet object
- `netuid`: Subnet ID
- `network`: Network name (mainnet, testnet, etc.)
- `port`: Service port
- `ip`: Binding IP address

## 🧪 Validator Template

`math_validator.py` provides a complete validator template:

### Features

- Automatically discovers miners from the network
- **Smart Validation**: Tests miner mathematical services and assigns weights based on results
- **Dynamic Weight Assignment**: 
  - Correct answers: 100 points
  - Incorrect answers: 30 points  
  - No response: 0 points
- Weight submission based on epoch time windows
- Configurable polling intervals and thresholds
- Duplicate submission protection

### Usage

```python
from template import MathValidator
from hetu.utils.wallet import unlock_wallet

# Unlock wallet
wallet = unlock_wallet("your_wallet_name")

# Create validator
validator = MathValidator(
    username="your_username",
    netuid=1,
    network="mainnet",
    wallet=wallet
)

# Run validator
await validator.run_continuous()
```

### Configuration Options

- `username`: Wallet username
- `netuid`: Subnet ID
- `network`: Network name
- `wallet`: Pre-initialized wallet object

### Weight Scoring System

The validator automatically verifies the service quality of each miner:

- **100 points**: All test cases return correct answers
- **30 points**: Some or all test cases return incorrect answers
- **0 points**: Miner unresponsive or service unavailable

The validation process includes:
- Addition service testing (4 test cases)
- Multiplication service testing (4 test cases)
- Automatic error handling and timeout management

## 🚀 Quick Start

### 1. Start Miner

```bash
cd template
python math_miner.py
```

### 2. Start Validator

```bash
cd template
python math_validator.py
```

### 3. Test Services

Use curl to test miner services:

```bash
# Test addition service
curl -X POST "http://127.0.0.1:8091/MathSumSynapse" \
     -H "Content-Type: application/json" \
     -d '{"x": 5.0, "y": 3.0}'

# Test multiplication service
curl -X POST "http://127.0.0.1:8091/MathProductSynapse" \
     -H "Content-Type: application/json" \
     -d '{"x": 4.0, "y": 6.0}'
```

## 🔧 Customization and Extension

### Adding New Service Types

1. Define new Synapse classes in `protocol.py`
2. Add new services to the `SERVICE_TYPES` dictionary
3. Implement service logic in the miner
4. Update validator to recognize new services

### Modifying Configuration

- Adjust polling interval: modify `DEFAULT_POLL_INTERVAL_SECONDS`
- Adjust epoch threshold: modify `DEFAULT_EPOCH_THRESHOLD_RATIO`
- Adjust weight scoring: modify `WEIGHT_SCORES` dictionary

## 📝 Important Notes

1. **Wallet Configuration**: Ensure wallet is properly configured before running
2. **Network Configuration**: Adjust netuid and network according to your needs
3. **Port Configuration**: Ensure ports are not occupied by other services
4. **Error Handling**: Templates include basic error handling, but you may need to adjust based on specific requirements

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve these templates!

## 📄 License

These templates follow the same license as the Hetu project.
