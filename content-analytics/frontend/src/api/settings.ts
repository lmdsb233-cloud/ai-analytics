import request from './index'

export interface Settings {
  id: string
  user_id: string
  ai_provider: string
  has_deepseek_key: boolean
  has_openai_key: boolean
  has_iflow_key: boolean
  iflow_model: string | null
  created_at: string
  updated_at: string
}

export interface SettingsUpdate {
  ai_provider?: string
  deepseek_api_key?: string
  openai_api_key?: string
  iflow_api_key?: string
  iflow_model?: string
}

export const settingsApi = {
  getSettings() {
    return request.get<Settings>('/settings')
  },

  updateSettings(data: SettingsUpdate) {
    return request.put<Settings>('/settings', data)
  },

  testApiKey() {
    return request.post('/settings/test-api-key')
  }
}
