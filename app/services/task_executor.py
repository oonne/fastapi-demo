"""任务执行器模块"""
from typing import Dict, Any, Type, Optional
from app.tasks.base import BaseTask
from app.services.task_manager import TaskManager, task_manager
from app.services.callback_service import callback_service
from app.constant.task_status import TaskStatus
from app.constant.task_type import TaskType
from app.utils.logger import get_logger
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode

logger = get_logger("app")


class TaskExecutor:
    """任务执行器，负责执行任务并管理任务生命周期"""
    
    def __init__(self):
        self._task_types: Dict[int, Type[BaseTask]] = {}
    
    def register_task_type(self, task_type: TaskType, task_class: Type[BaseTask]) -> None:
        """
        注册任务类型
        
        Args:
            task_type: 任务类型枚举值
            task_class: 任务类（必须继承自 BaseTask）
        """
        if not issubclass(task_class, BaseTask):
            raise ValueError(f"任务类 {task_class.__name__} 必须继承自 BaseTask")
        
        self._task_types[task_type.value] = task_class
        logger.info(f"注册任务类型: task_type={task_type.value} ({task_type.name_cn}), class={task_class.__name__}")
    
    async def execute_task(
        self,
        task_id: str,
        task_type: int,
        input: Dict[str, Any],
        task_manager_instance: Optional[TaskManager] = None
    ) -> None:
        """
        执行任务
        
        执行流程：
        1. 更新任务状态为 RUNNING
        2. 根据任务类型获取对应的任务类
        3. 创建任务实例并执行
        4. 执行成功：更新状态为 SUCCESS，保存结果，触发回调，删除任务
        5. 执行失败：更新状态为 FAILED，保存错误信息，触发回调，删除任务
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            input: 任务参数
            task_manager_instance: 任务管理器实例，默认使用全局实例
        """
        if task_manager_instance is None:
            task_manager_instance = task_manager
        
        try:
            # 1. 更新任务状态为 RUNNING
            await task_manager_instance.update_status(task_id, TaskStatus.RUNNING)
            logger.info(f"开始执行任务: task_id={task_id}, task_type={task_type}")
            
            # 2. 根据任务类型获取对应的任务类
            task_class = self._task_types.get(task_type)
            if not task_class:
                raise CustomException(
                    code=ErrorCode.TASK_TYPE_NOT_SUPPORTED,
                    message=f"不支持的任务类型: {task_type}",
                    status_code=400
                )
            
            # 3. 创建任务实例并执行
            task_instance = task_class(
                task_id=task_id,
                task_params=input,
                task_manager=task_manager_instance
            )
            
            result = await task_instance.execute()
            
            # 4. 执行成功：更新状态为 SUCCESS，保存结果
            await task_manager_instance.update_status(task_id, TaskStatus.SUCCESS)
            await task_manager_instance.update_result(task_id, result)
            
            # 获取任务信息用于回调
            task = await task_manager_instance.get_task(task_id)
            if task:
                logger.info(f"任务执行成功: task_id={task_id}")
                
                # 触发回调（使用固定配置）
                await callback_service.callback(
                    task_id=task_id,
                    status=TaskStatus.SUCCESS,
                    output=result,
                    progress=task.progress
                )
                
                # 删除任务
                await task_manager_instance.delete_task(task_id)
        
        except Exception as e:
            # 5. 执行失败：更新状态为 FAILED，保存错误信息
            # 判断是否是 CustomException，如果是则保存错误码和错误消息
            if isinstance(e, CustomException):
                error_output = {
                    "error": e.message,
                    "code": e.code
                }
                await task_manager_instance.update_status(task_id, TaskStatus.FAILED)
                await task_manager_instance.update_result(task_id, error_output)
                
                logger.error(
                    f"任务执行失败: task_id={task_id}, code={e.code}, error={e.message}",
                    exc_info=True
                )
            else:
                # 普通异常，只保存错误消息
                error_message = str(e)
                await task_manager_instance.update_status(task_id, TaskStatus.FAILED)
                await task_manager_instance.update_error(task_id, error_message)
                
                logger.error(
                    f"任务执行失败: task_id={task_id}, error={error_message}",
                    exc_info=True
                )
                error_output = {"error": error_message}
            
            # 获取任务信息用于回调
            task = await task_manager_instance.get_task(task_id)
            if task:
                # 触发回调（使用固定配置）
                await callback_service.callback(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    output=error_output,
                    progress=task.progress
                )
                
                # 删除任务
                await task_manager_instance.delete_task(task_id)


# 全局任务执行器实例
task_executor = TaskExecutor()
