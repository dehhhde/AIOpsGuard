"""用例模块"""

from application.use_cases.cancel_diagnosis_use_case import (
    CancelDiagnosisUseCase,
    DiagnosisCannotBeCancelledError,
    DiagnosisNotFoundError,
)
from application.use_cases.get_diagnosis_report_use_case import (
    DiagnosisReportNotFoundError,
    GetDiagnosisReportUseCase,
)
from application.use_cases.query_diagnosis_use_case import QueryDiagnosisUseCase
from application.use_cases.retry_diagnosis_use_case import (
    DiagnosisCannotBeRetriedError,
    RetryDiagnosisUseCase,
)
from application.use_cases.trigger_diagnosis_use_case import (
    DiagnosisAlreadyInProgressError,
    TriggerDiagnosisUseCase,
)

__all__ = [
    "TriggerDiagnosisUseCase",
    "QueryDiagnosisUseCase",
    "GetDiagnosisReportUseCase",
    "CancelDiagnosisUseCase",
    "RetryDiagnosisUseCase",
    "DiagnosisAlreadyInProgressError",
    "DiagnosisReportNotFoundError",
    "DiagnosisNotFoundError",
    "DiagnosisCannotBeCancelledError",
    "DiagnosisCannotBeRetriedError",
]
