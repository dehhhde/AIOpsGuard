<template>
  <el-card shadow="never" class="evidence-card">
    <div class="evidence-head">
      <div class="tag-gap">
        <el-tag :type="typeMeta.type" size="small">{{ typeMeta.label }}</el-tag>
        <span class="evidence-id mono">{{ evidence.id }}</span>
      </div>
      <span class="time-range mono">{{ formatRange(evidence.timeRange) }}</span>
    </div>

    <p class="summary">{{ evidence.summary }}</p>

    <div class="source">
      <span class="muted">来源：</span>
      <span class="mono">{{ evidence.source }}</span>
    </div>

    <div class="footer">
      <el-button link type="primary" @click="expanded = !expanded">
        {{ expanded ? '收起详情' : '展开详情' }}
      </el-button>
      <el-button link type="primary" @click="openGrafana">查看原始数据</el-button>
    </div>

    <div v-if="expanded" class="detail">
      <el-descriptions :column="1" size="small" border>
        <el-descriptions-item label="置信度影响">{{ weight }}</el-descriptions-item>
        <el-descriptions-item label="目标实例">{{ evidence.instance || '-' }}</el-descriptions-item>
        <el-descriptions-item label="指标 / 查询">
          {{ evidence.metricName || evidence.source }}
        </el-descriptions-item>
        <el-descriptions-item v-for="entry in detailEntries" :key="entry.key" :label="entry.key">
          {{ entry.value }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Evidence, EvidenceType } from '@/types/diagnosis'
import { formatRange } from '@/utils/time'
import { buildEvidenceGrafanaUrl } from '@/utils/grafana'
import type { TagType } from '@/utils/diagnosis'

const props = defineProps<{
  evidence: Evidence
  serviceName: string
}>()

const expanded = ref(false)

const TYPE_META: Record<EvidenceType, { label: string; type: TagType }> = {
  METRIC: { label: '指标证据', type: 'primary' },
  LOG: { label: '日志证据', type: 'warning' },
  TRACE: { label: '链路证据', type: 'success' },
}

const typeMeta = computed(() => TYPE_META[props.evidence.type] ?? TYPE_META.METRIC)

const weight = computed(() => {
  const value = props.evidence.detail.weight
  return typeof value === 'number' ? value.toFixed(2) : '—'
})

const detailEntries = computed(() =>
  Object.entries(props.evidence.detail)
    .filter(([key, value]) => key !== 'weight' && value !== null && value !== undefined)
    .map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value),
    })),
)

function openGrafana(): void {
  window.open(buildEvidenceGrafanaUrl(props.serviceName, props.evidence), '_blank', 'noopener')
}
</script>

<style scoped>
.evidence-card {
  border: 1px solid #e5e8ef;
}

.evidence-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.evidence-id {
  color: #7a889c;
}

.time-range {
  color: #7a889c;
}

.summary {
  margin: 0 0 8px;
  line-height: 1.7;
}

.source {
  font-size: 12px;
  line-height: 1.6;
  word-break: break-all;
}

.footer {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.detail {
  margin-top: 12px;
}
</style>
