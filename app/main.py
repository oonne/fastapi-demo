from fastapi import FastAPI

from app.routers import demo, items

app = FastAPI()

# 注册路由
app.include_router(items.router, prefix="/api", tags=["items"])
app.include_router(demo.router, prefix="/api", tags=["demo"])
