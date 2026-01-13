"""文本转订单任务实现"""
import asyncio
from typing import Dict, Any
from app.tasks.base import BaseTask
from app.schemas.task import ProgressUpdate
from app.constant.task_status import TaskStatus
from app.utils.logger import get_logger
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode
from app.services.llm_service import llm_service

logger = get_logger("app")


class TextToOrderTask(BaseTask):
    """文本转订单任务"""
    
    async def execute(self) -> Dict[str, Any]:
        """
        执行文本转订单任务
        
        返回说明：
        - 成功时：返回的字典会直接作为 output 保存到任务中，并通过回调发送
        - 失败时：抛出异常，TaskExecutor 会自动捕获并保存为 {"error": "错误信息"}
        
        Returns:
            Dict[str, Any]: 任务执行结果，会直接作为 output 保存
            
        Raises:
            Exception: 任务执行失败时抛出异常，会被 TaskExecutor 捕获并处理
        """
        logger.info(f"开始执行文本转订单任务: task_id={self.task_id}")
        
        # 获取输入参数
        text = self.task_params.get("text", "")
        merchantId = self.task_params.get("merchantId", "")
        customerId = self.task_params.get("customerId", "")
        
        # 校验输入值
        if not text:
            raise CustomException(
                code=ErrorCode.INPUT_FORMAT_ERROR,
                message="文本内容不能为空",
            )
        if not merchantId:
            raise CustomException(
                code=ErrorCode.INPUT_FORMAT_ERROR,
                message="商户ID不能为空",
            )
        
        # 开始处理
        await self.update_progress(ProgressUpdate(
            info="开始识别订单信息",
            status=TaskStatus.RUNNING
        ))
        
        # 这是调用LLM模型的示例
        result = await llm_service.invoke(
            ["你好，请介绍一下自己"],
            model_key="qwen-turbo"  # 指定使用 qwen-turbo 模型
        )
        print('result', result)
        
        # 最终进度更新
        await self.update_progress(ProgressUpdate(info="处理完成"))
        
        logger.info(f"文本转订单任务完成: task_id={self.task_id}")
        
        # 返回任务结果
        return {
            "products": [
                {
                    "name": "商品A",
                    "quantity": 2,
                    "unit": "个",
                    "price": 99.00,
                    "remark": "商品A的备注",    
                }
            ]
        }
