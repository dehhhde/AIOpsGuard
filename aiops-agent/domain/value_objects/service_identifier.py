"""服务标识符值对象"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ServiceIdentifier:
    """服务标识符值对象
    
    用于唯一标识一个服务实例
    
    特性：
    - 不可变
    - 服务名必填
    - 实例地址可选（用于定位具体实例）
    """
    
    service_name: str
    instance: Optional[str] = None
    
    def __post_init__(self) -> None:
        """验证服务标识符"""
        if not self.service_name or not self.service_name.strip():
            raise ValueError("服务名不能为空")
    
    def is_specific_instance(self) -> bool:
        """判断是否指定了具体实例"""
        return self.instance is not None and len(self.instance.strip()) > 0
    
    def to_dict(self) -> dict[str, str | None]:
        """转换为字典"""
        return {
            "service_name": self.service_name,
            "instance": self.instance
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> "ServiceIdentifier":
        """从字典创建"""
        return cls(
            service_name=data["service_name"],
            instance=data.get("instance")
        )
    
    def __str__(self) -> str:
        if self.instance:
            return f"{self.service_name}@{self.instance}"
        return self.service_name
