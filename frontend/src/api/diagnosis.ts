import type {
  DiagnosisReport,
  DiagnosisSession,
  HistoryQuery,
  MetricGroup,
  OverviewStats,
  PageResult,
  TriggerPayload,
  TriggerResult,
} from '@/types/diagnosis'
import { USE_MOCK } from '@/utils/env'
import { mockApi } from '@/mock'
import { get, post } from './request'

function pathId(diagnosisId: string): string {
  return encodeURIComponent(diagnosisId)
}

export const diagnosisApi = {
  listSessions(): Promise<DiagnosisSession[]> {
    if (USE_MOCK) return mockApi.listSessions()
    return get<DiagnosisSession[]>('/v1/diagnosis')
  },

  getOverview(): Promise<OverviewStats> {
    if (USE_MOCK) return mockApi.getOverview()
    return get<OverviewStats>('/v1/diagnosis/overview')
  },

  getDetail(diagnosisId: string): Promise<DiagnosisSession> {
    if (USE_MOCK) return mockApi.getDetail(diagnosisId)
    return get<DiagnosisSession>(`/v1/diagnosis/${pathId(diagnosisId)}`)
  },

  getReport(diagnosisId: string): Promise<DiagnosisReport | undefined> {
    if (USE_MOCK) return mockApi.getReport(diagnosisId)
    return get<DiagnosisReport | undefined>(`/v1/diagnosis/${pathId(diagnosisId)}/report`)
  },

  getHistory(query: HistoryQuery): Promise<PageResult<DiagnosisSession>> {
    if (USE_MOCK) return mockApi.getHistory(query)
    return get<PageResult<DiagnosisSession>>('/v1/diagnosis/history', {
      page: query.page,
      pageSize: query.pageSize,
      serviceName: query.serviceName,
      status: query.status,
      startTime: query.startTime,
      endTime: query.endTime,
    })
  },

  trigger(payload: TriggerPayload): Promise<TriggerResult> {
    if (USE_MOCK) return mockApi.trigger(payload)
    return post<TriggerResult>('/v1/diagnosis/trigger', payload)
  },

  getMetrics(diagnosisId: string): Promise<MetricGroup[]> {
    if (USE_MOCK) return mockApi.getMetrics(diagnosisId)
    return get<MetricGroup[]>(`/v1/diagnosis/${pathId(diagnosisId)}/metrics`)
  },
}
