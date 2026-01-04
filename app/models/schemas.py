from pydantic import BaseModel, Field


# Item 相关的 Pydantic 模型

class ItemBase(BaseModel):
    """Item 的基础模型，包含所有共享字段"""
    name: str = Field(..., description="物品名称", min_length=1, max_length=100)
    description: str | None = Field(None, description="物品描述", max_length=500)
    price: float = Field(..., description="价格", gt=0)
    tax: float | None = Field(None, description="税费", ge=0)


class ItemCreate(ItemBase):
    """创建物品的请求模型"""
    pass


class ItemUpdate(BaseModel):
    """更新物品的请求模型（所有字段都是可选的）"""
    name: str | None = Field(None, description="物品名称", min_length=1, max_length=100)
    description: str | None = Field(None, description="物品描述", max_length=500)
    price: float | None = Field(None, description="价格", gt=0)
    tax: float | None = Field(None, description="税费", ge=0)


class ItemResponse(ItemBase):
    """物品的响应模型"""
    id: int = Field(..., description="物品 ID")
    
    class Config:
        """Pydantic 配置"""
        # 允许从 ORM 对象创建（如果使用 SQLAlchemy 等）
        from_attributes = True
        # JSON Schema 示例
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "笔记本电脑",
                "description": "高性能笔记本电脑",
                "price": 5999.99,
                "tax": 599.99
            }
        }

