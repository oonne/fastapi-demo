"""任务相关的数据模型"""
import json
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.constant.task_status import TaskStatus
from app.constant.task_type import TaskType


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    model_config = ConfigDict(populate_by_name=True)
    
    task_id: str = Field(..., alias="taskId", description="任务ID，由业务模块提供")
    task_type: int = Field(..., alias="taskType", description="任务类型：1-文本生成订单, 2-图片生成订单, 3-语音生成订单")
    input: Dict[str, Any] = Field(
        ..., 
        description="任务参数，JSON格式",
        json_schema_extra={
            "example": {"text": "用户输入的文本内容"}
        }
    )
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v: int) -> int:
        """验证任务类型是否有效"""
        valid_types = [TaskType.TEXT_TO_ORDER.value, TaskType.IMAGE_TO_ORDER.value, TaskType.VOICE_TO_ORDER.value]
        if v not in valid_types:
            valid_types_str = ", ".join(map(str, valid_types))
            raise ValueError(f"无效的任务类型: {v}，有效值: {valid_types_str}")
        return v
    
    @field_validator('input')
    @classmethod
    def validate_input(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证 input 字段
        
        限制：
        1. 不能为空字典
        2. JSON 序列化后大小不超过 1MB（防止过大请求）
        3. 嵌套深度不超过 10 层（防止过深嵌套）
        """
        # 检查不能为空字典
        if not v:
            raise ValueError("input 不能为空字典")
        
        # 检查 JSON 序列化后的大小（限制为 1MB）
        try:
            json_str = json.dumps(v, ensure_ascii=False)
            size_mb = len(json_str.encode('utf-8')) / (1024 * 1024)
            if size_mb > 1:
                raise ValueError(f"input 序列化后大小不能超过 1MB，当前大小: {size_mb:.2f}MB")
        except (TypeError, ValueError) as e:
            if isinstance(e, ValueError) and "大小不能超过" in str(e):
                raise
            raise ValueError(f"input 包含无法序列化的数据: {str(e)}")
        
        # 检查嵌套深度（限制为 10 层）
        def get_depth(obj: Any, current_depth: int = 0) -> int:
            """递归计算字典/列表的最大嵌套深度"""
            if current_depth > 10:
                return current_depth
            
            if isinstance(obj, dict):
                if not obj:
                    return current_depth
                return max(get_depth(v, current_depth + 1) for v in obj.values())
            elif isinstance(obj, list):
                if not obj:
                    return current_depth
                return max(get_depth(item, current_depth + 1) for item in obj)
            else:
                return current_depth
        
        depth = get_depth(v)
        if depth > 10:
            raise ValueError(f"input 嵌套深度不能超过 10 层，当前深度: {depth}")
        
        return v


class TaskResponse(BaseModel):
    """任务响应模型"""
    model_config = ConfigDict(populate_by_name=True)
    
    task_id: str = Field(..., alias="taskId")
    task_type: int = Field(..., alias="taskType")
    status: TaskStatus
    progress: Optional[str] = None
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: list[TaskResponse]
    total: int


class TaskGetDetailRequest(BaseModel):
    """获取任务详情请求模型"""
    model_config = ConfigDict(populate_by_name=True)
    
    task_id: str = Field(..., alias="taskId", description="任务ID")


class TaskGetListRequest(BaseModel):
    """获取任务列表请求模型"""
    status: Optional[str] = Field(None, description="任务状态筛选，可选值: PENDING, RUNNING, 成功, FAILED")


class ProgressUpdate(BaseModel):
    """进度更新参数模型"""
    info: str = Field(..., description="进度信息")
    status: Optional[TaskStatus] = Field(None, description="可选的任务状态，如果提供则同时更新状态")
    trigger_callback: bool = Field(True, description="是否触发回调，默认为True")
