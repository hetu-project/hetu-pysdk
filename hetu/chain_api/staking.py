from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Staking:
    """Class for managing staking operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.add_stake = hetutensor.add_stake
        self.add_stake_multiple = hetutensor.add_stake_multiple
        self.get_hotkey_stake = hetutensor.get_hotkey_stake
        self.get_minimum_required_stake = hetutensor.get_minimum_required_stake
        self.get_stake = hetutensor.get_stake
        self.get_stake_add_fee = hetutensor.get_stake_add_fee
        self.get_stake_for_coldkey = hetutensor.get_stake_for_coldkey
        self.get_stake_for_coldkey_and_hotkey = (
            hetutensor.get_stake_for_coldkey_and_hotkey
        )
        self.get_stake_info_for_coldkey = hetutensor.get_stake_info_for_coldkey
        self.get_stake_movement_fee = hetutensor.get_stake_movement_fee
        self.get_unstake_fee = hetutensor.get_unstake_fee
        self.unstake = hetutensor.unstake
        self.unstake_multiple = hetutensor.unstake_multiple
