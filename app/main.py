from fastapi import FastAPI

from app.config.config import settings
from app.routers import demo_1, demo_2

app = FastAPI()

# 注册路由
app.include_router(demo_1.router, prefix="/api/demo-1", tags=["demo-1"])
app.include_router(demo_2.router, prefix="/api/demo-2", tags=["demo-2"])

print(settings.env_name)