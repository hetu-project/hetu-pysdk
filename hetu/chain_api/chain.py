from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Chain:
    """Class for managing chain state operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.get_block_hash = hetutensor.get_block_hash
        self.get_current_block = hetutensor.get_current_block
        self.get_delegate_identities = hetutensor.get_delegate_identities
        self.get_existential_deposit = hetutensor.get_existential_deposit
        self.get_minimum_required_stake = hetutensor.get_minimum_required_stake
        self.get_vote_data = hetutensor.get_vote_data
        self.get_timestamp = hetutensor.get_timestamp
        self.is_fast_blocks = hetutensor.is_fast_blocks
        self.last_drand_round = hetutensor.last_drand_round
        self.state_call = hetutensor.state_call
        self.tx_rate_limit = hetutensor.tx_rate_limit
