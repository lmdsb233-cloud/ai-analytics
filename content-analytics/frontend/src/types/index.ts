// 通用响应
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 用户
export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
}

// 数据集
export interface Dataset {
  id: string
  name: string
  original_filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  row_count: number
  error_message?: string
  created_at: string
  updated_at: string
}

// 笔记
export interface Post {
  id: string
  dataset_id: string
  data_id: string
  publish_time?: string
  publish_link?: string
  content_type?: string
  post_type?: string
  source?: string
  style_info?: string
  read_7d?: number
  interact_7d?: number
  visit_7d?: number
  want_7d?: number
  read_14d?: number
  interact_14d?: number
  visit_14d?: number
  want_14d?: number
  created_at: string
}

// 分析任务
export interface Analysis {
  id: string
  dataset_id: string
  name?: string
  status: 'pending' | 'analyzing' | 'ai_processing' | 'completed' | 'failed'
  progress: string
  error_message?: string
  created_at: string
  completed_at?: string
}

// 分析结果
export interface AnalysisResult {
  id: string
  analysis_id: string
  post_id: string
  performance?: string
  result_data?: {
    performance: string
    problem_metrics: string[]
    highlight_metrics: string[]
    compare_to_avg: Record<string, string>
    percentile_ranks: Record<string, number>
  }
  created_at: string
  post_data_id?: string
  post_content_type?: string
  post_type?: string
}

// AI输出
export interface AIOutput {
  id: string
  analysis_result_id: string
  summary?: string
  strengths?: string[]
  weaknesses?: string[]
  suggestions?: string[]
  model_name?: string
  created_at: string
}

// 导出
export interface Export {
  id: string
  analysis_id: string
  format: 'excel' | 'pdf' | 'json'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}
