<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">配置</h2>
        <p class="page-subtitle">展示数据源地址与功能开关的当前状态，本页只读</p>
      </div>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <StatePanel v-if="error" state="error" :description="error" @retry="load" />
    <StatePanel v-else-if="loading && !settings" state="loading" />
    <el-empty v-else-if="!settings" description="暂无配置信息" />

    <template v-else>
      <div class="card">
        <div class="section-title">
          <h3>数据源</h3>
          <span class="muted">地址来自 aiops-agent 配置，仅做展示</span>
        </div>
        <div class="table-wrap">
          <el-table :data="settings.dataSources" style="width: 100%">
            <el-table-column prop="name" label="组件" min-width="140" />
            <el-table-column label="类型" width="110">
              <template #default="{ row }">{{ kindLabel(row.kind) }}</template>
            </el-table-column>
            <el-table-column label="地址" min-width="260">
              <template #default="{ row }">
                <span class="mono">{{ row.url }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusMeta(row.status).type" size="small">
                  {{ statusMeta(row.status).label }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="note" label="说明" min-width="220" show-overflow-tooltip />
          </el-table>
        </div>
      </div>

      <div class="card">
        <div class="section-title">
          <h3>功能开关</h3>
          <span class="muted">LLM Provider：{{ settings.llmProvider }}</span>
        </div>
        <div class="table-wrap">
          <el-table :data="settings.switches" style="width: 100%">
            <el-table-column prop="name" label="开关" min-width="180" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-switch :model-value="row.enabled" disabled />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" min-width="300" show-overflow-tooltip />
          </el-table>
        </div>
        <p class="muted footer-note">
          最后更新时间：{{ formatDateTime(settings.updatedAt) }}。配置写入由后端配置管理提供，前端不提供修改入口。
        </p>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import StatePanel from '@/components/StatePanel.vue'
import { settingsApi } from '@/api/settings'
import type { DataSourceKind, DataSourceStatus, SystemSettings } from '@/types/settings'
import type { TagType } from '@/utils/diagnosis'
import { formatDateTime } from '@/utils/time'

const settings = ref<SystemSettings | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const KIND_LABELS: Record<DataSourceKind, string> = {
  metric: '指标',
  log: '日志',
  trace: '链路',
  visual: '可视化',
  storage: '存储',
  messaging: '消息队列',
  llm: '大模型',
}

const STATUS_META: Record<DataSourceStatus, { label: string; type: TagType }> = {
  reserved: { label: '预留', type: 'info' },
  partial: { label: '部分配置', type: 'warning' },
  configured: { label: '已配置', type: 'success' },
}

function kindLabel(kind: DataSourceKind): string {
  return KIND_LABELS[kind] ?? kind
}

function statusMeta(status: DataSourceStatus): { label: string; type: TagType } {
  return STATUS_META[status]
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    settings.value = await settingsApi.get()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '配置信息加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.footer-note {
  margin: 12px 0 0;
  font-size: 12px;
}
</style>
