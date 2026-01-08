from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
from app.utils.logger import get_logger
from app.utils.response import success_response
from app.utils.auth import verify_api_key
from app.schemas.response import StandardResponse

router = APIRouter()
logger = get_logger("app")


class DemoRequest(BaseModel):
    """Demo-1 请求模型，接收任意字符串数据"""
    data: str

@router.post("/", response_model=StandardResponse)
async def demo_post(request: DemoRequest, api_key: str = Depends(verify_api_key)):
    """
    Demo-1 POST 请求示例

    - **data**: 任意字符串数据（必填）

    返回标准格式响应，包含 code、message、data 字段
    """
    logger.info(f"收到 POST 请求，数据: {request.data}")
    try:
        # 业务逻辑处理
        processed_data = request.data
        
        logger.info(f"处理成功，返回数据: {processed_data}")
        # 返回成功响应，code=0，数据放在 data 字段中
        return success_response(data={"received_data": processed_data}, message="")
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
        # 抛出 HTTPException，会被异常处理器捕获并转换为标准格式
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")


@router.post("/http-request", response_model=StandardResponse)
async def http_request_handler(api_key: str = Depends(verify_api_key)):
    try:
        # 发起HTTP请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method='POST',
                url='https://yi-api.wuyanxun.com/auth/get-login-pow',
                headers={'Content-Type': 'application/json'},
                json={'name': 'admin'}
            )
            
            # 获取响应内容
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            }
            
            # 返回成功响应
            return success_response(
                data=response_data,
                message=f"请求成功"
            )
    except httpx.HTTPError as e:
        logger.error(f"HTTP请求失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"HTTP请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"处理HTTP请求时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求时出错: {str(e)}")

