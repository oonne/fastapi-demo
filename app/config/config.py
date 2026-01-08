"""
应用配置模块
使用 pydantic-settings 管理环境变量
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用配置
    env_name: str = "prod"
    
    # API Key 认证配置
    api_key: str = ""  # API Key，从环境变量读取，默认空字符串（生产环境必须设置）
    api_key_header_name: str = "X-API-Key"  # API Key 在 Header 中的名称
    
    # 配置读取环境变量
    model_config = SettingsConfigDict(
        env_file=".env.local",  # 指定 .env 文件
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量名不区分大小写（ENV_NAME 和 env_name 都可以）
        extra="ignore",  # 忽略 .env 文件中未定义的变量
    )


# 创建全局配置实例
# 当这个模块被导入时，会自动读取 .env 文件并创建配置对象
settings = Settings()

