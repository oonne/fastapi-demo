"""错误码常量定义
使用示例：
    from app.constant.error_code import ErrorCode
    
    return error_response(ErrorCode.PARAM_ERROR, "参数缺失")
"""


class ErrorCode:
    # 未知错误
    UNKNOWN_ERROR = 10000
    
    # 认证相关错误
    AUTH_MISSING_API_KEY = 10001  # 缺少 API Key
    AUTH_INVALID_API_KEY = 10002  # API Key 无效
    
    # 任务相关错误
    TASK_NOT_FOUND = 20001  # 任务不存在
    TASK_ID_EXISTS = 20002  # 任务ID已存在
    TASK_TYPE_NOT_SUPPORTED = 20003  # 不支持的任务类型