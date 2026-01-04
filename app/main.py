from typing import Union

from fastapi import FastAPI

from app.routers import items

app = FastAPI()

# 注册路由
app.include_router(items.router, prefix="/api", tags=["items"])