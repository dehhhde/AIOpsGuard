import type { SystemSettings } from '@/types/settings'
import { USE_MOCK } from '@/utils/env'
import { mockApi } from '@/mock'
import { get } from './request'

export const settingsApi = {
  get(): Promise<SystemSettings> {
    if (USE_MOCK) return mockApi.getSettings()
    return get<SystemSettings>('/v1/config')
  },
}
