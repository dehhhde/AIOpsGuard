import rawSessions from './data/sessions.json'
import { buildMetricGroups } from './metrics'
import type {
  DiagnosisSession,
  DiagnosisStage,
  DiagnosisStatus,
  HistoryQuery,
  MetricGroup,
  OverviewStats,
  PageResult,
  TriggerPayload,
  TriggerResult,
} from '@/types/diagnosis'
import type { SystemSettings } from '@/types/settings'
import { GRAFANA_BASE_URL } from '@/utils/env'
import { isRunning, isTerminal, stageIndexOf } from '@/utils/diagnosis'

const STAGE_FLOW: DiagnosisStage[] = ['collecting', 'metric', 'log', 'trace', 'rca', 'report']
const RUNNING_OFFSET_MS = 12 * 60 * 1000
const SESSION_HOUR_MS = 60 * 60 * 1000

const CLONE = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T

const delay = (ms = 260): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms))

function shiftIso(value: string, offset: number): string {
  return new Date(new Date(value).getTime() + offset).toISOString()
}

/** 把 Mock 时间整体平移到当前时间附近，保证工作台始终有“今日”数据 */
function shiftSession(session: DiagnosisSession, index: number): DiagnosisSession {
  const result = CLONE(session)
  const original = new Date(result.startedAt).getTime()
  if (Number.isNaN(original)) return result

  const targetStart = Date.now() - (isRunning(result.status) ? RUNNING_OFFSET_MS : (2 + index * 4) * SESSION_HOUR_MS)
  const offset = targetStart - original

  result.startedAt = shiftIso(result.startedAt, offset)
  if (result.finishedAt) result.finishedAt = shiftIso(result.finishedAt, offset)
  if (result.timeRange) {
    result.timeRange = {
      start: shiftIso(result.timeRange.start, offset),
      end: shiftIso(result.timeRange.end, offset),
    }
  }
  result.evidence = result.evidence.map((item) => ({
    ...item,
    timeRange: {
      start: shiftIso(item.timeRange.start, offset),
      end: shiftIso(item.timeRange.end, offset),
    },
  }))
  if (result.report) {
    result.report = { ...result.report, generatedAt: shiftIso(result.report.generatedAt, offset) }
  }
  return result
}

const sessions: DiagnosisSession[] = (rawSessions as unknown as DiagnosisSession[]).map((item, index) =>
  shiftSession(item, index),
)

const reportTemplateSession = sessions.find((session) => session.report)
const reportTemplate = reportTemplateSession?.report

function sortByStartedAtDesc(items: DiagnosisSession[]): DiagnosisSession[] {
  return [...items].sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
}

function findSession(diagnosisId: string): DiagnosisSession | undefined {
  return sessions.find((session) => session.diagnosisId === diagnosisId)
}

function completeSession(session: DiagnosisSession): void {
  session.status = 'completed'
  session.stage = 'report'
  session.progress = 100
  session.finishedAt = new Date().toISOString()

  if (session.rootCauses.length === 0 && reportTemplateSession) {
    session.rootCauses = CLONE(reportTemplateSession.rootCauses)
    session.evidence = CLONE(reportTemplateSession.evidence).map((item) => ({
      ...item,
      timeRange: session.timeRange ? { ...session.timeRange } : item.timeRange,
    }))
  }
  if (!session.report && reportTemplate) {
    session.report = {
      ...CLONE(reportTemplate),
      diagnosisId: session.diagnosisId,
      generatedAt: session.finishedAt,
    }
  }
}

/** 由 Mock WebSocket 驱动，每次推进一个阶段 */
export function tickSession(diagnosisId: string): DiagnosisSession | null {
  const session = findSession(diagnosisId)
  if (!session || isTerminal(session.status)) return null

  const currentIndex = stageIndexOf(session.stage)
  if (session.status === 'pending') {
    session.status = 'collecting'
    session.stage = 'collecting'
    session.progress = 8
  } else if (currentIndex >= STAGE_FLOW.length - 1) {
    completeSession(session)
  } else {
    const nextIndex = currentIndex + 1
    session.stage = STAGE_FLOW[nextIndex]
    session.status = session.stage === 'collecting' ? 'collecting' : 'analyzing'
    session.progress = Math.min(99, 8 + Math.round((nextIndex / STAGE_FLOW.length) * 92))
  }
  return session
}

export function getSessionSnapshot(diagnosisId: string): DiagnosisSession | null {
  const session = findSession(diagnosisId)
  return session ? CLONE(session) : null
}

function buildTriggerId(): string {
  const now = new Date()
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `diag-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(
    now.getMinutes(),
  )}${pad(now.getSeconds())}`
}

