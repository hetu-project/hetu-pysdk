from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Delegates:
    """Class for managing delegate operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.is_hotkey_delegate = hetutensor.is_hotkey_delegate
        self.get_delegate_by_hotkey = hetutensor.get_delegate_by_hotkey
        self.set_delegate_take = hetutensor.set_delegate_take
        self.get_delegate_identities = hetutensor.get_delegate_identities
        self.get_delegate_take = hetutensor.get_delegate_take
        self.get_delegated = hetutensor.get_delegated
        self.get_delegates = hetutensor.get_delegates
