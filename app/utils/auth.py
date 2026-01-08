"""
API Key 认证工具模块
提供 API Key 验证的依赖项
"""
from fastapi import Security
from fastapi.security import APIKeyHeader
from app.config.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode

logger = get_logger("app")

# 定义 API Key Header
api_key_header = APIKeyHeader(
    name=settings.api_key_header_name,
    auto_error=False  # 设置为 False，手动处理错误以返回标准格式
)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    API Key 验证依赖项
    
    使用方式：
        from app.utils.auth import verify_api_key
        
        @router.post("/")
        async def endpoint(api_key: str = Depends(verify_api_key)):
            # 业务逻辑
            pass
    
    Args:
        api_key: 从 Header 中提取的 API Key
    
    Returns:
        str: 验证通过后返回 API Key
    
    Raises:
        CustomException: 当 API Key 无效时抛出异常，使用项目标准错误格式
    """
    # 如果配置中没有设置 API Key，跳过验证（开发环境）
    if not settings.api_key:
        logger.warning("API Key 未配置，跳过认证验证（仅用于开发环境）")
        return "dev_mode"
    
    # 检查是否提供了 API Key
    if not api_key:
        logger.warning("请求缺少 API Key")
        raise CustomException(
            code=ErrorCode.AUTH_MISSING_API_KEY,
            message="缺少 API Key，请在 Header 中提供 X-API-Key",
            status_code=401
        )
    
    # 验证 API Key 是否匹配
    if api_key != settings.api_key:
        logger.warning(f"API Key 验证失败: {api_key[:10]}...")
        raise CustomException(
            code=ErrorCode.AUTH_INVALID_API_KEY,
            message="API Key 无效",
            status_code=401
        )
    
    logger.debug("API Key 验证成功")
    return api_key
