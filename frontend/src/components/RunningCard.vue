<template>
  <el-card shadow="never" class="running-card">
    <div class="running-head">
      <div>
        <span class="service">{{ session.serviceName }}</span>
        <StatusTag :status="session.status" class="status-tag" />
      </div>
      <el-button link type="primary" @click="goDetail">查看详情</el-button>
    </div>
    <div class="stage">
      <span class="muted">当前阶段</span>
      <span class="stage-label">{{ stageLabel }}</span>
    </div>
    <el-progress
      :percentage="percentage"
      :status="session.status === 'failed' ? 'exception' : undefined"
      :stroke-width="10"
    />
    <div class="running-meta">
      <span>已耗时 {{ elapsed }}</span>
      <span class="mono">{{ session.diagnosisId }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StatusTag from './StatusTag.vue'
import type { DiagnosisSession } from '@/types/diagnosis'
import { useDiagnosisStore } from '@/stores/diagnosis'
import { subscribeDiagnosisProgress, type ProgressChannel } from '@/api/ws'
import { DIAGNOSIS_STAGES, isTerminal } from '@/utils/diagnosis'
import { formatDuration, sessionDuration } from '@/utils/time'

const props = defineProps<{
  session: DiagnosisSession
}>()

const router = useRouter()
const store = useDiagnosisStore()
let channel: ProgressChannel | null = null

const percentage = computed(() => Math.min(100, Math.max(0, Math.round(props.session.progress ?? 0))))

const stageLabel = computed(() => {
  if (props.session.status === 'completed') return '已完成'
  if (props.session.status === 'failed') return '诊断失败'
  const stage = DIAGNOSIS_STAGES.find((item) => item.key === props.session.stage)
  return stage?.label ?? '等待调度'
})

const elapsed = computed(() =>
  formatDuration(sessionDuration(props.session.startedAt, props.session.finishedAt)),
)

function subscribe(): void {
  if (isTerminal(props.session.status)) return
  channel = subscribeDiagnosisProgress(props.session.diagnosisId, (event) => {
    store.applyProgress(event)
    if (isTerminal(event.status)) {
      channel?.close()
      channel = null
      void store.fetchOverview()
    }
  })
}

function goDetail(): void {
  void router.push(`/diagnosis/${props.session.diagnosisId}`)
}

onMounted(subscribe)

onBeforeUnmount(() => {
  channel?.close()
  channel = null
})
</script>

<style scoped>
.running-card {
  border: 1px solid #e5e8ef;
}

.running-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.service {
  font-weight: 600;
  margin-right: 8px;
}

.stage {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.stage-label {
  color: #409eff;
}

.running-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  color: #7a889c;
  font-size: 12px;
}
</style>
