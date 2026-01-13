"""任务基类模块"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.services.task_manager import TaskManager
from app.services.callback_service import callback_service
from app.schemas.task import ProgressUpdate


class BaseTask(ABC):
    """任务基类，所有具体任务必须继承此类"""
    
    def __init__(
        self,
        task_id: str,
        task_params: Dict[str, Any],
        task_manager: TaskManager
    ):
        """
        初始化任务
        
        Args:
            task_id: 任务ID
            task_params: 任务参数
            task_manager: 任务管理器实例
        """
        self.task_id = task_id
        self.task_params = task_params
        self.task_manager = task_manager
    
    async def update_progress(self, progress: ProgressUpdate) -> None:
        """
        更新任务进度，可选择同时更新状态
        
        Args:
            progress: 进度更新参数对象
        """
        # 如果提供了状态，先更新状态
        if progress.status is not None:
            await self.task_manager.update_status(self.task_id, progress.status)
        
        # 更新进度
        await self.task_manager.update_progress(self.task_id, progress.info)
        
        # 触发回调
        if progress.trigger_callback:
            # 获取当前任务状态（如果没提供status参数，使用当前状态）
            task = await self.task_manager.get_task(self.task_id)
            if task:
                current_status = progress.status if progress.status is not None else task.status
                await callback_service.callback(
                    task_id=self.task_id,
                    status=current_status,
                    progress=progress.info
                )
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        执行任务（抽象方法，子类必须实现）
        
        Returns:
            Dict[str, Any]: 任务执行结果
        
        Raises:
            Exception: 任务执行失败时抛出异常
        """
        pass
