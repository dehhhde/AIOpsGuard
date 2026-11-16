const env = import.meta.env

/** 是否使用 Mock 数据，默认开启；真实联调时设置 VITE_USE_MOCK=false */
export const USE_MOCK = env.VITE_USE_MOCK !== 'false'

export const API_BASE_URL = env.VITE_API_BASE_URL || '/api'

/** 为空时 WebSocket 使用当前站点的 host */
export const WS_BASE_URL = env.VITE_WS_BASE_URL || ''

export const GRAFANA_BASE_URL = env.VITE_GRAFANA_BASE_URL || 'http://localhost:3000'
