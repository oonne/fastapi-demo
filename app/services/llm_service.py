"""LangChain 服务模块"""
import os
from typing import List, Union, Dict, Any, AsyncIterator, Optional
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from app.config.config import settings
from app.utils.logger import get_logger

logger = get_logger("app")


class LangChainService:
    """LangChain 服务类，统一管理 LLM 模型的调用"""
    
    def __init__(self):
        """初始化服务，根据配置创建模型实例"""
        self.models: Dict[str, BaseChatModel] = {}  # 模型字典，key 为模型标识符
        self._initialize_models()
    
    def _get_api_key_env_name(self, model_key: str) -> str:
        """
        获取模型 API Key 的环境变量名称
        
        Args:
            model_key: 模型标识符
        
        Returns:
            str: 环境变量名称，格式为 DASHSCOPE_API_KEY_{模型标识符}（大写，下划线分隔）
        """
        # 将模型标识符转换为大写，并将连字符替换为下划线
        env_suffix = model_key.upper().replace("-", "_")
        return f"DASHSCOPE_API_KEY_{env_suffix}"
    
    def _create_tongyi_model(
        self,
        model_key: str,
        model_config: Dict[str, Any],
    ) -> ChatTongyi:
        """
        创建通义千问模型实例
        
        Args:
            model_key: 模型标识符
            model_config: 模型配置字典
        
        Returns:
            ChatTongyi: 模型实例
        
        Raises:
            ValueError: 当 API Key 未配置或模型创建失败时抛出异常
        """
        # 从环境变量读取 API Key
        api_key_env_name = self._get_api_key_env_name(model_key)
        dashscope_api_key = os.getenv(api_key_env_name, "")
        
        # 如果环境变量未设置，尝试不区分大小写查找
        if not dashscope_api_key:
            # pydantic-settings 默认不区分大小写，但 os.getenv 区分大小写
            # 尝试查找所有可能的大小写组合
            for key, value in os.environ.items():
                if key.upper() == api_key_env_name.upper():
                    dashscope_api_key = value
                    logger.debug(f"找到环境变量（不区分大小写）: {key} -> {api_key_env_name}")
                    break
        
        if not dashscope_api_key:
            error_msg = (
                f"模型 '{model_key}' 的 API Key 未配置。\n"
                f"请设置环境变量 {api_key_env_name}\n"
                f"可以在 .env.local 文件中添加：{api_key_env_name}=your_api_key_here"
            )
            logger.warning(error_msg)
            raise ValueError(error_msg)
        
        try:
            return ChatTongyi(
                model_name=model_config.get("model_name", "qwen-turbo"),
                temperature=model_config.get("temperature", 0.7),
                max_tokens=model_config.get("max_tokens", 2000),
                timeout=model_config.get("timeout", 60),
                dashscope_api_key=dashscope_api_key,
            )
        except Exception as e:
            error_msg = f"创建通义千问模型 '{model_key}' 失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
    
    def _initialize_models(self) -> None:
        """
        初始化所有配置的模型
        
        注意：如果所有模型初始化失败，不会抛出异常，只记录警告
        这样应用可以正常启动，但 LLM 功能将不可用
        """
        if not settings.llm_models_config:
            logger.warning("未配置任何 LLM 模型，请在 config.py 中配置 llm_models_config")
            return
        
        initialized_count = 0
        
        for model_key, model_config in settings.llm_models_config.items():
            try:
                provider = model_config.get("provider", "").lower()
                
                if provider == "tongyi":
                    model_instance = self._create_tongyi_model(model_key, model_config)
                    self.models[model_key] = model_instance
                    initialized_count += 1
                    logger.info(
                        f"模型初始化成功: key={model_key}, "
                        f"provider={provider}, model={model_config.get('model_name')}"
                    )
                else:
                    logger.warning(
                        f"不支持的模型提供商: {provider}，跳过模型 {model_key}"
                    )
            except Exception as e:
                logger.warning(
                    f"初始化模型 {model_key} 失败: {str(e)}。"
                    f"请检查环境变量 {self._get_api_key_env_name(model_key)} 是否已配置"
                )
                # 继续初始化其他模型，不中断整个流程
        
        if initialized_count == 0:
            logger.warning(
                "没有成功初始化的模型，LLM 功能将不可用。"
                "请检查配置和 API Key 环境变量。"
                "API Key 环境变量命名规则：DASHSCOPE_API_KEY_{模型标识符}（大写，下划线分隔）"
            )
        else:
            logger.info(f"LangChain 服务初始化完成，共初始化 {initialized_count} 个模型")
    
    def _get_model(self, model_key: Optional[str] = None) -> BaseChatModel:
        """
        获取模型实例
        
        Args:
            model_key: 模型标识符，如果为 None 则使用第一个可用模型
        
        Returns:
            BaseChatModel: 模型实例
        
        Raises:
            ValueError: 当模型不存在或未初始化时抛出异常
        """
        if not self.models:
            error_msg = (
                "没有可用的模型。请检查：\n"
                "1. 是否在 config.py 中配置了 llm_models_config\n"
                "2. 是否设置了正确的 API Key 环境变量\n"
                "3. API Key 环境变量命名规则：DASHSCOPE_API_KEY_{模型标识符}（大写，下划线分隔）"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 如果没有指定模型，使用第一个可用模型
        if not model_key:
            model_key = list(self.models.keys())[0]
            logger.debug(f"未指定模型，使用第一个可用模型: {model_key}")
        
        if model_key not in self.models:
            available_models = ", ".join(self.models.keys())
            error_msg = (
                f"模型 '{model_key}' 不存在。可用模型: {available_models}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return self.models[model_key]
    
    def _format_messages(
        self, messages: List[Union[str, Dict[str, Any]]]
    ) -> List[BaseMessage]:
        """
        格式化消息列表为 LangChain BaseMessage 对象
        
        Args:
            messages: 消息列表，可以是字符串或字典格式
                - 字符串：作为 HumanMessage 处理
                - 字典：支持 {"role": "user/system/assistant", "content": "..."} 格式
                   或 {"content": "..."} 格式（默认为 user）
        
        Returns:
            List[BaseMessage]: LangChain 消息对象列表
        
        Raises:
            ValueError: 当消息格式不正确时抛出异常
        """
        formatted_messages = []
        
        for msg in messages:
            if isinstance(msg, str):
                # 字符串直接作为用户消息
                formatted_messages.append(HumanMessage(content=msg))
            elif isinstance(msg, dict):
                # 字典格式，提取 role 和 content
                role = msg.get("role", "user").lower()
                content = msg.get("content", "")
                
                if not content:
                    logger.warning("消息字典中 content 为空，跳过该消息")
                    continue
                
                # 根据 role 创建对应的消息类型
                if role == "user":
                    formatted_messages.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    formatted_messages.append(AIMessage(content=content))
                elif role == "system":
                    formatted_messages.append(SystemMessage(content=content))
                else:
                    logger.warning(f"未知的消息角色: {role}，默认作为用户消息处理")
                    formatted_messages.append(HumanMessage(content=content))
            else:
                error_msg = f"不支持的消息格式: {type(msg)}，应为 str 或 dict"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        return formatted_messages
    
    async def invoke(
        self,
        messages: List[Union[str, Dict[str, Any]]],
        model_key: Optional[str] = None,
    ) -> str:
        """
        异步调用模型，返回文本结果
        
        Args:
            messages: 消息列表，可以是字符串或字典格式
                - 字符串：作为用户消息
                - 字典：支持 {"role": "user/system/assistant", "content": "..."} 格式
            model_key: 模型标识符，如果为 None 则使用第一个可用模型
        
        Returns:
            str: 模型生成的文本结果
        
        Raises:
            ValueError: 当模型不存在或消息格式错误时抛出异常
            Exception: 当模型调用失败时抛出异常
        """
        try:
            # 获取模型实例
            llm = self._get_model(model_key)
            
            # 格式化消息
            formatted_messages = self._format_messages(messages)
            
            # 调用模型
            used_model_key = model_key or list(self.models.keys())[0]
            logger.debug(f"调用 LLM 模型: key={used_model_key}")
            response = await llm.ainvoke(formatted_messages)
            
            # 提取文本内容
            if hasattr(response, "content"):
                result = response.content
            else:
                result = str(response)
            
            logger.debug(f"LLM 调用成功: model={used_model_key}, 返回结果长度={len(result)}")
            return result
            
        except ValueError:
            # ValueError 直接抛出，不需要包装
            raise
        except Exception as e:
            error_msg = f"模型调用异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    async def astream(
        self,
        messages: List[Union[str, Dict[str, Any]]],
        model_key: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        异步流式调用，返回生成器
        
        Args:
            messages: 消息列表，可以是字符串或字典格式
                - 字符串：作为用户消息
                - 字典：支持 {"role": "user/system/assistant", "content": "..."} 格式
            model_key: 模型标识符，如果为 None 则使用第一个可用模型
        
        Yields:
            str: 模型生成的文本块（逐步返回）
        
        Raises:
            ValueError: 当模型不存在或消息格式错误时抛出异常
            Exception: 当模型调用失败时抛出异常
        """
        try:
            # 获取模型实例
            llm = self._get_model(model_key)
            
            # 格式化消息
            formatted_messages = self._format_messages(messages)
            
            # 流式调用模型
            used_model_key = model_key or list(self.models.keys())[0]
            logger.debug(f"流式调用 LLM 模型: key={used_model_key}")
            
            async for chunk in llm.astream(formatted_messages):
                # 提取文本内容
                if hasattr(chunk, "content"):
                    yield chunk.content
                else:
                    yield str(chunk)
                    
        except ValueError:
            # ValueError 直接抛出，不需要包装
            raise
        except Exception as e:
            error_msg = f"模型流式调用异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg) from e
    
    def list_models(self) -> List[str]:
        """
        获取所有可用模型的标识符列表
        
        Returns:
            List[str]: 模型标识符列表
        """
        return list(self.models.keys())
    
    def get_model_info(self, model_key: Optional[str] = None) -> Dict[str, Any]:
        """
        返回指定模型的信息
        
        Args:
            model_key: 模型标识符，如果为 None 则返回第一个模型的信息
        
        Returns:
            Dict[str, Any]: 包含模型信息的字典
        """
        if not self.models:
            return {
                "error": "没有可用的模型",
                "initialized": False,
            }
        
        # 确定使用的模型标识符
        target_model_key = model_key or list(self.models.keys())[0]
        
        if target_model_key not in self.models:
            available_models = list(self.models.keys())
            return {
                "error": f"模型 '{target_model_key}' 不存在",
                "available_models": available_models,
            }
        
        # 从配置中获取模型信息
        model_config = settings.llm_models_config.get(target_model_key, {})
        
        return {
            "model_key": target_model_key,
            "provider": model_config.get("provider", ""),
            "model_name": model_config.get("model_name", ""),
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 2000),
            "timeout": model_config.get("timeout", 60),
            "initialized": True,
            "api_key_env_name": self._get_api_key_env_name(target_model_key),
        }
    
    def get_all_models_info(self) -> Dict[str, Any]:
        """
        返回所有模型的信息
        
        Returns:
            Dict[str, Any]: 包含所有模型信息的字典
        """
        return {
            "models_count": len(self.models),
            "available_models": list(self.models.keys()),
            "models": {
                model_key: self.get_model_info(model_key)
                for model_key in self.models.keys()
            },
        }


# 全局 LangChain 服务实例
llm_service = LangChainService()
