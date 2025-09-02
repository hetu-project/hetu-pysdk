#!/usr/bin/env python3
"""
Protocol Layer - Defines the communication protocol between miners and validators.
This file contains the Synapse classes that define the data structures and
interfaces for different services.
"""

from hetu.synapse import Synapse
from typing import Optional, Dict, Any


class MathSumSynapse(Synapse):
    """Synapse for addition service.
    
    This synapse handles mathematical addition operations between miners and validators.
    """
    
    # Input parameters
    x: float = 0.0
    y: float = 0.0
    
    # Result property
    @property
    def sum_result(self) -> float:
        """Calculate and return the sum of x and y."""
        return self.x + self.y
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert synapse to dictionary for easy serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "sum_result": self.sum_result,
            "completion": self.completion,
            "status_code": self.status_code,
            "error": self.error,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "timeout": self.timeout,
            "process_time": self.process_time,
            "response_time": self.response_time,
            "metadata": self.metadata,
            "headers": self.headers
        }


class MathProductSynapse(Synapse):
    """Synapse for multiplication service.
    
    This synapse handles mathematical multiplication operations between miners and validators.
    """
    
    # Input parameters
    x: float = 0.0
    y: float = 0.0
    
    # Result property
    @property
    def product_result(self) -> float:
        """Calculate and return the product of x and y."""
        return self.x * self.y
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert synapse to dictionary for easy serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "product_result": self.product_result,
            "completion": self.completion,
            "status_code": self.status_code,
            "error": self.error,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "timeout": self.timeout,
            "process_time": self.process_time,
            "response_time": self.response_time,
            "metadata": self.metadata,
            "headers": self.headers
        }


# Service type definitions for easy identification
SERVICE_TYPES = {
    "addition": MathSumSynapse,
    "multiplication": MathProductSynapse
}


def create_synapse(service_type: str, **kwargs) -> Optional[Synapse]:
    """Factory function to create synapse instances based on service type.
    
    Args:
        service_type: Type of service ("addition" or "multiplication")
        **kwargs: Parameters to initialize the synapse
        
    Returns:
        Synapse instance or None if service type is unknown
    """
    if service_type not in SERVICE_TYPES:
        return None
    
    synapse_class = SERVICE_TYPES[service_type]
    return synapse_class(**kwargs)


def get_available_services() -> list:
    """Get list of available service types."""
    return list(SERVICE_TYPES.keys())
