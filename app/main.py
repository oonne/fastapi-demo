from fastapi import FastAPI

from app.config.config import settings
from app.routers import demo_1, demo_2
from app.utils.logger import setup_logging

# 初始化日志配置（需要在应用创建之前执行，以便 Uvicorn 使用配置）
setup_logging(
    log_dir="logs",
    app_log_level="INFO",
    access_log_level="INFO",
    backup_count=30,  # 保留30天的日志
)

app = FastAPI()

# 注册路由
app.include_router(demo_1.router, prefix="/api/demo-1", tags=["demo-1"])
app.include_router(demo_2.router, prefix="/api/demo-2", tags=["demo-2"])

print(settings.env_name)