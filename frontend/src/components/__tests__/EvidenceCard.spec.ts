import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import EvidenceCard from '../EvidenceCard.vue'
import type { Evidence } from '@/types/diagnosis'

const evidence: Evidence = {
  id: 'ev-001',
  type: 'METRIC',
  summary: '堆内存使用量持续上升，疑似存在内存泄漏',
  source: 'prometheus: jvm.memory.used',
  metricName: 'jvm.memory.used',
  instance: 'target-app-1:8080',
  timeRange: {
    start: '2026-11-16T08:42:00+08:00',
    end: '2026-11-16T09:12:00+08:00',
  },
  detail: { baselineMB: 620, peakMB: 1980, weight: 0.86 },
}

function mountCard() {
  return mount(EvidenceCard, {
    props: { evidence, serviceName: 'target-app' },
    global: { plugins: [ElementPlus] },
  })
}

describe('EvidenceCard', () => {
  it('展示证据类型、摘要与来源', () => {
    const wrapper = mountCard()
    expect(wrapper.text()).toContain('指标证据')
    expect(wrapper.text()).toContain(evidence.summary)
    expect(wrapper.text()).toContain(evidence.source)
    expect(wrapper.text()).toContain('ev-001')
  })

  it('默认收起详情，点击后展开置信度影响', async () => {
    const wrapper = mountCard()
    expect(wrapper.text()).not.toContain('置信度影响')

    await wrapper.findAll('button')[0].trigger('click')

    expect(wrapper.text()).toContain('置信度影响')
    expect(wrapper.text()).toContain('0.86')
    expect(wrapper.text()).toContain('target-app-1:8080')
  })
})
