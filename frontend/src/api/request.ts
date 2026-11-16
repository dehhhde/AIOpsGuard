import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import { API_BASE_URL } from '@/utils/env'

const instance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

instance.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const message =
      error.response?.data?.detail || error.response?.data?.message || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  },
)

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await instance.get<T>(url, { params })
  return response.data
}

export async function post<T>(url: string, body?: unknown): Promise<T> {
  const response = await instance.post<T>(url, body)
  return response.data
}

export default instance
