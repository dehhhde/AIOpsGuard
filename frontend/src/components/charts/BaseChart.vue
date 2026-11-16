<template>
  <div ref="container" class="base-chart" :style="{ height }"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

const props = withDefaults(
  defineProps<{
    option: EChartsOption
    height?: string
  }>(),
  { height: '280px' },
)

const container = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let observer: ResizeObserver | null = null

onMounted(() => {
  if (!container.value) return
  const element = container.value
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(element)
  // 等一帧，确保容器已完成布局再初始化，避免拿到 0 宽高
  requestAnimationFrame(() => {
    if (!element.isConnected) return
    chart = echarts.init(element)
    chart.setOption(props.option)
  })
})

watch(
  () => props.option,
  (option) => {
    chart?.setOption(option, true)
  },
  { deep: true },
)

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.base-chart {
  width: 100%;
}
</style>
