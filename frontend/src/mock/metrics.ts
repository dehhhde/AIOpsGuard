import type { DiagnosisSession, MetricGroup, MetricPoint, MetricSeries } from '@/types/diagnosis'

const POINT_COUNT = 150

function makeRandom(seedText: string): () => number {
  let seed = Array.from(seedText).reduce((acc, char) => acc + char.charCodeAt(0), 7)
  return () => {
    seed = (seed * 9301 + 49297) % 233280
    return seed / 233280
  }
}

function makeSeries(
  name: string,
  unit: string,
  startMs: number,
  stepMs: number,
  count: number,
  generator: (index: number, random: () => number) => number,
): MetricSeries {
  const random = makeRandom(name)
  const points: MetricPoint[] = []
  for (let index = 0; index < count; index += 1) {
    const value = generator(index, random)
    points.push({
      timestamp: new Date(startMs + index * stepMs).toISOString(),
      value: Math.round(value * 100) / 100,
    })
  }
  return { name, unit, points }
}

/** 按会话时间窗生成三类 Mock 指标，点数 150，符合后端降采样约定 */
export function buildMetricGroups(session: DiagnosisSession): MetricGroup[] {
  const startMs = session.timeRange
    ? new Date(session.timeRange.start).getTime()
    : Date.now() - 60 * 60 * 1000
  const endMs = session.timeRange ? new Date(session.timeRange.end).getTime() : Date.now()
  const safeStart = Number.isNaN(startMs) ? Date.now() - 60 * 60 * 1000 : startMs
  const safeEnd = Number.isNaN(endMs) || endMs <= safeStart ? safeStart + 60 * 60 * 1000 : endMs
  const step = Math.max(1000, Math.floor((safeEnd - safeStart) / POINT_COUNT))

  return [
    {
      key: 'jvm',
      title: 'JVM 内存',
      description: '堆内存持续上升是本次诊断的核心指标证据',
      series: [
        makeSeries('堆内存使用', 'MB', safeStart, step, POINT_COUNT, (index, random) => {
          const growth = (index / POINT_COUNT) * 1150
          const surge = index > POINT_COUNT * 0.4 ? (index - POINT_COUNT * 0.4) * 7 : 0
          return 620 + growth + surge + random() * 45
        }),
        makeSeries('非堆内存使用', 'MB', safeStart, step, POINT_COUNT, (_index, random) => {
          return 180 + random() * 35
        }),
      ],
    },
    {
      key: 'http',
      title: 'HTTP 延迟',
      description: '订单查询接口 P99 在故障窗口内明显劣化',
      series: [
        makeSeries('P50 延迟', 'ms', safeStart, step, POINT_COUNT, (_index, random) => 120 + random() * 40),
        makeSeries('P95 延迟', 'ms', safeStart, step, POINT_COUNT, (index, random) => {
          return 280 + Math.sin(index / 12) * 60 + random() * 80
        }),
        makeSeries('P99 延迟', 'ms', safeStart, step, POINT_COUNT, (index, random) => {
          const deterioration = index > POINT_COUNT * 0.45 ? (index - POINT_COUNT * 0.45) * 12 : 0
          return 320 + deterioration + random() * 120
        }),
      ],
    },
    {
      key: 'pool',
      title: 'HikariCP 连接池',
      description: 'pending 连接堆积，说明数据库等待放大接口耗时',
      series: [
        makeSeries('活跃连接', '个', safeStart, step, POINT_COUNT, (index, random) => {
          return 4 + Math.min(6, index / POINT_COUNT) * 5 + random() * 2
        }),
        makeSeries('空闲连接', '个', safeStart, step, POINT_COUNT, (index, random) => {
          return Math.max(1, 5 - (index / POINT_COUNT) * 4 + random() * 2)
        }),
        makeSeries('等待连接', '个', safeStart, step, POINT_COUNT, (index, random) => {
          return index > POINT_COUNT * 0.35 ? random() * 18 : random() * 2
        }),
      ],
    },
  ]
}
