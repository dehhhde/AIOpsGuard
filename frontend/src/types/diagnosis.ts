export type DiagnosisStatus = 'pending' | 'collecting' | 'analyzing' | 'completed' | 'failed'

export type DiagnosisTriggerType = 'manual' | 'alert' | 'schedule'

/** 诊断阶段，与后端 LangGraph 节点顺序保持一致 */
export type DiagnosisStage = 'collecting' | 'metric' | 'log' | 'trace' | 'rca' | 'report'

export type EvidenceType = 'METRIC' | 'LOG' | 'TRACE'

export interface TimeRange {
  start: string
  end: string
}

export interface RootCause {
  rank: number
  cause: string
  confidence: number
  evidenceIds: string[]
  recommendations?: string[]
}

export interface Evidence {
  id: string
  type: EvidenceType
  summary: string
  source: string
  timeRange: TimeRange
  detail: Record<string, unknown>
  /** 指标名，用于生成 Grafana 深链 */
  metricName?: string
  /** 实例地址，对应 Grafana 的 var-instance */
  instance?: string
  /** 目标 Dashboard UID，缺省时按证据类型推导 */
  dashboardUid?: string
  /** 目标 Panel ID，对应 Grafana 的 viewPanel */
  panelId?: number
}

export interface ReportSection {
  title: string
  content: string
  collapsed?: boolean
}

export interface DiagnosisReport {
  diagnosisId: string
  generatedAt: string
  summary: string
  sections: ReportSection[]
  recommendations: string[]
}

export interface DiagnosisSession {
  diagnosisId: string
  serviceName: string
  serviceInstance?: string
  status: DiagnosisStatus
  stage?: DiagnosisStage
  progress?: number
  startedAt: string
  finishedAt?: string
  triggerType?: DiagnosisTriggerType
  timeRange?: TimeRange
  rootCauses: RootCause[]
  evidence: Evidence[]
  report?: DiagnosisReport
}

export interface MetricPoint {
  timestamp: string
  value: number
}

export interface MetricSeries {
  name: string
  unit: string
  points: MetricPoint[]
}

export type MetricGroupKey = 'jvm' | 'http' | 'pool'

export interface MetricGroup {
  key: MetricGroupKey
  title: string
  description: string
  series: MetricSeries[]
}

export interface OverviewStats {
  totalToday: number
  successRate: number
  avgDurationMs: number
  runningCount: number
}

export interface HistoryQuery {
  page: number
  pageSize: number
  serviceName?: string
  status?: DiagnosisStatus
  startTime?: string
  endTime?: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface TriggerPayload {
  targetService: string
  startTime: string
  endTime: string
}

export interface TriggerResult {
  diagnosisId: string
  status: string
  message: string
}

export type ProgressEventType = 'diagnosis.progress' | 'diagnosis.completed' | 'diagnosis.failed'

export interface ProgressEvent {
  event: ProgressEventType
  diagnosisId: string
  status: DiagnosisStatus
  stage?: DiagnosisStage
  progress?: number
  timestamp: string
}
