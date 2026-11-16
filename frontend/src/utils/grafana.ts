import type { Evidence, EvidenceType } from '@/types/diagnosis'
import { GRAFANA_BASE_URL } from '@/utils/env'

export interface GrafanaLinkOptions {
  service: string
  instance?: string
  from: string
  to: string
  dashboardUid?: string
  panelId?: number
}

const DASHBOARD_BY_TYPE: Record<EvidenceType, string> = {
  METRIC: 'aiops-target-app-jvm',
  LOG: 'aiops-target-app-logs',
  TRACE: 'aiops-target-app-traces',
}

export function dashboardUidForEvidence(type: EvidenceType): string {
  return DASHBOARD_BY_TYPE[type]
}

function toEpochMs(value: string): string {
  const timestamp = new Date(value).getTime()
  return Number.isNaN(timestamp) ? '' : String(timestamp)
}

export function buildGrafanaUrl(options: GrafanaLinkOptions): string {
  const base = GRAFANA_BASE_URL.replace(/\/+$/, '')
  const dashboardUid = options.dashboardUid || 'aiops-target-app-jvm'
  const params = new URLSearchParams()
  params.set('var-service', options.service)
  if (options.instance) params.set('var-instance', options.instance)
  const from = toEpochMs(options.from)
  const to = toEpochMs(options.to)
  if (from) params.set('from', from)
  if (to) params.set('to', to)
  if (options.panelId) params.set('viewPanel', String(options.panelId))
  params.set('kiosk', '')
  return `${base}/d/${dashboardUid}/aiops?${params.toString()}`
}

export function buildEvidenceGrafanaUrl(serviceName: string, evidence: Evidence): string {
  return buildGrafanaUrl({
    service: serviceName,
    instance: evidence.instance,
    from: evidence.timeRange.start,
    to: evidence.timeRange.end,
    dashboardUid: evidence.dashboardUid || dashboardUidForEvidence(evidence.type),
    panelId: evidence.panelId,
  })
}
