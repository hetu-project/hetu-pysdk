from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hetu.chain_api import HetutensorApi


def add_legacy_methods(hetutensor: "HetutensorApi"):
    """If HetutensorApi get `hetutensor_fields=True` arguments, then all classic Hetutensor fields added to root level."""
    hetutensor.add_stake = hetutensor._hetutensor.add_stake
    hetutensor.add_stake_multiple = hetutensor._hetutensor.add_stake_multiple
    hetutensor.all_subnets = hetutensor._hetutensor.all_subnets
    hetutensor.blocks_since_last_step = hetutensor._hetutensor.blocks_since_last_step
    hetutensor.blocks_since_last_update = (
        hetutensor._hetutensor.blocks_since_last_update
    )
    hetutensor.bonds = hetutensor._hetutensor.bonds
    hetutensor.burned_register = hetutensor._hetutensor.burned_register
    hetutensor.chain_endpoint = hetutensor._hetutensor.chain_endpoint
    hetutensor.commit = hetutensor._hetutensor.commit
    hetutensor.commit_reveal_enabled = hetutensor._hetutensor.commit_reveal_enabled
    hetutensor.commit_weights = hetutensor._hetutensor.commit_weights
    hetutensor.determine_block_hash = hetutensor._hetutensor.determine_block_hash
    hetutensor.difficulty = hetutensor._hetutensor.difficulty
    hetutensor.does_hotkey_exist = hetutensor._hetutensor.does_hotkey_exist
    hetutensor.encode_params = hetutensor._hetutensor.encode_params
    hetutensor.filter_netuids_by_registered_hotkeys = (
        hetutensor._hetutensor.filter_netuids_by_registered_hotkeys
    )
    hetutensor.get_all_commitments = hetutensor._hetutensor.get_all_commitments
    hetutensor.get_all_metagraphs_info = hetutensor._hetutensor.get_all_metagraphs_info
    hetutensor.get_all_neuron_certificates = (
        hetutensor._hetutensor.get_all_neuron_certificates
    )
    hetutensor.get_all_revealed_commitments = (
        hetutensor._hetutensor.get_all_revealed_commitments
    )
    hetutensor.get_all_subnets_info = hetutensor._hetutensor.get_all_subnets_info
    hetutensor.get_balance = hetutensor._hetutensor.get_balance
    hetutensor.get_balances = hetutensor._hetutensor.get_balances
    hetutensor.get_block_hash = hetutensor._hetutensor.get_block_hash
    hetutensor.get_children = hetutensor._hetutensor.get_children
    hetutensor.get_children_pending = hetutensor._hetutensor.get_children_pending
    hetutensor.get_commitment = hetutensor._hetutensor.get_commitment
    hetutensor.get_current_block = hetutensor._hetutensor.get_current_block
    hetutensor.get_current_weight_commit_info = (
        hetutensor._hetutensor.get_current_weight_commit_info
    )
    hetutensor.get_delegate_by_hotkey = hetutensor._hetutensor.get_delegate_by_hotkey
    hetutensor.get_delegate_identities = hetutensor._hetutensor.get_delegate_identities
    hetutensor.get_delegate_take = hetutensor._hetutensor.get_delegate_take
    hetutensor.get_delegated = hetutensor._hetutensor.get_delegated
    hetutensor.get_delegates = hetutensor._hetutensor.get_delegates
    hetutensor.get_existential_deposit = hetutensor._hetutensor.get_existential_deposit
    hetutensor.get_hotkey_owner = hetutensor._hetutensor.get_hotkey_owner
    hetutensor.get_hotkey_stake = hetutensor._hetutensor.get_hotkey_stake
    hetutensor.get_hyperparameter = hetutensor._hetutensor.get_hyperparameter
    hetutensor.get_metagraph_info = hetutensor._hetutensor.get_metagraph_info
    hetutensor.get_minimum_required_stake = (
        hetutensor._hetutensor.get_minimum_required_stake
    )
    hetutensor.get_netuids_for_hotkey = hetutensor._hetutensor.get_netuids_for_hotkey
    hetutensor.get_neuron_certificate = hetutensor._hetutensor.get_neuron_certificate
    hetutensor.get_neuron_for_pubkey_and_subnet = (
        hetutensor._hetutensor.get_neuron_for_pubkey_and_subnet
    )
    hetutensor.get_next_epoch_start_block = (
        hetutensor._hetutensor.get_next_epoch_start_block
    )
    hetutensor.get_owned_hotkeys = hetutensor._hetutensor.get_owned_hotkeys
    hetutensor.get_revealed_commitment = hetutensor._hetutensor.get_revealed_commitment
    hetutensor.get_revealed_commitment_by_hotkey = (
        hetutensor._hetutensor.get_revealed_commitment_by_hotkey
    )
    hetutensor.get_stake = hetutensor._hetutensor.get_stake
    hetutensor.get_stake_add_fee = hetutensor._hetutensor.get_stake_add_fee
    hetutensor.get_stake_for_coldkey = hetutensor._hetutensor.get_stake_for_coldkey
    hetutensor.get_stake_for_coldkey_and_hotkey = (
        hetutensor._hetutensor.get_stake_for_coldkey_and_hotkey
    )
    hetutensor.get_stake_for_hotkey = hetutensor._hetutensor.get_stake_for_hotkey
    hetutensor.get_stake_info_for_coldkey = (
        hetutensor._hetutensor.get_stake_info_for_coldkey
    )
    hetutensor.get_stake_movement_fee = hetutensor._hetutensor.get_stake_movement_fee
    hetutensor.get_subnet_burn_cost = hetutensor._hetutensor.get_subnet_burn_cost
    hetutensor.get_subnet_hyperparameters = (
        hetutensor._hetutensor.get_subnet_hyperparameters
    )
    hetutensor.get_subnet_info = hetutensor._hetutensor.get_subnet_info
    hetutensor.get_subnet_owner_hotkey = hetutensor._hetutensor.get_subnet_owner_hotkey
    hetutensor.get_subnet_reveal_period_epochs = (
        hetutensor._hetutensor.get_subnet_reveal_period_epochs
    )
    hetutensor.get_subnet_validator_permits = (
        hetutensor._hetutensor.get_subnet_validator_permits
    )
    hetutensor.get_subnets = hetutensor._hetutensor.get_subnets
    hetutensor.get_timestamp = hetutensor._hetutensor.get_timestamp
    hetutensor.get_total_subnets = hetutensor._hetutensor.get_total_subnets
    hetutensor.get_transfer_fee = hetutensor._hetutensor.get_transfer_fee
    hetutensor.get_uid_for_hotkey_on_subnet = (
        hetutensor._hetutensor.get_uid_for_hotkey_on_subnet
    )
    hetutensor.get_unstake_fee = hetutensor._hetutensor.get_unstake_fee
    hetutensor.get_vote_data = hetutensor._hetutensor.get_vote_data
    hetutensor.immunity_period = hetutensor._hetutensor.immunity_period
    hetutensor.is_fast_blocks = hetutensor._hetutensor.is_fast_blocks
    hetutensor.is_hotkey_delegate = hetutensor._hetutensor.is_hotkey_delegate
    hetutensor.is_hotkey_registered = hetutensor._hetutensor.is_hotkey_registered
    hetutensor.is_hotkey_registered_any = (
        hetutensor._hetutensor.is_hotkey_registered_any
    )
    hetutensor.is_hotkey_registered_on_subnet = (
        hetutensor._hetutensor.is_hotkey_registered_on_subnet
    )
    hetutensor.is_subnet_active = hetutensor._hetutensor.is_subnet_active
    hetutensor.last_drand_round = hetutensor._hetutensor.last_drand_round
    hetutensor.log_verbose = hetutensor._hetutensor.log_verbose
    hetutensor.max_weight_limit = hetutensor._hetutensor.max_weight_limit
    hetutensor.metagraph = hetutensor._hetutensor.metagraph
    hetutensor.min_allowed_weights = hetutensor._hetutensor.min_allowed_weights
    hetutensor.move_stake = hetutensor._hetutensor.move_stake
    hetutensor.network = hetutensor._hetutensor.network
    hetutensor.neurons = hetutensor._hetutensor.neurons
    hetutensor.neuron_for_uid = hetutensor._hetutensor.neuron_for_uid
    hetutensor.neurons_lite = hetutensor._hetutensor.neurons_lite
    hetutensor.query_constant = hetutensor._hetutensor.query_constant
    hetutensor.query_identity = hetutensor._hetutensor.query_identity
    hetutensor.query_map = hetutensor._hetutensor.query_map
    hetutensor.query_map_hetutensor = hetutensor._hetutensor.query_map_hetutensor
    hetutensor.query_module = hetutensor._hetutensor.query_module
    hetutensor.query_runtime_api = hetutensor._hetutensor.query_runtime_api
    hetutensor.query_hetutensor = hetutensor._hetutensor.query_hetutensor
    hetutensor.recycle = hetutensor._hetutensor.recycle
    hetutensor.register = hetutensor._hetutensor.register
    hetutensor.register_subnet = hetutensor._hetutensor.register_subnet
    hetutensor.reveal_weights = hetutensor._hetutensor.reveal_weights
    hetutensor.root_register = hetutensor._hetutensor.root_register
    hetutensor.root_set_weights = hetutensor._hetutensor.root_set_weights
    hetutensor.serve_axon = hetutensor._hetutensor.serve_axon
    hetutensor.set_children = hetutensor._hetutensor.set_children
    hetutensor.set_commitment = hetutensor._hetutensor.set_commitment
    hetutensor.set_delegate_take = hetutensor._hetutensor.set_delegate_take
    hetutensor.set_reveal_commitment = hetutensor._hetutensor.set_reveal_commitment
    hetutensor.set_subnet_identity = hetutensor._hetutensor.set_subnet_identity
    hetutensor.set_weights = hetutensor._hetutensor.set_weights
    hetutensor.setup_config = hetutensor._hetutensor.setup_config
    hetutensor.sign_and_send_extrinsic = hetutensor._hetutensor.sign_and_send_extrinsic
    hetutensor.start_call = hetutensor._hetutensor.start_call
    hetutensor.state_call = hetutensor._hetutensor.state_call
    hetutensor.subnet = hetutensor._hetutensor.subnet
    hetutensor.subnet_exists = hetutensor._hetutensor.subnet_exists
    hetutensor.subnetwork_n = hetutensor._hetutensor.subnetwork_n
    hetutensor.substrate = hetutensor._hetutensor.substrate
    hetutensor.swap_stake = hetutensor._hetutensor.swap_stake
    hetutensor.tempo = hetutensor._hetutensor.tempo
    hetutensor.transfer = hetutensor._hetutensor.transfer
    hetutensor.transfer_stake = hetutensor._hetutensor.transfer_stake
    hetutensor.tx_rate_limit = hetutensor._hetutensor.tx_rate_limit
    hetutensor.unstake = hetutensor._hetutensor.unstake
    hetutensor.unstake_multiple = hetutensor._hetutensor.unstake_multiple
    hetutensor.wait_for_block = hetutensor._hetutensor.wait_for_block
    hetutensor.weights = hetutensor._hetutensor.weights
    hetutensor.weights_rate_limit = hetutensor._hetutensor.weights_rate_limit
