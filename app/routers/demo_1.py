from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


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
    return DemoResponse(data=request.data)

