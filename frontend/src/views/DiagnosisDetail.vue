<template>
  <div class="page">
    <div class="page-header">
      <div class="title-wrap">
        <el-button link @click="router.push('/dashboard')">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回工作台</span>
        </el-button>
        <h2 v-if="session" class="page-title">
          {{ session.serviceName }}
          <StatusTag :status="session.status" class="title-tag" />
        </h2>
        <p v-if="session" class="page-subtitle mono">{{ session.diagnosisId }}</p>
      </div>
      <div class="tag-gap">
        <el-button :loading="store.loading.detail" @click="load">刷新</el-button>
        <el-button type="primary" plain @click="openGrafana">在 Grafana 查看</el-button>
      </div>
    </div>

    <StatePanel
      v-if="store.errors.detail"
      state="error"
      :description="store.errors.detail"
      @retry="load"
    />
    <StatePanel v-else-if="store.loading.detail && !session" state="loading" />
    <StatePanel v-else-if="!session" state="empty" description="未找到该诊断会话" />

    <template v-else>
      <div class="card">
        <el-descriptions :column="3" size="small" border>
          <el-descriptions-item label="诊断状态">
            <StatusTag :status="session.status" />
          </el-descriptions-item>
          <el-descriptions-item label="触发方式">
            {{ TRIGGER_LABELS[session.triggerType ?? ''] ?? '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="耗时">{{ duration }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ formatDateTime(session.startedAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="结束时间">
            {{ formatDateTime(session.finishedAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="目标实例">
            {{ session.serviceInstance ?? '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="诊断时间窗" :span="3">
            {{ formatRange(session.timeRange) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="running" class="running-progress">
          <div class="progress-head">
            <span>诊断进行中：{{ currentStageLabel }}</span>
            <span class="mono">{{ session.progress ?? 0 }}%</span>
          </div>
          <el-progress :percentage="session.progress ?? 0" :stroke-width="10" striped striped-flow />
          <p class="muted progress-hint">进度通过 WebSocket 自动推送，无需手动刷新</p>
        </div>
      </div>

      <div class="card">
        <div class="section-title">
          <h3>阶段时间线</h3>
          <span v-if="running" class="muted">当前：{{ currentStageLabel }}</span>
        </div>
        <StageTimeline :session="session" />
      </div>

      <el-alert
        v-if="session.status === 'failed'"
        type="error"
        :closable="false"
        show-icon
        title="诊断执行失败"
        :description="`在「${currentStageLabel}」阶段中断，请检查数据源可用性后重新触发诊断。`"
      />

      <template v-if="session.status === 'completed'">
        <div class="result-grid">
          <div class="card">
            <div class="section-title">
              <h3>根因排行</h3>
              <span class="muted">按置信度排序</span>
            </div>
            <RootCauseList :root-causes="session.rootCauses" />
          </div>
          <div class="card">
            <div class="section-title">
              <h3>置信度分布</h3>
            </div>
            <ConfidenceChart :root-causes="session.rootCauses" />
          </div>
        </div>

        <div class="card">
          <div class="section-title">
            <h3>证据链</h3>
            <span class="muted">共 {{ session.evidence.length }} 条，可跳转 Grafana 查看原始数据</span>
          </div>
          <el-empty v-if="!session.evidence.length" description="该诊断没有采集到证据" />
          <div v-for="group in evidenceGroups" :key="group.key" class="evidence-group">
            <h4 class="evidence-group-title">{{ group.label }}（{{ group.items.length }}）</h4>
            <EvidenceCard
              v-for="evidence in group.items"
              :key="evidence.id"
              :evidence="evidence"
              :service-name="session.serviceName"
            />
          </div>
        </div>

        <div class="card">
          <div class="section-title">
            <h3>指标摘要</h3>
            <span class="muted">原始曲线请在 Grafana 查看</span>
          </div>
          <StatePanel v-if="store.loading.metrics && !store.metrics.length" state="loading" />
          <StatePanel v-else-if="!store.metrics.length" state="empty" description="暂无指标摘要" />
          <el-tabs v-else v-model="activeMetric">
            <el-tab-pane
              v-for="group in store.metrics"
              :key="group.key"
              :label="group.title"
              :name="group.key"
            >
              <p class="muted metric-desc">{{ group.description }}</p>
              <MetricChart v-if="currentMetricGroup" :group="currentMetricGroup" />
            </el-tab-pane>
          </el-tabs>
        </div>

        <div class="card">
          <div class="section-title">
            <h3>诊断报告</h3>
            <span v-if="report" class="muted">生成于 {{ formatDateTime(report.generatedAt) }}</span>
          </div>
          <StatePanel v-if="store.loading.report && !report" state="loading" />
          <ReportView v-else-if="report" :report="report" />
          <StatePanel v-else state="empty" description="报告尚未生成" />
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import StatusTag from '@/components/StatusTag.vue'
import StageTimeline from '@/components/StageTimeline.vue'
import RootCauseList from '@/components/RootCauseList.vue'
import ConfidenceChart from '@/components/charts/ConfidenceChart.vue'
import EvidenceCard from '@/components/EvidenceCard.vue'
import MetricChart from '@/components/charts/MetricChart.vue'
import ReportView from '@/components/ReportView.vue'
import StatePanel from '@/components/StatePanel.vue'
import type { EvidenceType, MetricGroupKey } from '@/types/diagnosis'
import { useDiagnosisStore } from '@/stores/diagnosis'
import { subscribeDiagnosisProgress, type ProgressChannel } from '@/api/ws'
import { DIAGNOSIS_STAGES, TRIGGER_LABELS, isRunning, stageIndexOf } from '@/utils/diagnosis'
import { formatDateTime, formatDuration, formatRange, sessionDuration } from '@/utils/time'
import { buildGrafanaUrl } from '@/utils/grafana'

const route = useRoute()
const router = useRouter()
const store = useDiagnosisStore()

const activeMetric = ref<MetricGroupKey>('jvm')
let channel: ProgressChannel | null = null

const diagnosisId = computed(() => String(route.params.id ?? ''))
const session = computed(() => store.current)
const report = computed(() => store.report ?? session.value?.report ?? null)
const running = computed(() => (session.value ? isRunning(session.value.status) : false))

const duration = computed(() =>
  session.value
    ? formatDuration(sessionDuration(session.value.startedAt, session.value.finishedAt))
    : '-',
)

const currentStageLabel = computed(() => {
  if (!session.value) return '-'
  if (session.value.status === 'completed') return '已完成'
  if (session.value.status === 'failed') {
    return DIAGNOSIS_STAGES[stageIndexOf(session.value.stage)]?.label ?? '执行中'
  }
  return DIAGNOSIS_STAGES.find((stage) => stage.key === session.value?.stage)?.label ?? '等待调度'
})

const currentMetricGroup = computed(
  () => store.metrics.find((group) => group.key === activeMetric.value) ?? store.metrics[0],
)

const EVIDENCE_GROUPS: { key: EvidenceType; label: string }[] = [
  { key: 'METRIC', label: '指标证据' },
  { key: 'LOG', label: '日志证据' },
  { key: 'TRACE', label: '链路证据' },
]

const evidenceGroups = computed(() =>
  EVIDENCE_GROUPS.map((group) => ({
    ...group,
    items: (session.value?.evidence ?? []).filter((evidence) => evidence.type === group.key),
  })).filter((group) => group.items.length > 0),
)

function closeChannel(): void {
  channel?.close()
  channel = null
}

function subscribe(): void {
  if (!session.value) return
  channel = subscribeDiagnosisProgress(session.value.diagnosisId, (event) => {
    store.applyProgress(event)
    if (event.event === 'diagnosis.completed' || event.event === 'diagnosis.failed') {
      closeChannel()
      void refreshAfterFinish()
    }
  })
}

async function refreshAfterFinish(): Promise<void> {
  await store.fetchDetail(diagnosisId.value)
  await store.fetchReport(diagnosisId.value)
  void store.fetchMetrics(diagnosisId.value)
  void store.fetchOverview()
  void store.fetchSessions()
}

async function load(): Promise<void> {
  closeChannel()
  if (!diagnosisId.value) return
  await store.fetchDetail(diagnosisId.value)
  if (!session.value) return
  void store.fetchMetrics(diagnosisId.value)
  if (session.value.status === 'completed') {
    await store.fetchReport(diagnosisId.value)
  }
  if (running.value) subscribe()
}

function openGrafana(): void {
  if (!session.value) return
  const timeRange = session.value.timeRange
  window.open(
    buildGrafanaUrl({
      service: session.value.serviceName,
      instance: session.value.serviceInstance,
      from: timeRange?.start ?? session.value.startedAt,
      to: timeRange?.end ?? session.value.finishedAt ?? new Date().toISOString(),
    }),
    '_blank',
    'noopener',
  )
}

watch(
  () => route.params.id,
  () => {
    if (route.name === 'diagnosis-detail') void load()
  },
)

onMounted(load)

onBeforeUnmount(closeChannel)
</script>

<style scoped>
.title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-tag {
  margin-left: 8px;
  vertical-align: middle;
}

.running-progress {
  margin-top: 16px;
}

.progress-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}

.progress-hint {
  margin: 8px 0 0;
  font-size: 12px;
}

.result-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 16px;
}

.evidence-group + .evidence-group {
  margin-top: 16px;
}

.evidence-group-title {
  margin: 0 0 10px;
  font-size: 13px;
  color: #5c6b82;
}

.evidence-group :deep(.evidence-card + .evidence-card) {
  margin-top: 10px;
}

.metric-desc {
  margin: 0 0 8px;
  font-size: 12px;
}

@media (max-width: 1280px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
