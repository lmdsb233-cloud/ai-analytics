import request from './index'

export interface ScreenshotAnalysisResponse {
  success: boolean
  data: {
    summary: string
    strengths: string[]
    weaknesses: string[]
    suggestions: string[]
    model_name: string
    tokens_used?: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
    image_path: string
  }
}

/**
 * 上传截图并分析
 */
export function analyzeScreenshot(file: File): Promise<ScreenshotAnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return request.post<ScreenshotAnalysisResponse, ScreenshotAnalysisResponse>(
    '/screenshots/analyze',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
}
