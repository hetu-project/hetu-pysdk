from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Wallets:
    """Class for managing coldkey, hotkey, wallet operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.does_hotkey_exist = hetutensor.does_hotkey_exist
        self.filter_netuids_by_registered_hotkeys = (
            hetutensor.filter_netuids_by_registered_hotkeys
        )
        self.is_hotkey_registered_any = hetutensor.is_hotkey_registered_any
        self.is_hotkey_registered = hetutensor.is_hotkey_registered
        self.is_hotkey_delegate = hetutensor.is_hotkey_delegate
        self.get_balance = hetutensor.get_balance
        self.get_balances = hetutensor.get_balances
        self.get_children = hetutensor.get_children
        self.get_children_pending = hetutensor.get_children_pending
        self.get_delegate_by_hotkey = hetutensor.get_delegate_by_hotkey
        self.get_delegate_take = hetutensor.get_delegate_take
        self.get_delegated = hetutensor.get_delegated
        self.get_hotkey_owner = hetutensor.get_hotkey_owner
        self.get_hotkey_stake = hetutensor.get_hotkey_stake
        self.get_minimum_required_stake = hetutensor.get_minimum_required_stake
        self.get_netuids_for_hotkey = hetutensor.get_netuids_for_hotkey
        self.get_owned_hotkeys = hetutensor.get_owned_hotkeys
        self.get_stake = hetutensor.get_stake
        self.get_stake_add_fee = hetutensor.get_stake_add_fee
        self.get_stake_for_coldkey = hetutensor.get_stake_for_coldkey
        self.get_stake_for_coldkey_and_hotkey = (
            hetutensor.get_stake_for_coldkey_and_hotkey
        )
        self.get_stake_for_hotkey = hetutensor.get_stake_for_hotkey
        self.get_stake_info_for_coldkey = hetutensor.get_stake_info_for_coldkey
        self.get_stake_movement_fee = hetutensor.get_stake_movement_fee
        self.get_transfer_fee = hetutensor.get_transfer_fee
        self.get_unstake_fee = hetutensor.get_unstake_fee
