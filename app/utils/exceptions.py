"""自定义异常类"""
from typing import Any, Optional


class CustomException(Exception):
    """
    自定义异常类，支持自定义错误码和错误消息
    
    使用示例：
        raise CustomException(code=10001, message="自定义错误消息")
        raise CustomException(code=10001, message="自定义错误消息", status_code=400)
        raise CustomException(code=10001, message="自定义错误消息", data={"field": "value"})
    """
    
    def __init__(
        self,
        code: int,
        message: str,
        status_code: int = 500,
        data: Any = None
    ):
        """
        初始化自定义异常
        
        Args:
            code: 业务错误码（非0值）
            message: 错误消息
            status_code: HTTP 状态码，默认为 500
            data: 可选的错误数据
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)
