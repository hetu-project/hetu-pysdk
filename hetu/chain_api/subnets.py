from typing import Union

from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor
from hetu.hetu import Hetutensor as _Hetutensor


class Subnets:
    """Class for managing subnet operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.all_subnets = hetutensor.all_subnets
        self.blocks_since_last_step = hetutensor.blocks_since_last_step
        self.blocks_since_last_update = hetutensor.blocks_since_last_update
        self.bonds = hetutensor.bonds
        self.difficulty = hetutensor.difficulty
        self.get_all_subnets_info = hetutensor.get_all_subnets_info
        self.get_children = hetutensor.get_children
        self.get_children_pending = hetutensor.get_children_pending
        self.get_current_weight_commit_info = hetutensor.get_current_weight_commit_info
        self.get_hyperparameter = hetutensor.get_hyperparameter
        self.get_neuron_for_pubkey_and_subnet = (
            hetutensor.get_neuron_for_pubkey_and_subnet
        )
        self.get_next_epoch_start_block = hetutensor.get_next_epoch_start_block
        self.get_subnet_burn_cost = hetutensor.get_subnet_burn_cost
        self.get_subnet_hyperparameters = hetutensor.get_subnet_hyperparameters
        self.get_subnet_info = hetutensor.get_subnet_info
        self.get_subnet_owner_hotkey = hetutensor.get_subnet_owner_hotkey
        self.get_subnet_reveal_period_epochs = (
            hetutensor.get_subnet_reveal_period_epochs
        )
        self.get_subnet_validator_permits = hetutensor.get_subnet_validator_permits
        self.get_subnets = hetutensor.get_subnets
        self.get_total_subnets = hetutensor.get_total_subnets
        self.get_uid_for_hotkey_on_subnet = hetutensor.get_uid_for_hotkey_on_subnet
        self.immunity_period = hetutensor.immunity_period
        self.is_hotkey_registered_on_subnet = hetutensor.is_hotkey_registered_on_subnet
        self.is_subnet_active = hetutensor.is_subnet_active
        self.max_weight_limit = hetutensor.max_weight_limit
        self.min_allowed_weights = hetutensor.min_allowed_weights
        self.recycle = hetutensor.recycle
        self.register_subnet = hetutensor.register_subnet
        self.set_subnet_identity = hetutensor.set_subnet_identity
        self.subnet = hetutensor.subnet
        self.subnet_exists = hetutensor.subnet_exists
        self.subnetwork_n = hetutensor.subnetwork_n
        self.tempo = hetutensor.tempo
        self.weights_rate_limit = hetutensor.weights_rate_limit
        self.weights = hetutensor.weights
