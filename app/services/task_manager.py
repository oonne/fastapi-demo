"""任务管理器模块"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
from app.schemas.task import TaskResponse
from app.constant.task_status import TaskStatus
from app.utils.logger import get_logger
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode

logger = get_logger("app")


class Task:
    """任务数据类"""
    
    def __init__(
        self,
        task_id: str,
        task_type: int,
        input: Dict
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.progress: Optional[str] = None
        self.input = input
        self.output: Optional[Dict] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_response(self) -> TaskResponse:
        """转换为响应模型"""
        return TaskResponse(
            task_id=self.task_id,
            task_type=self.task_type,
            status=self.status,
            progress=self.progress,
            input=self.input,
            output=self.output,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class TaskManager:
    """任务管理器，使用内存字典存储任务"""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
    
    async def create_task(
        self,
        task_id: str,
        task_type: int,
        input: Dict
    ) -> Task:
        """
        创建任务
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            input: 任务参数
        
        Returns:
            Task: 创建的任务对象
        
        Raises:
            CustomException: 如果任务ID已存在
        """
        async with self._lock:
            if task_id in self._tasks:
                logger.warning(f"任务ID已存在: {task_id}")
                raise CustomException(
                    code=ErrorCode.TASK_ID_EXISTS,
                    message=f"任务ID已存在: {task_id}",
                    status_code=400
                )
            
            task = Task(
                task_id=task_id,
                task_type=task_type,
                input=input
            )
            self._tasks[task_id] = task
            logger.info(f"创建任务成功: task_id={task_id}, task_type={task_type}")
            return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            Task: 任务对象，如果不存在则返回None
        """
        async with self._lock:
            return self._tasks.get(task_id)
    
    async def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        获取任务列表
        
        Args:
            status: 可选的状态筛选
        
        Returns:
            List[Task]: 任务列表
        """
        async with self._lock:
            tasks = list(self._tasks.values())
            if status:
                tasks = [task for task in tasks if task.status == status]
            return tasks
    
    async def update_status(self, task_id: str, status: TaskStatus) -> None:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = status
                task.updated_at = datetime.now()
                logger.info(f"更新任务状态: task_id={task_id}, status={status.value}")
    
    async def update_result(self, task_id: str, result: Dict) -> None:
        """
        更新任务结果
        
        Args:
            task_id: 任务ID
            result: 任务结果
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.output = result
                task.updated_at = datetime.now()
                logger.info(f"更新任务结果: task_id={task_id}")
    
    async def update_progress(self, task_id: str, info: str) -> None:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            info: 进度信息
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.progress = info
                task.updated_at = datetime.now()
                logger.debug(f"更新任务进度: task_id={task_id}, info={info}")
    
    async def update_error(self, task_id: str, error: str) -> None:
        """
        更新错误信息
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.output = {"error": error}
                task.updated_at = datetime.now()
                logger.warning(f"更新任务错误: task_id={task_id}, error={error}")
    
    async def delete_task(self, task_id: str) -> None:
        """
        删除任务
        
        Args:
            task_id: 任务ID
        """
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"删除任务: task_id={task_id}")


# 全局任务管理器实例
task_manager = TaskManager()
