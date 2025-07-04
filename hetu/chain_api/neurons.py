from typing import Union
from hetu.hetu import Hetutensor as _Hetutensor
from hetu.async_hetutensor import AsyncHetutensor as _AsyncHetutensor


class Neurons:
    """Class for managing neuron operations."""

    def __init__(self, hetutensor: Union["_Hetutensor", "_AsyncHetutensor"]):
        self.get_all_neuron_certificates = hetutensor.get_all_neuron_certificates
        self.get_neuron_certificate = hetutensor.get_neuron_certificate
        self.neuron_for_uid = hetutensor.neuron_for_uid
        self.neurons = hetutensor.neurons
        self.neurons_lite = hetutensor.neurons_lite
        self.query_identity = hetutensor.query_identity
