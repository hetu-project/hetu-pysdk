from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Metagraphs:
    """Class for managing metagraph operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.get_metagraph_info = hetutensor.get_metagraph_info
        self.get_all_metagraphs_info = hetutensor.get_all_metagraphs_info
        self.metagraph = hetutensor.metagraph
