"""标准响应模型定义"""
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

# 定义泛型类型，用于指定 data 字段的类型
T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    标准响应模型
    
    所有API接口统一使用此响应格式：
    - code: 状态码，0表示成功，非0表示失败
    - message: 响应消息，成功时通常为"Success"，失败时为错误信息
    - data: 响应数据，成功时包含实际数据，失败时通常为None
    """
    code: int
    message: str
    data: Optional[T] = None

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "Success",
                "data": {}
            }
        }


class SuccessResponse(StandardResponse[T]):
    """成功响应的便捷类"""
    code: int = 0
    message: str = "Success"

