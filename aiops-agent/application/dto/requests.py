"""请求 DTO"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TriggerDiagnosisRequest(BaseModel):
    """触发诊断请求

    Attributes:
        service_name: 服务名称
        service_instance: 服务实例（可选）
        environment: 环境（prod/staging/dev）
        time_range_minutes: 时间范围（分钟），默认最近 60 分钟
        trigger_source: 触发来源（manual/alert/scheduled）
    """

    service_name: str = Field(..., min_length=1, max_length=200, description="服务名称")
    service_instance: Optional[str] = Field(
        None, max_length=200, description="服务实例"
    )
    environment: str = Field(default="prod", description="环境")
    time_range_minutes: int = Field(
        default=60, ge=1, le=1440, description="时间范围（分钟）"
    )
    trigger_source: str = Field(default="manual", description="触发来源")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "user-service",
                "service_instance": "user-service-01",
                "environment": "prod",
                "time_range_minutes": 60,
                "trigger_source": "manual",
            }
        }


class QueryDiagnosisRequest(BaseModel):
    """查询诊断请求"""

    session_id: Optional[str] = Field(None, description="诊断会话 ID")
    service_name: Optional[str] = Field(None, description="服务名称")
    status: Optional[str] = Field(None, description="诊断状态")
    limit: int = Field(default=10, ge=1, le=100, description="返回数量限制")
