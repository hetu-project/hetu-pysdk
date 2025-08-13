import base64
import json
import sys
from typing import Any, ClassVar, Optional, Union
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
