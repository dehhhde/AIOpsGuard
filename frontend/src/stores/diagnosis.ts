import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  DiagnosisReport,
  DiagnosisSession,
  HistoryQuery,
  MetricGroup,
  OverviewStats,
  PageResult,
  ProgressEvent,
  TriggerPayload,
  TriggerResult,
} from '@/types/diagnosis'
import { diagnosisApi } from '@/api/diagnosis'
import { isRunning } from '@/utils/diagnosis'

export const useDiagnosisStore = defineStore('diagnosis', () => {
  const sessions = ref<DiagnosisSession[]>([])
  const overview = ref<OverviewStats | null>(null)
  const current = ref<DiagnosisSession | null>(null)
  const report = ref<DiagnosisReport | null>(null)
  const metrics = ref<MetricGroup[]>([])
  const history = ref<PageResult<DiagnosisSession>>({ items: [], total: 0, page: 1, pageSize: 10 })
  const historyQuery = reactive<HistoryQuery>({ page: 1, pageSize: 10 })

  const loading = reactive({
    overview: false,
    sessions: false,
    detail: false,
    report: false,
    metrics: false,
    history: false,
  })

  const errors = reactive({
    overview: null as string | null,
    sessions: null as string | null,
    detail: null as string | null,
    history: null as string | null,
    settings: null as string | null,
  })

  const runningSessions = computed(() => sessions.value.filter((session) => isRunning(session.status)))

  const recentSessions = computed(() =>
    sessions.value.filter((session) => !isRunning(session.status)).slice(0, 6),
  )

  const serviceOptions = computed(() => {
    const names = new Set(sessions.value.map((session) => session.serviceName))
    if (names.size === 0) names.add('target-app')
    return Array.from(names).sort()
  })

  function toMessage(error: unknown, fallback: string): string {
    return error instanceof Error && error.message ? error.message : fallback
  }

  async function fetchOverview(): Promise<void> {
    loading.overview = true
    errors.overview = null
    try {
      overview.value = await diagnosisApi.getOverview()
    } catch (error) {
      errors.overview = toMessage(error, '概览数据加载失败')
    } finally {
      loading.overview = false
    }
  }

  async function fetchSessions(): Promise<void> {
    loading.sessions = true
    errors.sessions = null
    try {
      sessions.value = await diagnosisApi.listSessions()
    } catch (error) {
      errors.sessions = toMessage(error, '诊断列表加载失败')
    } finally {
      loading.sessions = false
    }
  }

  async function fetchDetail(diagnosisId: string): Promise<void> {
    loading.detail = true
    errors.detail = null
    try {
      current.value = await diagnosisApi.getDetail(diagnosisId)
      report.value = current.value.report ?? null
    } catch (error) {
      current.value = null
      report.value = null
      errors.detail = toMessage(error, '诊断详情加载失败')
    } finally {
      loading.detail = false
    }
  }

  async function fetchReport(diagnosisId: string): Promise<void> {
    loading.report = true
    try {
      report.value = (await diagnosisApi.getReport(diagnosisId)) ?? null
    } catch {
      report.value = null
    } finally {
      loading.report = false
    }
  }

  async function fetchMetrics(diagnosisId: string): Promise<void> {
    loading.metrics = true
    try {
      metrics.value = await diagnosisApi.getMetrics(diagnosisId)
    } catch {
      metrics.value = []
    } finally {
      loading.metrics = false
    }
  }

  async function fetchHistory(query?: Partial<HistoryQuery>): Promise<void> {
    if (query) {
      const target = historyQuery as unknown as Record<string, unknown>
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined) target[key] = value
      })
    }
    loading.history = true
    errors.history = null
    try {
      history.value = await diagnosisApi.getHistory({ ...historyQuery })
    } catch (error) {
      errors.history = toMessage(error, '历史记录加载失败')
    } finally {
      loading.history = false
    }
  }

  async function triggerDiagnosis(payload: TriggerPayload): Promise<TriggerResult> {
    const result = await diagnosisApi.trigger(payload)
    await Promise.all([fetchSessions(), fetchOverview()])
    return result
  }

  function applyProgress(event: ProgressEvent): void {
    const patch = (session: DiagnosisSession): void => {
      session.status = event.status
      if (event.stage) session.stage = event.stage
      if (typeof event.progress === 'number') session.progress = event.progress
      if (event.status === 'completed' && !session.finishedAt) {
        session.finishedAt = event.timestamp
      }
    }
    sessions.value.forEach((session) => {
      if (session.diagnosisId === event.diagnosisId) patch(session)
    })
    if (current.value?.diagnosisId === event.diagnosisId) patch(current.value)
  }

  function resetHistoryQuery(): void {
    historyQuery.page = 1
    historyQuery.pageSize = 10
    historyQuery.serviceName = undefined
    historyQuery.status = undefined
    historyQuery.startTime = undefined
    historyQuery.endTime = undefined
  }

  return {
    sessions,
    overview,
    current,
    report,
    metrics,
    history,
    historyQuery,
    loading,
    errors,
    runningSessions,
    recentSessions,
    serviceOptions,
    fetchOverview,
    fetchSessions,
    fetchDetail,
    fetchReport,
    fetchMetrics,
    fetchHistory,
    triggerDiagnosis,
    applyProgress,
    resetHistoryQuery,
  }
})
