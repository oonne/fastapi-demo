"""任务类型枚举"""
from enum import Enum


class TaskType(int, Enum):
    """任务类型枚举"""
    TEXT_TO_ORDER = 1  # 文本生成订单
    IMAGE_TO_ORDER = 2  # 图片生成订单
    VOICE_TO_ORDER = 3  # 语音生成订单
    
    @property
    def name_cn(self) -> str:
        """获取中文名称"""
        name_map = {
            TaskType.TEXT_TO_ORDER: "文本生成订单",
            TaskType.IMAGE_TO_ORDER: "图片生成订单",
            TaskType.VOICE_TO_ORDER: "语音生成订单",
        }
        return name_map[self]
    
    @classmethod
    def get_all_types(cls) -> list[dict]:
        """获取所有任务类型的列表，格式为 [{key: int, name: str}]"""
        return [
            {"key": cls.TEXT_TO_ORDER.value, "name": cls.TEXT_TO_ORDER.name_cn},
            {"key": cls.IMAGE_TO_ORDER.value, "name": cls.IMAGE_TO_ORDER.name_cn},
            {"key": cls.VOICE_TO_ORDER.value, "name": cls.VOICE_TO_ORDER.name_cn},
        ]
