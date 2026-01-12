"""任务路由模块"""
import asyncio
from fastapi import APIRouter, Depends
from app.schemas.task import TaskCreateRequest, TaskResponse, TaskListResponse, TaskGetDetailRequest
from app.schemas.response import StandardResponse
from app.services.task_manager import task_manager
from app.services.task_executor import task_executor
from app.utils.logger import get_logger
from app.utils.response import success_response
from app.utils.auth import verify_api_key
from app.utils.exceptions import CustomException
from app.constant.error_code import ErrorCode

router = APIRouter()
logger = get_logger("app")


@router.post("/create", response_model=StandardResponse)
async def create_task(
    request: TaskCreateRequest,
    api_key: str = Depends(verify_api_key)
) -> StandardResponse:
    """
    创建任务
    
    - **taskId**: 任务ID，由业务模块提供（必填）
    - **taskType**: 任务类型，1-文本生成订单, 2-图片生成订单, 3-语音生成订单（必填）
    - **input**: 任务参数，JSON格式（必填）
    
    创建任务后会立即异步启动执行
    回调URL、回调方法和回调请求头使用环境变量固定配置
    """
    
    try:
        # 创建任务（会检查任务ID是否已存在）
        task = await task_manager.create_task(
            task_id=request.task_id,
            task_type=request.task_type,
            input=request.input
        )
        
        logger.info(
            f"创建任务成功: task_id={request.task_id}, "
            f"task_type={request.task_type}"
        )
        
        # 立即异步启动执行任务（不阻塞响应）
        asyncio.create_task(
            task_executor.execute_task(
                task_id=request.task_id,
                task_type=request.task_type,
                input=request.input
            )
        )
        
        # 返回成功响应
        return success_response(
            data={"taskId": request.task_id},
            message="任务创建成功"
        )
    
    except CustomException:
        # 重新抛出自定义异常，会被异常处理器捕获
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        raise CustomException(
            code=ErrorCode.UNKNOWN_ERROR,
            message=f"创建任务失败: {str(e)}",
            status_code=500
        )


@router.post("/get-detail", response_model=StandardResponse[TaskResponse])
async def get_task(
    request: TaskGetDetailRequest,
    api_key: str = Depends(verify_api_key)
) -> StandardResponse[TaskResponse]:
    """
    查询任务状态
    
    - **taskId**: 任务ID（请求体参数）
    
    返回任务详细信息，包括 progress
    如果任务不存在，返回404错误
    """
    task = await task_manager.get_task(request.task_id)
    
    if not task:
        raise CustomException(
            code=ErrorCode.TASK_NOT_FOUND,
            message=f"任务不存在: {request.task_id}",
            status_code=404
        )
    
    return success_response(
        data=task.to_response(),
        message="查询成功"
    )


@router.post("/get-list", response_model=StandardResponse[TaskListResponse])
async def get_tasks(
    api_key: str = Depends(verify_api_key)
) -> StandardResponse[TaskListResponse]:
    """
    查询任务列表
    
    返回所有任务的完整列表，不进行任何筛选
    """
    # 获取所有任务列表
    tasks = await task_manager.get_tasks()
    
    # 转换为响应模型
    task_responses = [task.to_response() for task in tasks]
    
    return success_response(
        data=TaskListResponse(tasks=task_responses, total=len(task_responses)),
        message="查询成功"
    )
