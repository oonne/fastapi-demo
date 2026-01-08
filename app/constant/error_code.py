"""错误码常量定义
使用示例：
    from app.constant.error_code import ErrorCode
    
    return error_response(ErrorCode.PARAM_ERROR, "参数缺失")
"""


class ErrorCode:
    # 未知错误
    UNKNOWN_ERROR = 10000