import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from hetu.hetu import Hetutensor
from hetu.cosmos.hetu.checkpointing.v1 import query_pb2


def query_raw_checkpoint_list():
    grpc_endpoint = "localhost:9090" 
    request = query_pb2.QueryRawCheckpointListRequest()
    hetu = Hetutensor()
    try:
        response = hetu.query_raw_checkpoint_list(grpc_endpoint, request)
        print("gRPC RawCheckpointList response:", response)
        assert response is not None
    except Exception as e:
        print(f"gRPC call failed: {e}")

query_raw_checkpoint_list()