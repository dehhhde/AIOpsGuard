"""领域模型与 ORM 模型的映射器

负责在领域模型和数据库 ORM 模型之间转换
"""
from .diagnosis_mapper import DiagnosisMapper

__all__ = ["DiagnosisMapper"]
