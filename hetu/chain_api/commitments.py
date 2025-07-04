from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Commitments:
    """Class for managing any commitment operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.commit_reveal_enabled = hetutensor.commit_reveal_enabled
        self.get_all_commitments = hetutensor.get_all_commitments
        self.get_all_revealed_commitments = hetutensor.get_all_revealed_commitments
        self.get_commitment = hetutensor.get_commitment
        self.get_current_weight_commit_info = hetutensor.get_current_weight_commit_info
        self.get_revealed_commitment = hetutensor.get_revealed_commitment
        self.get_revealed_commitment_by_hotkey = (
            hetutensor.get_revealed_commitment_by_hotkey
        )
        self.set_commitment = hetutensor.set_commitment
        self.set_reveal_commitment = hetutensor.set_reveal_commitment
