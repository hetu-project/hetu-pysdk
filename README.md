# HetuSubnet PySDK

HetuSubnet PySDK is a Python client library for interacting with the Hetu EVM blockchain, supporting distributed computing, neuron management, and subnet operations.

## 🏗️ Architecture Overview

HetuSubnet adopts a layered architecture design with clear separation of responsibilities:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Mainnet        │    │  Subnet         │    │  Neuron         │
│                 │    │                 │    │                 │
│ • Global Staking│◄──►│ • Subnet Mgmt   │◄──►│ • Compute      │
│ • Token Economy │    │ • Param Config  │    │ • Validation   │
│ • Network Gov   │    │ • Liquidity Mgmt│    │ • State Sync   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Network Layer Responsibilities

- **Mainnet**: Core network managing global parameters, staking, and economic policies
- **Subnet (netuid ≥ 1)**: Specialized networks providing domain-specific services with their own governance
- **Neurons**: Active participants in subnets, divided into validators and miners

### Detailed Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAINNET                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Global Staking Contract    │  Subnet Manager    │  WHETU Token Contract   │
│  • Manage total stakes      │  • Create subnets  │  • Token economics     │
│  • Allocate to subnets      │  • Set parameters  │  • Reward distribution │
│  • Handle rewards           │  • Governance      │  • Staking mechanics   │
└─────────────────────────────┼─────────────────────┼─────────────────────────┘
                              │                     │
                              ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUBNET (netuid=1)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Neuron Manager Contract    │  AMM Factory       │  Subnet Parameters     │
│  • Register neurons         │  • Liquidity pools │  • Max validators      │
│  • Manage roles             │  • Token swaps     │  • Staking thresholds  │
│  • Track performance        │  • Price discovery │  • Reward rates        │
└─────────────────────────────┼─────────────────────┼─────────────────────────┘
                              │                     │
                              ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEURON LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  VALIDATORS                 │  MINERS                                      │
│  • Verify computations      │  • Execute tasks                            │
│  • Maintain consensus       │  • Provide services                         │
│  • Distribute rewards       │  • Report results                           │
│  • Network governance       │  • Earn rewards                             │
└─────────────────────────────┴───────────────────────────────────────────────┘
```

### Network Structure

```
                    MAINNET
                       │
                       │ Global Staking & Governance
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    SUBNET 1      SUBNET 2      SUBNET N
   (netuid=1)    (netuid=2)    (netuid=N)
        │              │              │
        │              │              │
    ┌───┴───┐      ┌───┴───┐      ┌───┴───┐
    │       │      │       │      │       │
 VALIDATORS │   VALIDATORS │   VALIDATORS │
    │       │      │       │      │       │
    │       │      │       │      │       │
   MINERS   │     MINERS   │     MINERS   │
```

## 🔗 Subnet and Mainnet Interaction

### 1. Network Hierarchy

- **Mainnet**: Core network managing global parameters and staking
- **Subnet (netuid ≥ 1)**: Dedicated networks providing specific services
- **Neurons**: Participants in subnets, divided into validators and miners

### 2. Interaction Flow

```
User → Mainnet Staking → Allocate to Subnet → Register Neuron → Provide Services
```

### 3. Network Topology

```
                    MAINNET
                       │
                       │ Global Staking & Governance
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    SUBNET 1      SUBNET 2      SUBNET N
   (netuid=1)    (netuid=2)    (netuid=N)
        │              │              │
        │              │              │
    ┌───┴───┐      ┌───┴───┐      ┌───┴───┐
    │       │      │       │      │       │
 VALIDATORS │   VALIDATORS │   VALIDATORS │
    │       │      │       │      │       │
    │       │      │       │      │       │
   MINERS   │     MINERS   │     MINERS   │
