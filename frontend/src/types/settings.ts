export type DataSourceStatus = 'reserved' | 'partial' | 'configured'

export type DataSourceKind = 'metric' | 'log' | 'trace' | 'visual' | 'storage' | 'messaging' | 'llm'

export interface DataSourceInfo {
  name: string
  kind: DataSourceKind
  url: string
  status: DataSourceStatus
  note?: string
}

export interface FeatureSwitch {
  key: string
  name: string
  enabled: boolean
  description: string
}

export interface SystemSettings {
  dataSources: DataSourceInfo[]
  switches: FeatureSwitch[]
  llmProvider: string
  updatedAt: string
}
