"""任务状态枚举"""
from enum import Enum


class TaskStatus(int, Enum):
    """任务状态枚举"""
    PENDING = 1  # 待执行
    RUNNING = 2  # 执行中
    SUCCESS = 3  # 成功
    FAILED = 4  # 失败
    
    @property
    def name_cn(self) -> str:
        """获取中文名称"""
        name_map = {
            TaskStatus.PENDING: "待执行",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.SUCCESS: "成功",
            TaskStatus.FAILED: "失败",
        }
        return name_map[self]