```

### 4. Key Differences from Traditional Networks

- **Direct Mainnet Control**: Mainnet directly manages all subnets
- **Independent Subnet Governance**: Each subnet has its own parameters and governance
- **Flexible Subnet Creation**: New subnets can be created for different use cases

### 3. Detailed Interaction Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAINNET                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Global Staking Contract    │  Subnet Manager    │  WHETU Token Contract   │
│  • Manage total stakes      │  • Create subnets  │  • Token economics     │
│  • Allocate to subnets      │  • Set parameters  │  • Reward distribution │
│  • Handle rewards           │  • Governance      │  • Staking mechanics   │
└─────────────────────────────┼─────────────────────┼─────────────────────────┘
                              │                     │
                              ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SUBNET (netuid=1)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Neuron Manager Contract    │  AMM Factory       │  Subnet Parameters     │
│  • Register neurons         │  • Liquidity pools │  • Max validators      │
│  • Manage roles             │  • Token swaps     │  • Staking thresholds  │
│  • Track performance        │  • Price discovery │  • Reward rates        │
└─────────────────────────────┼─────────────────────┼─────────────────────────┘
                              │                     │
                              ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEURON LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  VALIDATORS                 │  MINERS                                      │
│  • Verify computations      │  • Execute tasks                            │
│  • Maintain consensus       │  • Provide services                         │
│  • Distribute rewards       │  • Report results                           │
│  • Network governance       │  • Earn rewards                             │
└─────────────────────────────┴───────────────────────────────────────────────┘
```

## 🔄 Miner and Validator Collaboration

### 1. Role Definition and Responsibilities

#### Validators (Network Guardians)
- **Consensus Maintenance**: Ensure network integrity and quality
- **Task Distribution**: Route compute requests to appropriate miners
- **Result Verification**: Validate and aggregate miner responses
- **Reward Distribution**: Allocate rewards based on miner performance
- **Network Governance**: Participate in subnet parameter decisions

#### Miners (Service Providers)
- **Compute Execution**: Execute actual computational tasks
- **Service Availability**: Maintain high uptime and responsiveness
- **Performance Optimization**: Optimize compute efficiency
- **Result Reporting**: Return accurate and timely results
- **Stake Management**: Maintain sufficient stake for participation

### 2. Collaboration Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │ Validator   │    │    Miner    │    │   Result    │
│  Request    │───►│  Discovery  │───►│  Execution  │───►│ Validation  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       │            │  Load       │    │  Compute    │    │  Consensus  │
       │            │  Balance    │    │  Service    │    │  & Reward   │
       └───────────►│  & Route    │    │  Execution  │    │  Distribution│
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3. Detailed Collaboration Process

#### Phase 1: Request Processing
```python
# Client sends request to validator
async def client_request(validator_endpoint: str, task: str):
    synapse = Synapse(completion=task)
    
    # Validator receives and processes request
    response = await dendrite.query(
        axons=[validator_endpoint],
        synapse=synapse,
        timeout=30.0
    )
    return response
```

#### Phase 2: Validator Task Distribution
```python
async def validator_distribute_task(netuid: int, task: str):
    """Validator distributes task to multiple miners"""
    # 1. Discover available miners
    miners = hetu.get_subnet_miners(netuid)
    active_miners = []
    
    for miner_addr in miners:
        info = hetu.get_neuron_info(netuid, miner_addr)
        if info and info['is_active'] and info['stake'] > 0:
            active_miners.append({
                'address': miner_addr,
                'endpoint': info['axon_endpoint'],
                'port': info['axon_port'],
                'stake': info['stake'],
                'performance': info.get('last_update', 0)
            })
    
    # 2. Select miners based on stake and performance
    selected_miners = select_optimal_miners(active_miners, task_complexity=task)
    
    # 3. Distribute task to selected miners
    return await distribute_to_miners(selected_miners, task)
```

#### Phase 3: Miner Task Execution
```python
async def miner_execute_task(synapse: Synapse):
    """Miner executes the received task"""
    try:
        # Parse task from synapse
        task = synapse.completion
        
        # Execute computation
        if "add" in task:
            result = execute_addition(task)
        elif "multiply" in task:
            result = execute_multiplication(task)
        elif "ai_inference" in task:
            result = execute_ai_inference(task)
        else:
            result = "Unknown task type"
        
        # Update synapse with result
        synapse.completion = result
        synapse.process_time = time.time()
        
        return synapse
        
    except Exception as e:
        synapse.completion = f"Error: {str(e)}"
        synapse.status_code = 500
        return synapse
```

