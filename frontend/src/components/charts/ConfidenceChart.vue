<template>
  <BaseChart :option="option" height="240px" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseChart from './BaseChart.vue'
import type { RootCause } from '@/types/diagnosis'

const props = defineProps<{
  rootCauses: RootCause[]
}>()

const COLORS = ['#f56c6c', '#e6a23c', '#909399']

function colorOf(confidence: number): string {
  if (confidence >= 0.8) return COLORS[0]
  if (confidence >= 0.5) return COLORS[1]
  return COLORS[2]
}

const option = computed<EChartsOption>(() => {
  const sorted = [...props.rootCauses].sort((a, b) => b.confidence - a.confidence)
  return {
    grid: { left: 56, right: 48, top: 16, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => `${Math.round(Number(value) * 100)}%`,
    },
    xAxis: {
      type: 'value',
      max: 1,
      axisLabel: { formatter: (value: number) => `${Math.round(value * 100)}%`, color: '#8a97ab' },
      splitLine: { lineStyle: { color: '#eef1f6' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((item) => `#${item.rank} 根因`),
      axisLabel: { color: '#5c6b82' },
      axisLine: { lineStyle: { color: '#e5e8ef' } },
    },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        data: sorted.map((item) => ({
          value: item.confidence,
          itemStyle: { color: colorOf(item.confidence), borderRadius: [0, 4, 4, 0] },
        })),
        label: {
          show: true,
          position: 'right',
          formatter: (params) => `${Math.round(Number(params.value) * 100)}%`,
          color: '#5c6b82',
        },
      },
    ],
  }
})
</script>
