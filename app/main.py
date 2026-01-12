from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger import get_logger
from app.config.config import settings
from app.routers import task
from app.utils.logger import setup_logging
from app.utils.response import error_response
from app.utils.exceptions import CustomException
from app.services.task_executor import task_executor
from app.tasks.text_to_order import TextToOrderTask
from app.tasks.image_to_order import ImageToOrderTask
from app.tasks.voice_to_order import VoiceToOrderTask
from app.constant.task_type import TaskType

# 初始化日志配置（需要在应用创建之前执行，以便 Uvicorn 使用配置）
setup_logging(
    log_dir="logs",
    app_log_level="INFO",
    access_log_level="INFO",
    backup_count=30,  # 保留30天的日志
)
logger = get_logger("app")

app = FastAPI()

# 注册路由
app.include_router(task.router, prefix="/task", tags=["task"])

# 初始化任务执行器：注册任务类型
task_executor.register_task_type(TaskType.TEXT_TO_ORDER, TextToOrderTask)
task_executor.register_task_type(TaskType.IMAGE_TO_ORDER, ImageToOrderTask)
task_executor.register_task_type(TaskType.VOICE_TO_ORDER, VoiceToOrderTask)
logger.info("任务类型注册完成:")
logger.info(f"  - {TaskType.TEXT_TO_ORDER.value}: {TaskType.TEXT_TO_ORDER.name_cn}")
logger.info(f"  - {TaskType.IMAGE_TO_ORDER.value}: {TaskType.IMAGE_TO_ORDER.name_cn}")
logger.info(f"  - {TaskType.VOICE_TO_ORDER.value}: {TaskType.VOICE_TO_ORDER.name_cn}")


"""
处理 HTTPException 异常，统一返回标准格式
使用方法：
raise HTTPException(status_code=500, detail="自定义错误内容")
"""
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        ).model_dump()
    )


"""
处理 Starlette HTTPException 异常，统一返回标准格式
"""
@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.status_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        ).model_dump()
    )


"""
处理请求验证错误，统一返回标准格式
"""
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        error_messages.append(f"{field}: {message}")
    
    error_msg = "; ".join(error_messages) if error_messages else "请求参数验证失败"
    
    # 记录请求详细信息用于调试
    try:
        # 读取请求体
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""
        
        # 记录请求信息
        logger.warning(
            f"请求参数验证失败 - URL: {request.url.path}, "
            f"Method: {request.method}, "
            f"Headers: {dict(request.headers)}, "
            f"Body: {body_str}, "
            f"Errors: {error_messages}"
        )
    except Exception as e:
        logger.warning(f"记录请求信息时出错: {str(e)}")
    
    return JSONResponse(
        status_code=400,
        content=error_response(
            code=400,
            message=error_msg,
            data={"errors": errors}
        ).model_dump()
    )


"""
处理自定义异常，统一返回标准格式
使用方法：
    raise CustomException(code=10001, message="自定义错误消息")
    raise CustomException(code=10001, message="自定义错误消息", status_code=400)
"""
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            data=exc.data
        ).model_dump()
    )


"""
处理其他未捕获的异常，统一返回标准格式
如果异常有 code 和 message 属性，则使用它们；否则使用默认值
使用方法：
    raise CustomException(code=10001, message="自定义错误消息")
"""
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    from app.utils.logger import get_logger
    logger = get_logger("app")
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    # 检查异常是否有自定义的 code 和 message 属性
    if hasattr(exc, 'code') and hasattr(exc, 'message'):
        status_code = getattr(exc, 'status_code', 500)
        data = getattr(exc, 'data', None)
        return JSONResponse(
            status_code=status_code,
            content=error_response(
                code=exc.code,
                message=exc.message,
                data=data
            ).model_dump()
        )
    
    # 默认处理：返回 500 错误
    return JSONResponse(
        status_code=500,
        content=error_response(
            code=500,
            message="服务器内部错误"
        ).model_dump()
    )

# 启动项目
logger.info(f"启动项目: {settings.env_name}")