#### Phase 4: Result Aggregation and Validation
```python
async def validator_aggregate_results(miner_responses: list, expected_consensus: float = 0.67):
    """Validator aggregates and validates miner results"""
    # 1. Group results by response
    result_groups = {}
    for response in miner_responses:
        result = response.completion
        if result not in result_groups:
            result_groups[result] = []
        result_groups[result].append(response)
    
    # 2. Find consensus result
    total_responses = len(miner_responses)
    consensus_threshold = total_responses * expected_consensus
    
    for result, responses in result_groups.items():
        if len(responses) >= consensus_threshold:
            # Consensus reached
            return {
                'consensus_result': result,
                'consensus_count': len(responses),
                'total_responses': total_responses,
                'confidence': len(responses) / total_responses
            }
    
    # No consensus reached
    return {
        'consensus_result': None,
        'consensus_count': 0,
        'total_responses': total_responses,
        'confidence': 0.0
    }
```

### 4. Reward Distribution Mechanism

```python
async def distribute_rewards(netuid: int, consensus_result: dict, miner_responses: list):
    """Distribute rewards based on consensus and performance"""
    # 1. Calculate base rewards
    base_reward = get_subnet_reward_rate(netuid)
    
    # 2. Distribute to validators (consensus participants)
    validator_reward = base_reward * 0.3  # 30% to validators
    
    # 3. Distribute to miners (service providers)
    miner_reward = base_reward * 0.7  # 70% to miners
    
    # 4. Allocate miner rewards based on performance
    for response in miner_responses:
        if response.completion == consensus_result['consensus_result']:
            # Correct result - full reward
            reward_amount = miner_reward / len(miner_responses)
            await transfer_reward(response.miner_address, reward_amount)
        else:
            # Incorrect result - reduced reward or penalty
            penalty_amount = miner_reward / len(miner_responses) * 0.5
            await apply_penalty(response.miner_address, penalty_amount)
```

## 🌐 Mainnet Interaction Mechanisms

### 1. Staking and Economic Model

#### Global Staking Pool
```python
# Users stake WHETU tokens in mainnet
async def stake_in_mainnet(wallet, amount: int):
    """Stake tokens in mainnet global pool"""
    success = hetu.add_global_stake(
        wallet=wallet,
        amount=amount
    )
    
    if success:
        print(f"Successfully staked {amount} WHETU in mainnet")
        return True
    else:
        print("Failed to stake in mainnet")
        return False
```

#### Subnet Allocation
```python
# Allocate staked tokens to specific subnets
async def allocate_to_subnet(wallet, netuid: int, amount: int):
    """Allocate staked tokens to subnet"""
    success = hetu.allocate_to_subnet(
        wallet=wallet,
        netuid=netuid,
        amount=amount
    )
    
    if success:
        print(f"Successfully allocated {amount} WHETU to subnet {netuid}")
        return True
    else:
        print(f"Failed to allocate to subnet {netuid}")
        return False
```

### 2. Network Governance and Parameter Updates

#### Subnet Parameter Management
```python
async def update_subnet_parameters(netuid: int, new_params: dict):
    """Update subnet parameters through governance"""
    # Get current parameters
    current_params = hetu.get_subnet_params(netuid)
    
    # Validate parameter changes
    if validate_parameter_changes(current_params, new_params):
        # Submit parameter update transaction
        success = await submit_parameter_update(netuid, new_params)
        return success
    else:
        print("Invalid parameter changes")
        return False
```

#### Economic Policy Updates
```python
async def update_economic_policy(policy_type: str, new_value: int):
    """Update mainnet economic policies"""
    if policy_type == "reward_rate":
        success = await update_reward_rate(new_value)
    elif policy_type == "staking_threshold":
        success = await update_staking_threshold(new_value)
    elif policy_type == "penalty_multiplier":
        success = await update_penalty_multiplier(new_value)
    
    return success
```

### 3. Cross-Subnet Communication

