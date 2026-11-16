<template>
  <BaseChart :option="option" :height="height" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import BaseChart from './BaseChart.vue'
import type { MetricGroup } from '@/types/diagnosis'
import { formatTime } from '@/utils/time'

const props = withDefaults(
  defineProps<{
    group: MetricGroup
    height?: string
  }>(),
  { height: '280px' },
)

const COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c']

const option = computed<EChartsOption>(() => {
  const firstSeries = props.group.series[0]
  const timestamps = firstSeries?.points.map((point) => formatTime(point.timestamp)) ?? []
  return {
    color: COLORS,
    tooltip: { trigger: 'axis' },
    legend: { top: 0, icon: 'roundRect', itemHeight: 8 },
    grid: { left: 56, right: 24, top: 40, bottom: 36 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timestamps,
      axisLabel: { color: '#8a97ab', hideOverlap: true },
      axisLine: { lineStyle: { color: '#e5e8ef' } },
    },
    yAxis: {
      type: 'value',
      name: firstSeries?.unit ?? '',
      axisLabel: { color: '#8a97ab' },
      splitLine: { lineStyle: { color: '#eef1f6' } },
    },
    series: props.group.series.map((series) => ({
      name: series.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2 },
      data: series.points.map((point) => point.value),
    })),
  }
})
</script>
