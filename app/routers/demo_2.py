from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.logger import get_logger
from app.utils.response import success_response
from app.schemas.response import StandardResponse

router = APIRouter()
logger = get_logger("app")


class DemoRequest(BaseModel):
    """Demo-2 请求模型，接收任意字符串数据"""
    data: str


@router.post("/", response_model=StandardResponse)
async def demo_post(request: DemoRequest):
    """
    Demo-2 POST 请求示例

    - **data**: 任意字符串数据（必填）

    返回标准格式响应，包含 code、message、data 字段
    """
    logger.info(f"收到 POST 请求，数据: {request.data}")
    try:
        # 业务逻辑处理
        processed_data = request.data
        
        logger.info(f"处理成功，返回数据: {processed_data}")
        # 返回成功响应，code=0，数据放在 data 字段中
        return success_response(data={"received_data": processed_data}, message="处理成功")
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
        # 抛出 HTTPException，会被异常处理器捕获并转换为标准格式
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