#### Inter-Subnet Token Transfers
```python
async def transfer_between_subnets(
    from_netuid: int, 
    to_netuid: int, 
    amount: int,
    wallet
):
    """Transfer tokens between subnets"""
    # 1. Withdraw from source subnet
    withdraw_success = await withdraw_from_subnet(from_netuid, amount, wallet)
    
    if withdraw_success:
        # 2. Allocate to destination subnet
        allocate_success = await allocate_to_subnet(wallet, to_netuid, amount)
        return allocate_success
    else:
        return False
```

#### Cross-Subnet Service Discovery
```python
async def discover_cross_subnet_services(target_netuid: int, service_type: str):
    """Discover services across different subnets"""
    # Get subnet information
    subnet_info = hetu.get_subnet_info(target_netuid)
    
    if subnet_info and subnet_info.is_active:
        # Query available services
        services = await query_subnet_services(target_netuid, service_type)
        return services
    else:
        print(f"Subnet {target_netuid} is not active")
        return []
```

### 4. State Synchronization

#### Blockchain State Updates
```python
async def sync_subnet_state(netuid: int):
    """Synchronize subnet state with mainnet"""
    # Get latest block number
    latest_block = hetu.get_current_block()
    
    # Get subnet state at latest block
    subnet_state = hetu.get_subnet_info(netuid, block=latest_block)
    
    # Update local state
    await update_local_subnet_state(netuid, subnet_state)
    
    return subnet_state
```

#### Neuron Status Synchronization
```python
async def sync_neuron_status(netuid: int, neuron_address: str):
    """Synchronize individual neuron status"""
    # Get neuron info from blockchain
    neuron_info = hetu.get_neuron_info(netuid, neuron_address)
    
    # Update local neuron status
    await update_local_neuron_status(netuid, neuron_address, neuron_info)
    
    return neuron_info
```

## 📚 Core Components

### HetuSubnet Client
```python
from hetu.hetu import HetuSubnet

# Initialize client
hetu = HetuSubnet(
    network="local",  # or "mainnet", "testnet"
    log_verbose=True
)

# Set wallet
hetu.set_wallet_from_username("username", "password")
```

### Axon (Compute Service Provider)
```python
from hetu.axon import Axon

# Create compute service
axon = Axon(
    ip="127.0.0.1",
    port=8091,
    external_ip="your.public.ip",
    external_port=8091
)

# Define compute function
async def compute_service(synapse):
    """Handle compute requests"""
    if "add" in synapse.completion:
        # Parse "add 10 20" format
        parts = synapse.completion.split()
        if len(parts) == 3 and parts[0] == "add":
            a, b = int(parts[1]), int(parts[2])
            result = a + b
            synapse.completion = f"Result: {a} + {b} = {result}"
            return synapse
    
    synapse.completion = "Unknown operation"
    return synapse

# Attach service and start
axon.attach(compute_service)
axon.start()
```

### Dendrite (Validator/Client)
```python
from hetu.dendrite import Dendrite
from hetu.synapse import Synapse

# Create validator client
dendrite = Dendrite(
    username="validator_username",
    password="validator_password"
)

# Query subnet information
async def query_subnet():
    # Get subnet list
    subnets = hetu.get_subnets()
    print(f"Available subnets: {subnets}")
    
    # Get specific subnet info
    netuid = 1
    subnet_info = hetu.get_subnet_info(netuid)
    print(f"Subnet {netuid} info: {subnet_info}")
    
    # Get neuron lists
    neurons = hetu.get_subnet_neurons(netuid)
    validators = hetu.get_subnet_validators(netuid)
    miners = hetu.get_subnet_miners(netuid)
    
    print(f"Total neurons: {len(neurons)}")
    print(f"Validators: {len(validators)}")
    print(f"Miners: {len(miners)}")
```

## 🌐 Subnet Operations

### 1. Create Subnet
```python
# Register new subnet
success = hetu.register_subnet(
    wallet=wallet,
    name="AI Compute Network",
    description="Distributed AI computation services",
    token_name="AI Token",
    token_symbol="AIT"
)

if success:
    print("Subnet created successfully!")
else:
    print("Subnet creation failed")
```

### 2. Activate Subnet
```python
# Activate subnet
success = hetu.activate_subnet(
    wallet=wallet,
    netuid=1
)

if success:
    print("Subnet activated successfully!")
else:
    print("Subnet activation failed")
```

