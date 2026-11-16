"""诊断路由"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from application.container import container
from application.dto.requests import QueryDiagnosisRequest, TriggerDiagnosisRequest
from application.dto.responses import (
    DiagnosisReportResponse,
    DiagnosisSessionResponse,
    TriggerDiagnosisResponse,
)
from application.services.diagnosis_application_service import (
    DiagnosisApplicationService,
)
from application.use_cases.trigger_diagnosis_use_case import (
    DiagnosisAlreadyInProgressError,
)

router = APIRouter(prefix="/api/v1/diagnosis", tags=["diagnosis"])


def get_diagnosis_service() -> DiagnosisApplicationService:
    """获取诊断应用服务"""
    return container.diagnosis_service


@router.post(
    "/trigger",
    response_model=TriggerDiagnosisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="触发诊断",
    description="触发一次新的诊断任务，返回诊断会话 ID",
)
async def trigger_diagnosis(
    request: TriggerDiagnosisRequest,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> TriggerDiagnosisResponse:
    """触发诊断"""
    try:
        return await service.trigger_diagnosis(request)
    except DiagnosisAlreadyInProgressError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/sessions",
    response_model=List[DiagnosisSessionResponse],
    summary="查询诊断会话",
    description="根据条件查询诊断会话列表",
)
async def query_diagnosis(
    session_id: Optional[str] = None,
    service_name: Optional[str] = None,
    status_param: Optional[str] = None,
    limit: int = 10,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> List[DiagnosisSessionResponse]:
    """查询诊断会话"""
    request = QueryDiagnosisRequest(
        session_id=session_id,
        service_name=service_name,
        status=status_param,
        limit=limit,
    )
    return await service.query_diagnosis(request)


@router.get(
    "/sessions/{session_id}",
    response_model=DiagnosisSessionResponse,
    summary="获取诊断会话详情",
    description="根据会话 ID 获取诊断详情",
)
async def get_diagnosis_by_id(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> DiagnosisSessionResponse:
    """获取诊断会话详情"""
    result = await service.get_diagnosis_by_id(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnosis session {session_id} not found",
        )
    return result


@router.get(
    "/sessions/{session_id}/report",
    response_model=DiagnosisReportResponse,
    summary="获取诊断报告",
    description="获取完整的诊断报告（含证据和根因）",
)
async def get_diagnosis_report(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> DiagnosisReportResponse:
    """获取诊断报告"""
    try:
        return await service.get_diagnosis_report(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="取消诊断",
    description="取消正在进行的诊断任务",
)
async def cancel_diagnosis(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> None:
    """取消诊断"""
    try:
        await service.cancel_diagnosis(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/sessions/{session_id}/retry",
    response_model=TriggerDiagnosisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="重新诊断",
    description="重新执行失败的诊断任务",
)
async def retry_diagnosis(
    session_id: str,
    service: DiagnosisApplicationService = Depends(get_diagnosis_service),
) -> TriggerDiagnosisResponse:
    """重新诊断"""
    try:
        return await service.retry_diagnosis(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
