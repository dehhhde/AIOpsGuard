<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '216px'" class="layout-aside">
      <div class="brand" :class="{ 'brand--collapsed': collapsed }">
        <el-icon :size="22" color="#409eff"><DataLine /></el-icon>
        <span v-if="!collapsed" class="brand-text">AIOpsGuard</span>
      </div>
      <el-menu :default-active="activeMenu" :collapse="collapsed" router class="layout-menu">
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>诊断工作台</template>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <template #title>历史记录</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>配置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-button text class="collapse-btn" @click="collapsed = !collapsed">
            <el-icon :size="18">
              <Expand v-if="collapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          <span class="header-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag v-if="USE_MOCK" type="warning" effect="plain" size="small">Mock 数据</el-tag>
          <el-button link type="primary" @click="openGrafana">
            <el-icon><Monitor /></el-icon>
            <span>Grafana</span>
          </el-button>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Clock, DataLine, Expand, Fold, Monitor, Odometer, Setting } from '@element-plus/icons-vue'
import { GRAFANA_BASE_URL, USE_MOCK } from '@/utils/env'

const route = useRoute()
const collapsed = ref(false)

const pageTitle = computed(() => (route.meta.title as string | undefined) ?? 'AIOpsGuard')

const activeMenu = computed(() => {
  if (route.path.startsWith('/diagnosis')) return '/dashboard'
  return route.path
})

function openGrafana(): void {
  window.open(GRAFANA_BASE_URL, '_blank', 'noopener')
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
}

.layout-aside {
  background: #10192b;
  transition: width 0.2s ease;
  overflow: hidden;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 60px;
  padding: 0 20px;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand--collapsed {
  justify-content: center;
  padding: 0;
}

.brand-text {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.layout-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #b6c2d9;
  --el-menu-hover-bg-color: rgba(64, 158, 255, 0.12);
  --el-menu-active-color: #ffffff;
}

.layout-menu :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.22);
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e8ef;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
}

.collapse-btn {
  padding: 6px;
}

.layout-main {
  padding: 20px;
  background: #f4f6fa;
  overflow-x: hidden;
}

@media (max-width: 1280px) {
  .layout-main {
    padding: 14px;
  }
}
</style>
