from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("app")


class DemoRequest(BaseModel):
    """Demo-1 请求模型，接收任意字符串数据"""
    data: str


class DemoResponse(BaseModel):
    """Demo-1 响应模型，返回字符串数据"""
    data: str


@router.post("/", response_model=DemoResponse)
async def demo_post(request: DemoRequest):
    """
    Demo-1 POST 请求示例

    - **data**: 任意字符串数据（必填）

    返回接收到的字符串数据
    """
    logger.info(f"收到 POST 请求，数据: {request.data}")
    try:
        response = DemoResponse(data=request.data)
        logger.info(f"处理成功，返回数据: {response.data}")
        return response
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
        raise

