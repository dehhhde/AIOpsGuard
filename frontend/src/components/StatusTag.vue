<template>
  <el-tag :type="meta.type" :effect="effect" size="small">{{ meta.label }}</el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { DiagnosisStatus } from '@/types/diagnosis'
import { STATUS_META } from '@/utils/diagnosis'

const props = withDefaults(
  defineProps<{
    status: DiagnosisStatus
    effect?: 'light' | 'dark' | 'plain'
  }>(),
  { effect: 'light' },
)

const meta = computed(() => STATUS_META[props.status] ?? STATUS_META.pending)
</script>