### 3. Register Neuron
```python
# Register as miner
success = hetu.register_neuron(
    netuid=1,
    is_validator_role=False,  # False = miner, True = validator
    axon_endpoint="your.public.ip",
    axon_port=8091,
    prometheus_endpoint="",
    prometheus_port=0
)

if success:
    print("Neuron registered successfully!")
else:
    print("Neuron registration failed")
```

### 4. Staking Management
```python
# Global staking
success = hetu.add_global_stake(
    wallet=wallet,
    amount=1000000000000000000  # 1 ETH (wei)
)

# Allocate to subnet
success = hetu.allocate_to_subnet(
    wallet=wallet,
    netuid=1,
    amount=500000000000000000  # 0.5 ETH
)
```

## 🔄 Distributed Computing Flow

### 1. Service Discovery
async def discover_miners(netuid: int):
    """Discover miners in subnet"""
    # Get all miner addresses
    miners = hetu.get_subnet_miners(netuid)
    
    # Get miner details
    miner_info = []
    for miner_addr in miners:
        info = hetu.get_neuron_info(netuid, miner_addr)
        if info and info['is_active']:
            miner_info.append({
                'address': miner_addr,
                'endpoint': info['axon_endpoint'],
                'port': info['axon_port'],
                'stake': info['stake']
            })
    
    return miner_info

### 2. Task Distribution
async def distribute_computation(netuid: int, task: str):
    """Distribute compute tasks to miners"""
    # Discover miners
    miners = await discover_miners(netuid)
    
    # Create Dendrite client
    async with Dendrite() as dendrite:
        # Parallel queries to all miners
        synapses = [Synapse(completion=task) for _ in miners]
        
        # Send requests
        responses = await dendrite.query(
            axons=miners,
            synapse=synapses[0],
            timeout=30.0
        )
        
        return responses

### 3. Result Validation
async def validate_results(responses, expected_result):
    """Validate compute results"""
    valid_results = []
    
    for response in responses:
        if hasattr(response, 'completion'):
            # Check if results are consistent
            if response.completion == expected_result:
                valid_results.append(response)
    
    # If more than 2/3 results are consistent, consider valid
    return len(valid_results) >= len(responses) * 2 / 3

## 🤝 Miner and Validator Collaboration

### 1. Role Definition and Responsibilities

#### Validators (Network Guardians)
- **Consensus Maintenance**: Ensure network integrity and quality
- **Task Distribution**: Route compute requests to appropriate miners
- **Result Verification**: Validate and aggregate miner responses
- **Reward Distribution**: Allocate rewards based on miner performance
- **Network Governance**: Participate in subnet parameter decisions

#### Miners (Service Providers)
- **Compute Execution**: Execute actual computational tasks
- **Service Availability**: Maintain high uptime and responsiveness
- **Performance Optimization**: Optimize compute efficiency
- **Result Reporting**: Return accurate and timely results
- **Stake Management**: Maintain sufficient stake for participation

### 2. Collaboration Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │ Validator   │    │    Miner    │    │   Result    │
│  Request    │───►│  Discovery  │───►│  Execution  │───►│ Validation  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   ▼                   ▼
       │            ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
       │            │  Load       │    │  Compute    │    │  Consensus  │
       │            │  Balance    │    │  Service    │    │  & Reward   │
       └───────────►│  & Route    │    │  Execution  │    │  Distribution│
                    └─────────────┘    └─────────────┘    └─────────────┘
```

### 3. Detailed Collaboration Process

#### Phase 1: Request Processing
```python
# Client sends request to validator
async def client_request(validator_endpoint: str, task: str):
    synapse = Synapse(completion=task)
    
    # Validator receives and processes request
    response = await dendrite.query(
        axons=[validator_endpoint],
        synapse=synapse,
        timeout=30.0
    )
    return response
