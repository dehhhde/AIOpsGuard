<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">历史记录</h2>
        <p class="page-subtitle">按时间范围、服务与状态筛选历史诊断，并导出当前页数据</p>
      </div>
      <el-button @click="exportPage" :disabled="!store.history.items.length">
        <el-icon><Download /></el-icon>
        <span>导出当前页</span>
      </el-button>
    </div>

    <div class="card">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="range"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            range-separator="至"
          />
        </el-form-item>
        <el-form-item label="服务">
          <el-select v-model="serviceName" placeholder="全部服务" clearable style="width: 160px">
            <el-option
              v-for="service in store.serviceOptions"
              :key="service"
              :label="service"
              :value="service"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="status" placeholder="全部状态" clearable style="width: 140px">
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilters">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card">
      <div class="section-title">
        <h3>诊断记录</h3>
        <span class="muted">共 {{ store.history.total }} 条</span>
      </div>

      <StatePanel
        v-if="store.errors.history"
        state="error"
        :description="store.errors.history"
        @retry="load"
      />
      <StatePanel v-else-if="store.loading.history && !store.history.items.length" state="loading" />
      <StatePanel v-else-if="!store.history.items.length" state="empty" description="没有符合条件的诊断记录" />
      <template v-else>
        <div class="table-wrap">
          <el-table :data="store.history.items" style="width: 100%" @row-click="openDetail">
            <el-table-column prop="diagnosisId" label="诊断 ID" min-width="200">
              <template #default="{ row }">
                <span class="mono">{{ row.diagnosisId }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="serviceName" label="服务" min-width="130" />
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
            <el-table-column label="首要根因" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">{{ row.rootCauses[0]?.cause ?? '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="openDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="pagination">
          <el-pagination
            :current-page="store.history.page"
            :page-size="store.history.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="store.history.total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import StatusTag from '@/components/StatusTag.vue'
import StatePanel from '@/components/StatePanel.vue'
import type { DiagnosisSession, DiagnosisStatus } from '@/types/diagnosis'
import { useDiagnosisStore } from '@/stores/diagnosis'
import { STATUS_META } from '@/utils/diagnosis'
import { downloadJson } from '@/utils/download'
import { formatDateTime, formatDuration, sessionDuration } from '@/utils/time'

const router = useRouter()
const store = useDiagnosisStore()

const range = ref<[Date, Date] | null>(null)
const serviceName = ref<string | undefined>()
const status = ref<DiagnosisStatus | undefined>()

const statusOptions = computed(() =>
  Object.entries(STATUS_META).map(([value, meta]) => ({
    value: value as DiagnosisStatus,
    label: meta.label,
  })),
)

function load(): void {
  void store.fetchSessions()
  void store.fetchHistory()
}

function applyFilters(): void {
  store.historyQuery.serviceName = serviceName.value
  store.historyQuery.status = status.value
  store.historyQuery.startTime = range.value?.[0]?.toISOString()
  store.historyQuery.endTime = range.value?.[1]?.toISOString()
  store.historyQuery.page = 1
  void store.fetchHistory()
}

function resetFilters(): void {
  range.value = null
  serviceName.value = undefined
  status.value = undefined
  store.resetHistoryQuery()
  void store.fetchHistory()
}

function handlePageChange(page: number): void {
  store.historyQuery.page = page
  void store.fetchHistory()
}

function handleSizeChange(pageSize: number): void {
  store.historyQuery.pageSize = pageSize
  store.historyQuery.page = 1
  void store.fetchHistory()
}

function openDetail(row: DiagnosisSession): void {
  void router.push(`/diagnosis/${row.diagnosisId}`)
}

function exportPage(): void {
  if (!store.history.items.length) {
    ElMessage.warning('当前没有可导出的数据')
    return
  }
  downloadJson(`diagnosis-history-${Date.now()}.json`, store.history.items)
  ElMessage.success(`已导出 ${store.history.items.length} 条记录`)
}

onMounted(load)
</script>

<style scoped>
.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
