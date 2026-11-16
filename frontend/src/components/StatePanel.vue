<template>
  <div class="state-panel">
    <el-skeleton v-if="state === 'loading'" :rows="4" animated />
    <el-result
      v-else-if="state === 'error'"
      icon="error"
      title="加载失败"
      :sub-title="description || '请稍后重试'"
    >
      <template #extra>
        <el-button type="primary" @click="emit('retry')">重新加载</el-button>
      </template>
    </el-result>
    <el-empty v-else :description="description || '暂无数据'">
      <slot name="action" />
    </el-empty>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  state: 'loading' | 'empty' | 'error'
  description?: string
}>()

const emit = defineEmits<{
  retry: []
}>()
</script>

<style scoped>
.state-panel {
  padding: 12px 0;
}
</style>
