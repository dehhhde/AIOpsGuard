<template>
  <el-dialog
    :model-value="modelValue"
    title="触发诊断"
    width="520px"
    :close-on-click-modal="false"
    @update:model-value="handleVisibleChange"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="目标服务" prop="targetService">
        <el-select v-model="form.targetService" placeholder="请选择服务" style="width: 100%">
          <el-option v-for="service in services" :key="service" :label="service" :value="service" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间窗" prop="range">
        <el-date-picker
          v-model="form.range"
          type="datetimerange"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          range-separator="至"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">开始诊断</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useDiagnosisStore } from '@/stores/diagnosis'

const props = defineProps<{
  modelValue: boolean
  services: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  created: [diagnosisId: string]
}>()

const store = useDiagnosisStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)

function defaultRange(): [Date, Date] {
  const end = new Date()
  const start = new Date(end.getTime() - 30 * 60 * 1000)
  return [start, end]
}

const form = reactive<{ targetService: string; range: [Date, Date] | null }>({
  targetService: props.services[0] ?? 'target-app',
  range: defaultRange(),
})

const rules: FormRules = {
  targetService: [{ required: true, message: '请选择目标服务', trigger: 'change' }],
  range: [{ required: true, message: '请选择诊断时间窗', trigger: 'change' }],
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) return
    formRef.value?.clearValidate()
    if (!form.targetService) form.targetService = props.services[0] ?? 'target-app'
    if (!form.range) form.range = defaultRange()
  },
)

function handleVisibleChange(value: boolean): void {
  emit('update:modelValue', value)
}

function close(): void {
  emit('update:modelValue', false)
}

async function submit(): Promise<void> {
  if (!formRef.value || !form.range) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const result = await store.triggerDiagnosis({
      targetService: form.targetService,
      startTime: form.range[0].toISOString(),
      endTime: form.range[1].toISOString(),
    })
    ElMessage.success(result.message)
    emit('created', result.diagnosisId)
    close()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '触发诊断失败')
  } finally {
    submitting.value = false
  }
}
</script>
