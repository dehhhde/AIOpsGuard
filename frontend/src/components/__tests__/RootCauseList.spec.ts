import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import RootCauseList from '../RootCauseList.vue'
import type { RootCause } from '@/types/diagnosis'

const rootCauses: RootCause[] = [
  { rank: 2, cause: '连接池等待升高', confidence: 0.4, evidenceIds: ['ev-003'] },
  {
    rank: 1,
    cause: '缓存未设上限导致堆内存泄漏',
    confidence: 0.92,
    evidenceIds: ['ev-001', 'ev-002', 'ev-004'],
    recommendations: ['为缓存设置容量上限'],
  },
]

function mountList() {
  return mount(RootCauseList, {
    props: { rootCauses },
    global: { plugins: [ElementPlus] },
  })
}

describe('RootCauseList', () => {
  it('按置信度从高到低排序', () => {
    const text = mountList().text()
    expect(text.indexOf('缓存未设上限导致堆内存泄漏')).toBeLessThan(text.indexOf('连接池等待升高'))
  })

  it('展示置信度百分比与证据数量', () => {
    const wrapper = mountList()
    expect(wrapper.text()).toContain('92%')
    expect(wrapper.text()).toContain('证据 3 条')
    expect(wrapper.text()).toContain('证据 1 条')
  })

  it('展示修复建议', () => {
    expect(mountList().text()).toContain('为缓存设置容量上限')
  })

  it('没有根因时展示空状态', () => {
    const wrapper = mount(RootCauseList, {
      props: { rootCauses: [] },
      global: { plugins: [ElementPlus] },
    })
    expect(wrapper.text()).toContain('暂无根因结论')
  })
})
