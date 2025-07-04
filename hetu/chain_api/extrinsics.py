from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Extrinsics:
    """Class for managing extrinsic operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.add_stake = hetutensor.add_stake
        self.add_stake_multiple = hetutensor.add_stake_multiple
        self.burned_register = hetutensor.burned_register
        self.commit_weights = hetutensor.commit_weights
        self.move_stake = hetutensor.move_stake
        self.register = hetutensor.register
        self.register_subnet = hetutensor.register_subnet
        self.reveal_weights = hetutensor.reveal_weights
        self.root_register = hetutensor.root_register
        self.root_set_weights = hetutensor.root_set_weights
        self.set_children = hetutensor.set_children
        self.set_subnet_identity = hetutensor.set_subnet_identity
        self.set_weights = hetutensor.set_weights
        self.serve_axon = hetutensor.serve_axon
        self.start_call = hetutensor.start_call
        self.swap_stake = hetutensor.swap_stake
        self.transfer = hetutensor.transfer
        self.transfer_stake = hetutensor.transfer_stake
        self.unstake = hetutensor.unstake
        self.unstake_multiple = hetutensor.unstake_multiple
