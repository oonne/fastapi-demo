"""回调服务模块"""
import asyncio
import json
from typing import Optional, Dict, Any
import httpx
from app.constant.task_status import TaskStatus
from app.config.config import settings
from app.utils.logger import get_logger

logger = get_logger("app")


class CallbackService:
    """回调服务，负责向业务模块发送回调请求"""
    
    def __init__(self):
        self.timeout = settings.callback_timeout
    
    async def callback(
        self,
        task_id: str,
        status: TaskStatus,
        output: Optional[Dict[str, Any]] = None,
        progress: Optional[str] = None
    ) -> None:
        """
        发送回调请求
        
        Args:
            task_id: 任务ID
            status: 任务状态
            output: 任务输出（成功时为结果，失败时为包含error的字典）
            progress: 任务进度信息
        """
        # 构建回调数据
        callback_data = {
            "taskId": task_id,
            "taskStatus": status.value,
            "progress": progress,
            "output": json.dumps(output) if output is not None else None
        }
        
        # 使用固定配置构建回调URL和请求头
        callback_url = settings.callback_domain + "/ai-task/callback-update"
        callback_headers = {"Content-Type": "application/json"}
        if settings.callback_key:
            callback_headers["x-api-key"] = settings.callback_key
        
        # 使用 asyncio.create_task 异步执行，不阻塞主流程
        asyncio.create_task(self._send_callback(
            callback_url=callback_url,
            callback_method="POST",  # 固定使用POST
            callback_headers=callback_headers,
            callback_data=callback_data,
            task_id=task_id
        ))
    
    async def _send_callback(
        self,
        callback_url: str,
        callback_method: str,
        callback_headers: Optional[Dict[str, str]],
        callback_data: Dict[str, Any],
        task_id: str
    ) -> None:
        """
        实际发送回调请求
        
        Args:
            callback_url: 回调URL
            callback_method: 回调方法
            callback_headers: 回调请求头
            callback_data: 回调数据
            task_id: 任务ID
        """
        try:
            # 使用 httpx.AsyncClient 异步发送HTTP请求
            # 固定使用POST方法
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    callback_url,
                    json=callback_data,
                    headers=callback_headers
                )
                
                # 检查响应状态
                if response.is_success:
                    logger.info(
                        f"回调成功: task_id={task_id}, "
                        f"url={callback_url}, status_code={response.status_code}"
                    )
                else:
                    logger.warning(
                        f"回调失败: task_id={task_id}, "
                        f"url={callback_url}, status_code={response.status_code}, "
                        f"response={response.text[:200]}"
                    )
        
        except httpx.TimeoutException:
            logger.error(
                f"回调超时: task_id={task_id}, url={callback_url}, "
                f"timeout={self.timeout}s"
            )
        except httpx.HTTPError as e:
            logger.error(
                f"回调HTTP错误: task_id={task_id}, url={callback_url}, error={str(e)}"
            )
        except Exception as e:
            logger.error(
                f"回调异常: task_id={task_id}, url={callback_url}, error={str(e)}",
                exc_info=True
            )


# 全局回调服务实例
callback_service = CallbackService()
