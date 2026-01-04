from fastapi import APIRouter

from app.models.schemas import ItemCreate, ItemResponse

router = APIRouter()


# POST 请求示例
@router.post("/items/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """
    创建新物品的 POST 请求示例
    
    - **name**: 物品名称（必填）
    - **description**: 物品描述（可选）
    - **price**: 价格（必填）
    - **tax**: 税费（可选）
    """
    # 模拟创建物品（实际项目中应该保存到数据库）
    # 这里只是返回一个模拟的 ID
    created_item = ItemResponse(
        id=1,  # 实际应该从数据库生成
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax
    )
    return created_item


# 另一个 POST 示例：带路径参数
@router.post("/items/{item_id}/update")
async def update_item(item_id: int, item: ItemCreate):
    """
    更新物品的 POST 请求示例
    
    - **item_id**: 路径参数，物品 ID
    - **item**: 请求体，包含要更新的物品信息
    """
    return {
        "message": f"物品 {item_id} 已更新",
        "item_id": item_id,
        "updated_data": item.model_dump()
    }

