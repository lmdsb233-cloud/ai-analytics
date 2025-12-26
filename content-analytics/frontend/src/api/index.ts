import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

type RetryableAxiosRequestConfig = AxiosRequestConfig & {
  __retryCount?: number
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const isNetworkOrTimeoutError = (error: any) => {
  return (
    error?.code === 'ECONNABORTED' ||
    error?.code === 'ERR_NETWORK' ||
    error?.message === 'Network Error' ||
    (typeof error?.message === 'string' && error.message.toLowerCase().includes('timeout'))
  )
}

const shouldRetryRequest = (error: any) => {
  const config = error?.config as RetryableAxiosRequestConfig | undefined
  if (!config) return false

  const method = (config.method || 'get').toLowerCase()
  if (method !== 'get') return false

  const retryCount = config.__retryCount || 0
  if (retryCount >= 1) return false

  return isNetworkOrTimeoutError(error)
}

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const instance: AxiosInstance = axios.create({
  baseURL,
  timeout: 10000,  // 10秒超时
  adapter: 'xhr',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  async (error) => {
    if (shouldRetryRequest(error)) {
      const config = error.config as RetryableAxiosRequestConfig
      config.__retryCount = (config.__retryCount || 0) + 1
      await sleep(300)
      return instance(config)
    }

    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        const authStore = useAuthStore()
        const url = String(error?.config?.url || '')
        const isAuthRequest = url.includes('/auth/login') || url.includes('/auth/register')
        const hasToken = !!authStore.token

        if (!isAuthRequest && hasToken) {
          authStore.logout()
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
        } else {
          ElMessage.error(data?.detail || data?.message || '未授权')
        }
      } else if (status === 403) {
        ElMessage.error('没有权限访问')
      } else if (status === 404) {
        ElMessage.error('资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器错误，请稍后重试')
      } else {
        ElMessage.error(data?.detail || data?.message || '请求失败')
      }
    } else {
      if (error?.code === 'ECONNABORTED') {
        ElMessage.error('请求超时，请稍后重试')
      } else if (typeof navigator !== 'undefined' && !navigator.onLine) {
        ElMessage.error('网络已断开，请检查网络连接')
      } else {
        ElMessage.error('无法连接服务器，请确认后端服务已启动')
      }
    }
    return Promise.reject(error)
  }
)

export default instance