```

#### Phase 2: Validator Task Distribution
```python
async def validator_distribute_task(netuid: int, task: str):
    """Validator distributes task to multiple miners"""
    # 1. Discover available miners
    miners = hetu.get_subnet_miners(netuid)
    active_miners = []
    
    for miner_addr in miners:
        info = hetu.get_neuron_info(netuid, miner_addr)
        if info and info['is_active'] and info['stake'] > 0:
            active_miners.append({
                'address': miner_addr,
                'endpoint': info['axon_endpoint'],
                'port': info['axon_port'],
                'stake': info['stake'],
                'performance': info.get('last_update', 0)
            })
    
    # 2. Select miners based on stake and performance
    selected_miners = select_optimal_miners(active_miners, task_complexity=task)
    
    # 3. Distribute task to selected miners
    return await distribute_to_miners(selected_miners, task)
```

#### Phase 3: Miner Task Execution
```python
async def miner_execute_task(synapse: Synapse):
    """Miner executes the received task"""
    try:
        # Parse task from synapse
        task = synapse.completion
        
        # Execute computation
        if "add" in task:
            result = execute_addition(task)
        elif "multiply" in task:
            result = execute_multiplication(task)
        elif "ai_inference" in task:
            result = execute_ai_inference(task)
        else:
            result = "Unknown task type"
        
        # Update synapse with result
        synapse.completion = result
        synapse.process_time = time.time()
        
        return synapse
        
    except Exception as e:
        synapse.completion = f"Error: {str(e)}"
        synapse.status_code = 500
        return synapse
```

#### Phase 4: Result Aggregation and Validation
```python
async def validator_aggregate_results(miner_responses: list, expected_consensus: float = 0.67):
    """Validator aggregates and validates miner results"""
    # 1. Group results by response
    result_groups = {}
    for response in miner_responses:
        result = response.completion
        if result not in result_groups:
            result_groups[result] = []
        result_groups[result].append(response)
    
    # 2. Find consensus result
    total_responses = len(miner_responses)
    consensus_threshold = total_responses * expected_consensus
    
    for result, responses in result_groups.items():
        if len(responses) >= consensus_threshold:
            # Consensus reached
            return {
                'consensus_result': result,
                'consensus_count': len(responses),
                'total_responses': total_responses,
                'confidence': len(responses) / total_responses
            }
    
    # No consensus reached
    return {
        'consensus_result': None,
        'consensus_count': 0,
        'total_responses': total_responses,
        'confidence': 0.0
    }
```

### 4. Reward Distribution Mechanism

```python
async def distribute_rewards(netuid: int, consensus_result: dict, miner_responses: list):
    """Distribute rewards based on consensus and performance"""
    # 1. Calculate base rewards
    base_reward = get_subnet_reward_rate(netuid)
    
    # 2. Distribute to validators (consensus participants)
    validator_reward = base_reward * 0.3  # 30% to validators
    
    # 3. Distribute to miners (service providers)
    miner_reward = base_reward * 0.7  # 70% to miners
    
    # 4. Allocate miner rewards based on performance
    for response in miner_responses:
        if response.completion == consensus_result['consensus_result']:
            # Correct result - full reward
            reward_amount = miner_reward / len(miner_responses)
            await transfer_reward(response.miner_address, reward_amount)
        else:
            # Incorrect result - reduced reward or penalty
            penalty_amount = miner_reward / len(miner_responses) * 0.5
            await apply_penalty(response.miner_address, penalty_amount)
```

## 🧪 Complete Test Examples

### Local Testing
```python
# test_local_computation.py
import asyncio
from hetu.hetu import HetuSubnet
from hetu.axon import Axon
from hetu.dendrite import Dendrite
from hetu.synapse import Synapse

async def test_local_computation():
    # 1. Start compute service (Axon)
    axon = Axon(ip="127.0.0.1", port=8091)
    
    async def compute_service(synapse):
        """Simple compute service"""
        if "add" in synapse.completion:
            parts = synapse.completion.split()
            if len(parts) == 3 and parts[0] == "add":
                a, b = int(parts[1]), int(parts[2])
                result = a + b
                synapse.completion = f"Result: {a} + {b} = {result}"
                return synapse
        return synapse
    
    axon.attach(compute_service)
    axon.start()
    
    # 2. Wait for service startup
    await asyncio.sleep(2)
    
    # 3. Create client (Dendrite)
    async with Dendrite() as dendrite:
        # 4. Send compute request
        synapse = Synapse(completion="add 15 25")
        
        # 5. Query service
        response = await dendrite.query(
            axons=[axon],
            synapse=synapse,
            timeout=10.0
        )
        
        print(f"Compute result: {response.completion}")
    
    # 6. Cleanup
    axon.stop()