const settings: SystemSettings = {
  dataSources: [
    { name: 'Prometheus', kind: 'metric', url: 'http://localhost:9090', status: 'reserved', note: '指标采集与查询' },
    { name: 'Loki', kind: 'log', url: 'http://localhost:3100', status: 'reserved', note: '日志检索与聚类' },
    { name: 'Tempo', kind: 'trace', url: 'http://localhost:3200', status: 'reserved', note: '链路检索与耗时分析' },
    { name: 'Grafana', kind: 'visual', url: GRAFANA_BASE_URL, status: 'reserved', note: '原始时序与检索主展示位' },
    {
      name: 'PostgreSQL',
      kind: 'storage',
      url: 'postgresql://localhost:5432/aiops',
      status: 'reserved',
      note: '诊断报告、根因、证据链存储',
    },
    { name: 'Redis', kind: 'storage', url: 'redis://localhost:6379/0', status: 'reserved', note: '诊断状态与缓存' },
    { name: 'Kafka', kind: 'messaging', url: 'localhost:9092', status: 'reserved', note: '告警与问题事件接入' },
    {
      name: 'LLM',
      kind: 'llm',
      url: 'https://dashscope.aliyuncs.com',
      status: 'reserved',
      note: '根因说明与修复建议生成',
    },
  ],
  switches: [
    {
      key: 'prometheus',
      name: 'Prometheus 指标采集',
      enabled: true,
      description: '按诊断时间窗拉取指标并降采样到 100~300 点',
    },
    {
      key: 'trace',
      name: 'Trace 链路分析',
      enabled: true,
      description: '拉取 Tempo 链路，定位慢调用与错误传播',
    },
    {
      key: 'kafka',
      name: 'Kafka 事件接入',
      enabled: false,
      description: '接收告警与问题事件，未配置时自动关闭，不影响启动',
    },
    {
      key: 'llm',
      name: 'LLM 增强分析',
      enabled: false,
      description: '调用大模型生成根因解释，未配置时使用规则结论',
    },
  ],
  llmProvider: 'Qwen (DashScope)',
  updatedAt: new Date().toISOString(),
}

export const mockApi = {
  async listSessions(): Promise<DiagnosisSession[]> {
    await delay()
    return sortByStartedAtDesc(sessions).map(CLONE)
  },

  async getOverview(): Promise<OverviewStats> {
    await delay(180)
    const terminal = sessions.filter((session) => isTerminal(session.status))
    const completed = terminal.filter((session) => session.status === 'completed')
    const durations = terminal
      .map((session) => {
        if (!session.finishedAt) return undefined
        return new Date(session.finishedAt).getTime() - new Date(session.startedAt).getTime()
      })
      .filter((value): value is number => typeof value === 'number' && value > 0)
    const avgDurationMs = durations.length
      ? Math.round(durations.reduce((sum, value) => sum + value, 0) / durations.length)
      : 0

    return {
      totalToday: sessions.length,
      successRate: terminal.length ? completed.length / terminal.length : 0,
      avgDurationMs,
      runningCount: sessions.filter((session) => isRunning(session.status)).length,
    }
  },

  async getDetail(diagnosisId: string): Promise<DiagnosisSession> {
    await delay()
    const session = findSession(diagnosisId)
    if (!session) {
      throw new Error('诊断会话不存在或已过期')
    }
    return CLONE(session)
  },

  async getReport(diagnosisId: string): Promise<DiagnosisSession['report']> {
    await delay(200)
    const session = findSession(diagnosisId)
    if (!session) {
      throw new Error('诊断会话不存在或已过期')
    }
    if (session.report) return CLONE(session.report)
    if (session.status === 'completed' && reportTemplate) {
      return {
        ...CLONE(reportTemplate),
        diagnosisId,
        generatedAt: session.finishedAt ?? reportTemplate.generatedAt,
      }
    }
    return undefined
  },

  async getHistory(query: HistoryQuery): Promise<PageResult<DiagnosisSession>> {
    await delay()
    const start = query.startTime ? new Date(query.startTime).getTime() : undefined
    const end = query.endTime ? new Date(query.endTime).getTime() : undefined

    const filtered = sortByStartedAtDesc(sessions).filter((session) => {
      if (query.serviceName && session.serviceName !== query.serviceName) return false
      if (query.status && session.status !== query.status) return false
      const startedAt = new Date(session.startedAt).getTime()
      if (start !== undefined && startedAt < start) return false
      if (end !== undefined && startedAt > end) return false
      return true
    })

    const page = Math.max(1, query.page)
    const pageSize = Math.max(1, query.pageSize)
    const offset = (page - 1) * pageSize
    return {
      items: filtered.slice(offset, offset + pageSize).map(CLONE),
      total: filtered.length,
      page,
      pageSize,
    }
  },

  async trigger(payload: TriggerPayload): Promise<TriggerResult> {
    await delay(400)
    if (!payload.targetService) {
      throw new Error('请选择要诊断的服务')
    }
    const diagnosisId = buildTriggerId()
    const session: DiagnosisSession = {
      diagnosisId,
      serviceName: payload.targetService,
      serviceInstance: `${payload.targetService}-mock-1:8080`,
      status: 'pending' as DiagnosisStatus,
      stage: 'collecting',
      progress: 0,
      startedAt: new Date().toISOString(),
      triggerType: 'manual',
      timeRange: { start: payload.startTime, end: payload.endTime },
      rootCauses: [],
      evidence: [],
    }
    sessions.unshift(session)
    return {
      diagnosisId,
      status: 'processing',
      message: '诊断任务已创建，正在采集数据',
    }
  },

  async getMetrics(diagnosisId: string): Promise<MetricGroup[]> {
    await delay(220)
    const session = findSession(diagnosisId)
    if (!session) {
      throw new Error('诊断会话不存在或已过期')
    }
    return buildMetricGroups(session)
  },

  async getSettings(): Promise<SystemSettings> {
    await delay(160)
    return CLONE(settings)
  },
}
