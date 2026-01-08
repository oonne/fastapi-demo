"""响应工具函数"""
from typing import Any, Optional
from app.schemas.response import StandardResponse, SuccessResponse


def success_response(data: Any = None, message: str = "Success") -> StandardResponse:
    """
    创建成功响应
    
    Args:
        data: 响应数据，可以是任何类型
        message: 响应消息，默认为"Success"
    
    Returns:
        StandardResponse: 标准响应对象，code=0
    """
    return SuccessResponse(code=0, message=message, data=data)


def error_response(code: int, message: str, data: Any = None) -> StandardResponse:
    """
    创建错误响应
    
    Args:
        code: 错误码，非0值
        message: 错误消息
        data: 可选的错误数据，通常为None
    
    Returns:
        StandardResponse: 标准响应对象，code!=0
    """
    return StandardResponse(code=code, message=message, data=data)