if __name__ == "__main__":
    asyncio.run(test_local_computation())
```

### Network Testing
```python
# test_network_computation.py
import asyncio
from hetu.hetu import HetuSubnet

async def test_network_computation():
    # 1. Initialize HetuSubnet client
    hetu = HetuSubnet(
        network="mainnet",  # or "testnet"
        log_verbose=True
    )
    
    # 2. Set wallet
    hetu.set_wallet_from_username("username", "password")
    
    # 3. Query subnet info
    netuid = 1
    subnet_info = hetu.get_subnet_info(netuid)
    print(f"Subnet info: {subnet_info}")
    
    # 4. Discover miners
    miners = hetu.get_subnet_miners(netuid)
    print(f"Discovered miners: {miners}")
    
    # 5. Distribute compute tasks
    # ... implement task distribution logic

if __name__ == "__main__":
    asyncio.run(test_network_computation())
```

## 📊 Monitoring and Management

### 1. Subnet Health Monitoring
```python
def monitor_subnet_health(netuid: int):
    """Monitor subnet health status"""
    # Get subnet parameters
    params = hetu.get_subnet_params(netuid)
    print(f"Subnet parameters: {params}")
    
    # Get neuron statistics
    total_neurons = hetu.get_subnet_neuron_count(netuid)
    total_validators = hetu.get_subnet_validator_count(netuid)
    total_miners = hetu.get_subnet_miner_count(netuid)
    
    print(f"Neuron statistics:")
    print(f"  Total: {total_neurons}")
    print(f"  Validators: {total_validators}")
    print(f"  Miners: {total_miners}")
```

### 2. Staking Status Query
```python
def check_stake_status(user_address: str):
    """Check user staking status"""
    # Global staking info
    stake_info = hetu.get_stake_info(user_address)
    print(f"Global staking: {stake_info}")
    
    # Subnet allocation info
    subnets = hetu.get_subnets()
    for netuid in subnets:
        allocation = hetu.get_subnet_allocation(user_address, netuid)
        if allocation:
            print(f"Subnet {netuid} allocation: {allocation}")
```

## 🚀 Deployment Recommendations

### 1. Production Environment Configuration
```python
# Production environment config
axon = Axon(
    ip="0.0.0.0",  # Listen on all interfaces
    port=8091,
    external_ip="your.public.ip",
    external_port=8091,
    max_workers=50,  # Increase worker threads
    trace=True  # Enable detailed logging
)
```

### 2. Load Balancing
```python
# Use multiple Axon instances
axons = []
for i in range(3):
    axon = Axon(
        ip="127.0.0.1",
        port=8091 + i,
        external_ip="your.public.ip",
        external_port=8091 + i
    )
    axon.attach(compute_service)
    axon.start()
    axons.append(axon)
```

### 3. Error Handling and Retry
```python
async def robust_query(dendrite, axons, synapse, max_retries=3):
    """Query with retry mechanism"""
    for attempt in range(max_retries):
        try:
            response = await dendrite.query(
                axons=axons,
                synapse=synapse,
                timeout=30.0
            )
            return response
        except Exception as e:
            print(f"Query failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)
```

## 📝 Summary

HetuSubnet PySDK provides complete distributed computing infrastructure:

1. **Subnet Management**: Create, configure, and activate dedicated networks
2. **Neuron Management**: Register, stake, and synchronize state
3. **Distributed Computing**: Axon provides services, Dendrite consumes services
4. **Network Discovery**: Automatically discover available services via metagraph
5. **Staking Economy**: Global staking and subnet allocation mechanisms

This architecture supports building decentralized computing networks where:
- Mainnet handles global governance and economic models
- Subnets provide domain-specific services
- Neurons execute actual compute tasks
- Validators ensure network quality and security

Through this design, HetuSubnet achieves true decentralized distributed computing while maintaining the balance of economic incentives and network governance.