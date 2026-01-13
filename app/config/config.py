"""
应用配置模块
使用 pydantic-settings 管理环境变量
"""
import os
from pathlib import Path
from typing import Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# 在创建 Settings 实例之前，先加载 .env.local 文件中的所有环境变量到 os.environ
# 这样即使 Settings 类中没有定义的字段，也能通过 os.getenv() 访问
env_file = Path(".env.local")
if env_file.exists():
    load_dotenv(env_file, override=False)  # override=False 表示不覆盖已存在的环境变量

class Settings(BaseSettings):
    # 应用配置
    env_name: str = "prod"
    
    # API Key 认证配置
    api_key: str = ""  # API Key，从环境变量读取，默认空字符串（生产环境必须设置）
    
    # 任务管理配置
    max_concurrent_tasks: int = 0  # 最大并发任务数，0表示不限制
    callback_timeout: int = 30  # 回调请求超时时间（秒）
    
    # 回调配置
    callback_domain: str = ""  # 回调域名，从环境变量 CALLBACK_DOMAIN 读取
    callback_key: str = ""  # 回调API Key，从环境变量 CALLBACK_KEY 读取
    
    # LLM 多模型配置
    # 模型配置字典，key 为模型标识符（用于选择模型），value 为模型配置
    # API Key 通过环境变量读取，命名规则：DASHSCOPE_API_KEY_{模型标识符}（大写，下划线分隔）
    # 例如：模型标识符为 "qwen-turbo"，则环境变量名为 DASHSCOPE_API_KEY_QWEN_TURBO
    # 默认配置示例（可在代码中修改或通过环境变量覆盖）
    llm_models_config: Dict[str, Dict[str, Any]] = Field(
        default={
            "qwen-turbo": {
                "provider": "tongyi",
                "model_name": "qwen-turbo",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 60,
            },
            "qwen-plus": {
                "provider": "tongyi",
                "model_name": "qwen-plus",
                "temperature": 0.8,
                "max_tokens": 3000,
                "timeout": 60,
            },
        },
        description="LLM 多模型配置字典"
    )
    dashscope_api_key_qwen_turbo: str = ""
    dashscope_api_key_qwen_plus: str = ""
    
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

