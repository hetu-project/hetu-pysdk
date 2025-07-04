from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Queries:
    """Class for managing hetutensor query operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.query_constant = hetutensor.query_constant
        self.query_map = hetutensor.query_map
        self.query_map_hetutensor = hetutensor.query_map_hetutensor
        self.query_module = hetutensor.query_module
        self.query_runtime_api = hetutensor.query_runtime_api
        self.query_hetutensor = hetutensor.query_hetutensor
