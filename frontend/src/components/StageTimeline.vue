<template>
  <div class="stage-timeline">
    <el-steps :active="active" :process-status="processStatus" align-center finish-status="success">
      <el-step
        v-for="(stage, index) in DIAGNOSIS_STAGES"
        :key="stage.key"
        :title="stage.label"
        :description="stage.description"
      >
        <template #icon>
          <el-icon v-if="isStageFailed(session, index)"><CircleCloseFilled /></el-icon>
          <el-icon v-else-if="isStageFinished(session, index)"><CircleCheckFilled /></el-icon>
          <span v-else class="step-index">{{ index + 1 }}</span>
        </template>
      </el-step>
    </el-steps>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import type { DiagnosisSession } from '@/types/diagnosis'
import {
  DIAGNOSIS_STAGES,
  activeStageIndex,
  isStageFailed,
  isStageFinished,
} from '@/utils/diagnosis'

const props = defineProps<{
  session: DiagnosisSession
}>()

const active = computed(() => activeStageIndex(props.session))
const processStatus = computed(() => (props.session.status === 'failed' ? 'error' : 'process'))
</script>

<style scoped>
.stage-timeline {
  padding: 8px 4px 4px;
}

.step-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e8eef7;
  color: #6b7c93;
  font-size: 12px;
}

:deep(.el-step__description) {
  font-size: 12px;
}

@media (max-width: 1100px) {
  :deep(.el-step__description) {
    display: none;
  }
}
</style>
