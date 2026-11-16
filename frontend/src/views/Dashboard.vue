<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">诊断工作台</h2>
        <p class="page-subtitle">查看最近诊断结果、进行中的任务，并手动触发一次诊断</p>
      </div>
      <el-button type="primary" @click="dialogVisible = true">
        <el-icon><Plus /></el-icon>
        <span>触发诊断</span>
      </el-button>
    </div>

    <StatePanel
      v-if="store.errors.sessions"
      state="error"
      :description="store.errors.sessions"
      @retry="load"
    />
    <el-skeleton v-else-if="!store.overview && store.loading.overview" :rows="2" animated />
    <div v-else class="stats-grid">
      <div class="stat-card card">
        <span class="stat-label">今日诊断数</span>
        <span class="stat-value">{{ store.overview?.totalToday ?? 0 }}</span>
        <span class="stat-hint">包含进行中的任务</span>
      </div>
      <div class="stat-card card">
        <span class="stat-label">诊断成功率</span>
        <span class="stat-value">{{ successRate }}%</span>
        <span class="stat-hint">已完成任务占比</span>
      </div>
      <div class="stat-card card">
        <span class="stat-label">平均耗时</span>
        <span class="stat-value">{{ avgDuration }}</span>
        <span class="stat-hint">从触发到报告生成</span>
      </div>
      <div class="stat-card card">
        <span class="stat-label">进行中</span>
        <span class="stat-value accent">{{ store.overview?.runningCount ?? 0 }}</span>
        <span class="stat-hint">进度每 2 秒自动刷新</span>
      </div>
    </div>

    <div v-if="store.runningSessions.length" class="card">
      <div class="section-title">
        <h3>进行中的诊断</h3>
        <span class="muted">Mock 模式每 2 秒推进一个阶段</span>
      </div>
      <div class="running-grid">
        <RunningCard
          v-for="session in store.runningSessions"
          :key="session.diagnosisId"
          :session="session"
        />
      </div>
    </div>

    <div class="card">
      <div class="section-title">
        <h3>最近诊断</h3>
        <el-button link type="primary" @click="router.push('/history')">查看全部</el-button>
      </div>

      <StatePanel v-if="store.loading.sessions && !store.sessions.length" state="loading" />
      <StatePanel
        v-else-if="!store.recentSessions.length"
        state="empty"
        description="还没有已完成的诊断"
      >
        <template #action>
          <el-button type="primary" @click="dialogVisible = true">触发第一次诊断</el-button>
        </template>
      </StatePanel>
      <div v-else class="table-wrap">
        <el-table :data="store.recentSessions" style="width: 100%" @row-click="openDetail">
          <el-table-column prop="serviceName" label="服务" min-width="140" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <StatusTag :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="开始时间" min-width="170">
            <template #default="{ row }">{{ formatDateTime(row.startedAt) }}</template>
          </el-table-column>
          <el-table-column label="耗时" width="110">
            <template #default="{ row }">
              {{ formatDuration(sessionDuration(row.startedAt, row.finishedAt)) }}
            </template>
          </el-table-column>
          <el-table-column label="首要根因" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">{{ row.rootCauses[0]?.cause ?? '—' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click.stop="openDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <TriggerDialog
      v-model="dialogVisible"
      :services="store.serviceOptions"
      @created="handleCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import StatusTag from '@/components/StatusTag.vue'
import RunningCard from '@/components/RunningCard.vue'
import TriggerDialog from '@/components/TriggerDialog.vue'
import StatePanel from '@/components/StatePanel.vue'
import type { DiagnosisSession } from '@/types/diagnosis'
import { useDiagnosisStore } from '@/stores/diagnosis'
import { formatDateTime, formatDuration, sessionDuration } from '@/utils/time'

const router = useRouter()
const store = useDiagnosisStore()
const dialogVisible = ref(false)

const successRate = computed(() =>
  store.overview ? Math.round(store.overview.successRate * 1000) / 10 : 0,
)
const avgDuration = computed(() => formatDuration(store.overview?.avgDurationMs))

function load(): void {
  void store.fetchSessions()
  void store.fetchOverview()
}

function openDetail(row: DiagnosisSession): void {
  void router.push(`/diagnosis/${row.diagnosisId}`)
}

function handleCreated(diagnosisId: string): void {
  void router.push(`/diagnosis/${diagnosisId}`)
}

onMounted(load)
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label {
  color: #7a889c;
  font-size: 13px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-value.accent {
  color: #409eff;
}

.stat-hint {
  color: #9aa7ba;
  font-size: 12px;
}

.running-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

@media (max-width: 1280px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .running-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
