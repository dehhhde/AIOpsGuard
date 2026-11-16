<template>
  <div class="root-cause-list">
    <el-empty v-if="sorted.length === 0" description="暂无根因结论" :image-size="60" />
    <div v-for="item in sorted" :key="item.rank" class="root-cause-item">
      <div class="root-cause-head">
        <span class="rank">#{{ item.rank }}</span>
        <span class="cause">{{ item.cause }}</span>
        <span class="confidence" :style="{ color: colorOf(item.confidence) }">
          {{ toPercent(item.confidence) }}%
        </span>
      </div>
      <el-progress
        :percentage="toPercent(item.confidence)"
        :color="colorOf(item.confidence)"
        :stroke-width="8"
        :show-text="false"
      />
      <div class="meta">
        <span>置信度 {{ toPercent(item.confidence) }}%</span>
        <span>证据 {{ item.evidenceIds.length }} 条</span>
      </div>
      <ul v-if="item.recommendations && item.recommendations.length" class="recommendations">
        <li v-for="(recommendation, index) in item.recommendations" :key="index">
          {{ recommendation }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RootCause } from '@/types/diagnosis'

const props = defineProps<{
  rootCauses: RootCause[]
}>()

const sorted = computed(() => [...props.rootCauses].sort((a, b) => b.confidence - a.confidence))

function toPercent(value: number): number {
  return Math.round(Math.min(1, Math.max(0, value)) * 100)
}

function colorOf(value: number): string {
  if (value >= 0.8) return '#f56c6c'
  if (value >= 0.5) return '#e6a23c'
  return '#909399'
}
</script>

<style scoped>
.root-cause-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.root-cause-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}

.rank {
  color: #409eff;
  font-weight: 600;
  flex-shrink: 0;
}

.cause {
  flex: 1;
  line-height: 1.6;
}

.confidence {
  font-weight: 600;
  flex-shrink: 0;
}

.meta {
  display: flex;
  gap: 18px;
  margin-top: 6px;
  color: #7a889c;
  font-size: 12px;
}

.recommendations {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #5c6b82;
  font-size: 13px;
  line-height: 1.7;
}
</style>
