from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


# 定义请求模型
class DemoRequest(BaseModel):
    """Demo 请求模型，接收任意字符串数据"""
    data: str


# 定义响应模型
class DemoResponse(BaseModel):
    """Demo 响应模型，返回字符串数据"""
    data: str


# POST 请求：接收字符串，返回字符串
@router.post("/demo/", response_model=DemoResponse)
async def demo_post(request: DemoRequest):
    """
    Demo POST 请求示例
    
    - **data**: 任意字符串数据（必填）
    
    返回接收到的字符串数据
    """
    return DemoResponse(data=request.data)

