import base64
import json
import sys
from typing import Any, ClassVar, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

class TerminalInfo(BaseModel):
    """简化的终端信息"""
    model_config = ConfigDict(validate_assignment=True)

    status_code: Optional[int] = None
    status_message: Optional[str] = None
    process_time: Optional[float] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    hotkey: Optional[str] = None  # 钱包地址
    signature: Optional[str] = None  # 签名

    # 类型转换验证器
    _extract_process_time = field_validator("process_time", mode="before")(lambda x: float(x) if x is not None else x)
    _extract_port = field_validator("port", mode="before")(lambda x: int(x) if x is not None else x)

class Synapse(BaseModel):
    """简化的 Synapse 类"""
    model_config = ConfigDict(validate_assignment=True)

    # 基本信息
    name: Optional[str] = None
    timeout: Optional[float] = 12.0
    total_size: Optional[int] = 0
    header_size: Optional[int] = 0

    # 终端信息
    dendrite: Optional[TerminalInfo] = None
    axon: Optional[TerminalInfo] = None

    # 自定义字段（子类可以添加）
    completion: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None

    @field_validator("name", mode="before")
    def set_name_type(cls, values):
        if isinstance(values, dict):
            values["name"] = cls.__name__
        return values

    def to_dict(self) -> dict:
        """转换为字典"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Synapse":
        """从字典创建实例"""
        return cls(**data)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(completion={self.completion})"

    def __repr__(self) -> str:
        return self.__str__()
