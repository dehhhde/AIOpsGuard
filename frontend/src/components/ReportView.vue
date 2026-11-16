<template>
  <div class="report-view">
    <el-alert type="success" :closable="false" show-icon class="report-summary">
      <template #title>诊断结论</template>
      <p class="summary-text">{{ report.summary }}</p>
    </el-alert>

    <el-collapse v-model="activeSections">
      <el-collapse-item
        v-for="section in report.sections"
        :key="section.title"
        :title="section.title"
        :name="section.title"
      >
        <div class="markdown-body" v-html="render(section.content)"></div>
      </el-collapse-item>
    </el-collapse>

    <div v-if="report.recommendations.length" class="recommendations">
      <h4>修复建议清单</h4>
      <ul>
        <li v-for="(item, index) in report.recommendations" :key="index">{{ item }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { marked } from 'marked'
import type { DiagnosisReport } from '@/types/diagnosis'

const props = defineProps<{
  report: DiagnosisReport
}>()

const activeSections = ref<string[]>(
  props.report.sections.filter((section) => !section.collapsed).map((section) => section.title),
)

function render(markdown: string): string {
  return marked.parse(markdown, { async: false }) as string
}
</script>

<style scoped>
.report-summary {
  margin-bottom: 14px;
}

.summary-text {
  margin: 6px 0 0;
  line-height: 1.7;
}

.recommendations {
  margin-top: 18px;
  padding: 14px 16px;
  background: #f7f9fc;
  border-radius: 6px;
}

.recommendations h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.recommendations ul {
  margin: 0;
  padding-left: 20px;
  line-height: 1.8;
  color: #2c3a4d;
}
</style>
