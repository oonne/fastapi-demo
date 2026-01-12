"""任务基类模块"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.services.task_manager import TaskManager


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
    
    async def update_progress(self, info: str) -> None:
        """
        更新任务进度
        
        Args:
            info: 进度信息
        """
        await self.task_manager.update_progress(self.task_id, info)
    
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
