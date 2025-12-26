import request from './index'
import type { ApiResponse, Analysis, AnalysisResult, AIOutput, Post } from '@/types'

export function createAnalysis(data: { dataset_id: string, name?: string, config?: any }): Promise<ApiResponse<Analysis>> {
  return request.post('/analyses', data)
}

export function getAnalyses(datasetId?: string, page = 1, pageSize = 20): Promise<ApiResponse<Analysis[]>> {
  const params: any = { page, page_size: pageSize }
  if (datasetId) params.dataset_id = datasetId
  return request.get('/analyses', { params })
}

export function getAnalysis(id: string): Promise<ApiResponse<Analysis>> {
  return request.get(`/analyses/${id}`)
}

export function getAnalysisResults(
  analysisId: string, 
  performance?: string, 
  page = 1, 
  pageSize = 50
): Promise<ApiResponse<AnalysisResult[]>> {
  const params: any = { page, page_size: pageSize }
  if (performance) params.performance = performance
  return request.get(`/analyses/${analysisId}/results`, { params, timeout: 60000 })
}

export function triggerAIAnalysis(analysisId: string): Promise<ApiResponse<void>> {
  return request.post(`/analyses/${analysisId}/ai`)
}

export function getPost(postId: string): Promise<ApiResponse<Post>> {
  return request.get(`/posts/${postId}`)
}

export function getPostAIOutput(postId: string, analysisId: string): Promise<ApiResponse<AIOutput>> {
  return request.get(`/posts/${postId}/ai-output`, { params: { analysis_id: analysisId } })
}
