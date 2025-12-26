import request from './index'
import type { ApiResponse, Dataset } from '@/types'

export function uploadDataset(formData: FormData): Promise<ApiResponse<Dataset>> {
  return request.post('/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 60000  // 文件上传60秒超时
  })
}

export function getDatasets(page = 1, pageSize = 20): Promise<ApiResponse<{ items: Dataset[], total: number }>> {
  return request.get('/datasets', { params: { page, page_size: pageSize } })
}

export function getDataset(id: string): Promise<ApiResponse<Dataset>> {
  return request.get(`/datasets/${id}`)
}

export function deleteDataset(id: string): Promise<ApiResponse<void>> {
  return request.delete(`/datasets/${id}`)
}
