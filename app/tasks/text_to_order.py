"""文本转订单任务实现"""
import asyncio
from typing import Dict, Any
from app.tasks.base import BaseTask
from app.schemas.task import ProgressUpdate
from app.constant.task_status import TaskStatus
from app.utils.logger import get_logger

logger = get_logger("app")


class TextToOrderTask(BaseTask):
    """文本转订单任务"""
    
    async def execute(self) -> Dict[str, Any]:
        """
        执行文本转订单任务
        
        Returns:
            Dict[str, Any]: 任务执行结果（空数据，待补充）
        """
        logger.info(f"开始执行文本转订单任务: task_id={self.task_id}")
        
        await asyncio.sleep(1)
        await self.update_progress(ProgressUpdate(
            info="正在解析文本内容...",
            status=TaskStatus.RUNNING
        ))
        await asyncio.sleep(1)
        
        # 最终进度更新
        await self.update_progress(ProgressUpdate(info="处理完成"))
        
        logger.info(f"文本转订单任务完成: task_id={self.task_id}")
        
        # 返回空数据
        return {}
