import type { DiagnosisSession, DiagnosisStage, DiagnosisStatus } from '@/types/diagnosis'

export interface StageMeta {
  key: DiagnosisStage
  label: string
  description: string
}

export const DIAGNOSIS_STAGES: StageMeta[] = [
  { key: 'collecting', label: '数据采集', description: '拉取指标、日志与链路数据' },
  { key: 'metric', label: '指标分析', description: '识别资源与性能异常' },
  { key: 'log', label: '日志分析', description: '聚类错误日志与异常模式' },
  { key: 'trace', label: '链路分析', description: '定位耗时与错误传播路径' },
  { key: 'rca', label: '根因推理', description: '融合证据并排序根因' },
  { key: 'report', label: '报告生成', description: '输出结论与修复建议' },
]

export type TagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

export const STATUS_META: Record<DiagnosisStatus, { label: string; type: TagType }> = {
  pending: { label: '排队中', type: 'info' },
  collecting: { label: '数据采集中', type: 'warning' },
  analyzing: { label: '分析中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'danger' },
}

export const TRIGGER_LABELS: Record<string, string> = {
  manual: '手动触发',
  alert: '告警触发',
  schedule: '定时触发',
}

export function isRunning(status: DiagnosisStatus): boolean {
  return status === 'pending' || status === 'collecting' || status === 'analyzing'
}

export function isTerminal(status: DiagnosisStatus): boolean {
  return status === 'completed' || status === 'failed'
}

export function stageIndexOf(stage?: DiagnosisStage): number {
  if (!stage) return 0
  const index = DIAGNOSIS_STAGES.findIndex((item) => item.key === stage)
  return index < 0 ? 0 : index
}

/** el-steps 的激活索引：已完成全亮，失败停在当前阶段 */
export function activeStageIndex(session: DiagnosisSession): number {
  if (session.status === 'completed') return DIAGNOSIS_STAGES.length
  return stageIndexOf(session.stage)
}

export function isStageFinished(session: DiagnosisSession, index: number): boolean {
  if (session.status === 'completed') return true
  return index < stageIndexOf(session.stage)
}

export function isStageFailed(session: DiagnosisSession, index: number): boolean {
  return session.status === 'failed' && index === stageIndexOf(session.stage)
}
