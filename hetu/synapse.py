import base64
import json
import sys
import time
from typing import Any, ClassVar, Optional, Union, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator

class BaseSynapse(BaseModel):
    """Base class for all synapse types."""
    
    # Basic fields
    hotkey: Optional[str] = None  # Wallet address
    signature: Optional[str] = None  # Signature
    
    # Type conversion validators
    @field_validator('hotkey', mode='before')
    @classmethod
    def validate_hotkey(cls, v):
        if v is not None and not isinstance(v, str):
            return str(v)
        return v
    
    @field_validator('signature', mode='before')
    @classmethod
    def validate_signature(cls, v):
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

class Synapse(BaseSynapse):
    """
    Main Synapse class for request/response communication between Axon and Dendrite.
    """
    
    # Core fields
    completion: str = ""  # Request/response content
    status_code: int = 200  # HTTP status code
    error: Optional[str] = None  # Error message if any
    
    # Request metadata
    request_id: Optional[str] = None  # Unique request identifier
    timestamp: Optional[float] = None  # Request timestamp
    timeout: Optional[float] = None  # Request timeout
    
    # Response metadata
    process_time: Optional[float] = None  # Processing time
    response_time: Optional[float] = None  # Response timestamp
    
    # Additional fields
    metadata: Optional[Dict[str, Any]] = None  # Custom metadata
    headers: Optional[Dict[str, str]] = None  # Request/response headers
    
    # Validation
    model_config = ConfigDict(extra='allow')  # Allow extra fields
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}
        if self.headers is None:
            self.headers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert synapse to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Synapse':
        """Create synapse from dictionary."""
        return cls(**data)
    
    def set_completion(self, completion: str) -> 'Synapse':
        """Set completion content."""
        self.completion = completion
        return self
    
    def set_error(self, error: str, status_code: int = 500) -> 'Synapse':
        """Set error message and status code."""
        self.error = error
        self.status_code = status_code
        return self
    
    def set_success(self, completion: str, status_code: int = 200) -> 'Synapse':
        """Set success response."""
        self.completion = completion
        self.status_code = status_code
        self.error = None
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'Synapse':
        """Add metadata key-value pair."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        return self
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)
    
    def is_success(self) -> bool:
        """Check if response is successful."""
        return 200 <= self.status_code < 300
    
    def is_error(self) -> bool:
        """Check if response has error."""
        return self.status_code >= 400 or self.error is not None
    
    def __str__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.is_success() else "ERROR"
        return f"Synapse({status}, code={self.status_code}, completion='{self.completion[:50]}...')"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Synapse(completion='{self.completion}', status_code={self.status_code}, error='{self.error}')"

class TerminalInfo(BaseModel):
    """Terminal information for endpoints."""
    
    # Basic information
    ip: str
    port: int
    protocol: str = "http"
    
    # Terminal information
    version: Optional[str] = None
    capabilities: Optional[list[str]] = None
    
    # Custom fields (subclasses can add)
    metadata: Optional[dict] = {}

class SynapseRequest(BaseModel):
    """Request wrapper for synapse."""
    
    synapse: Synapse
    target_axon: Optional[str] = None
    priority: float = 0.0
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "synapse": self.synapse.to_dict(),
            "target_axon": self.target_axon,
            "priority": self.priority,
            "timeout": self.timeout
        }

class SynapseResponse(BaseModel):
    """Response wrapper for synapse."""
    
    synapse: Synapse
    source_axon: Optional[str] = None
    response_time: float = 0.0
    success: bool = True
    
    @classmethod
    def from_synapse(cls, synapse: Synapse, source_axon: str = None) -> 'SynapseResponse':
        """Create response from synapse."""
        return cls(
            synapse=synapse,
            source_axon=source_axon,
            response_time=time.time(),
            success=synapse.is_success()
        )
