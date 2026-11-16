import type { ProgressEvent } from '@/types/diagnosis'
import { USE_MOCK, WS_BASE_URL } from '@/utils/env'
import { subscribeMockProgress } from '@/mock/ws'

export interface ProgressChannel {
  close(): void
}

const MAX_RETRIES = 3

function resolveWsUrl(diagnosisId: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const origin = WS_BASE_URL || `${protocol}://${window.location.host}`
  return `${origin.replace(/\/+$/, '')}/ws/diagnosis/${encodeURIComponent(diagnosisId)}`
}

/**
 * 订阅诊断进度：
 * - Mock 模式：本地每 2 秒推进一个阶段
 * - 真实模式：连接后端 WebSocket，断线后最多重连 3 次，组件可用 REST 补拉兜底
 */
export function subscribeDiagnosisProgress(
  diagnosisId: string,
  handler: (event: ProgressEvent) => void,
): ProgressChannel {
  if (USE_MOCK) {
    return subscribeMockProgress(diagnosisId, handler)
  }

  let socket: WebSocket | null = null
  let closed = false
  let retries = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined

  const connect = (): void => {
    socket = new WebSocket(resolveWsUrl(diagnosisId))
    socket.onopen = () => {
      retries = 0
    }
    socket.onmessage = (message) => {
      try {
        handler(JSON.parse(String(message.data)) as ProgressEvent)
      } catch {
        // 忽略无法解析的推送，等待下一次消息
      }
    }
    socket.onclose = () => {
      if (closed || retries >= MAX_RETRIES) return
      retries += 1
      reconnectTimer = setTimeout(connect, 1500 * retries)
    }
  }

  connect()

  return {
    close(): void {
      closed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      socket?.close()
      socket = null
    },
  }
}
