import axios from './index'
import type { ApiResponse } from '@/types'

export interface Conversation {
  id: string
  title?: string
  context_type: 'general' | 'analysis' | 'analysis_result'
  context_analysis_id?: string
  context_analysis_result_id?: string
  created_at: string
  updated_at: string
  message_count?: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: any
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

export interface ConversationCreate {
  title?: string
  context_type?: 'general' | 'analysis' | 'analysis_result'
  context_analysis_id?: string
  context_analysis_result_id?: string
}

// 创建对话
export function createConversation(data: ConversationCreate): Promise<ApiResponse<Conversation>> {
  return axios.post('/chat/conversations', data)
}

// 获取对话列表
export function getConversations(params?: {
  context_type?: string
  context_analysis_id?: string
  page?: number
  page_size?: number
}): Promise<ApiResponse<Conversation[]>> {
  return axios.get('/chat/conversations', { params })
}

// 获取对话详情
export function getConversation(id: string): Promise<ApiResponse<ConversationDetail>> {
  return axios.get(`/chat/conversations/${id}`)
}

// 从分析结果创建对话
export function createConversationFromAnalysisResult(
  analysisResultId: string
): Promise<ApiResponse<Conversation>> {
  return axios.post(`/chat/analysis-results/${analysisResultId}/conversation`)
}

// 发送消息（SSE流式响应）
export async function sendMessage(
  conversationId: string,
  content: string,
  callbacks: {
    onStart?: () => void
    onChunk: (chunk: string) => void
    onDone?: () => void
    onError?: (error: Error) => void
  }
) {
  // 使用fetch API发送POST请求并读取流式响应
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  // 从auth store获取token
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  const token = authStore.token || localStorage.getItem('token') || ''
  
  fetch(`${baseURL}/chat/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token || ''}`
    },
    body: JSON.stringify({ content })
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('无法读取响应流')
      }
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'start') {
                callbacks.onStart?.()
              } else if (data.type === 'chunk') {
                callbacks.onChunk(data.content)
              } else if (data.type === 'done') {
                callbacks.onDone?.()
                return
              } else if (data.type === 'error') {
                callbacks.onError?.(new Error(data.message))
                return
              }
            } catch (e) {
              console.error('解析SSE消息失败:', e)
            }
          }
        }
      }
    })
    .catch((error) => {
      callbacks.onError?.(error)
    })
}
