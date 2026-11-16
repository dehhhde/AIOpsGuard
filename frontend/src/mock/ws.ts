import type { ProgressEvent, ProgressEventType } from '@/types/diagnosis'
import { isTerminal } from '@/utils/diagnosis'
import { getSessionSnapshot, tickSession } from './index'

export interface ProgressSubscription {
  close(): void
}

type ProgressHandler = (event: ProgressEvent) => void

const timers = new Map<string, ReturnType<typeof setInterval>>()
const listeners = new Map<string, Set<ProgressHandler>>()

function stopTimer(diagnosisId: string): void {
  const timer = timers.get(diagnosisId)
  if (timer) {
    clearInterval(timer)
    timers.delete(diagnosisId)
  }
}

function emit(diagnosisId: string): void {
  const session = getSessionSnapshot(diagnosisId)
  if (!session) return

  const eventType: ProgressEventType =
    session.status === 'completed'
      ? 'diagnosis.completed'
      : session.status === 'failed'
        ? 'diagnosis.failed'
        : 'diagnosis.progress'
  const event: ProgressEvent = {
    event: eventType,
    diagnosisId,
    status: session.status,
    stage: session.stage,
    progress: session.progress,
    timestamp: new Date().toISOString(),
  }
  listeners.get(diagnosisId)?.forEach((handler) => handler(event))
  if (isTerminal(session.status)) {
    stopTimer(diagnosisId)
  }
}

function startTimer(diagnosisId: string): void {
  if (timers.has(diagnosisId)) return
  const timer = setInterval(() => {
    const session = tickSession(diagnosisId)
    if (!session) {
      stopTimer(diagnosisId)
      return
    }
    emit(diagnosisId)
  }, 2000)
  timers.set(diagnosisId, timer)
}

/** Mock 进度通道：每 2 秒推进一个阶段，订阅后立即回放当前状态 */
export function subscribeMockProgress(
  diagnosisId: string,
  handler: ProgressHandler,
): ProgressSubscription {
  const handlers = listeners.get(diagnosisId) ?? new Set<ProgressHandler>()
  handlers.add(handler)
  listeners.set(diagnosisId, handlers)

  const snapshot = getSessionSnapshot(diagnosisId)
  if (snapshot && !isTerminal(snapshot.status)) {
    startTimer(diagnosisId)
  }
  emit(diagnosisId)

  return {
    close(): void {
      handlers.delete(handler)
      if (handlers.size === 0) {
        listeners.delete(diagnosisId)
        stopTimer(diagnosisId)
      }
    },
  }
}
