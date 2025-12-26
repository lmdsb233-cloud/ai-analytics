import request from './index'

export interface ExportRecord {
  id: string
  analysis_id: string
  analysis_name: string
  format: string
  status: string
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export const exportsApi = {
  // 获取导出列表
  getExports() {
    return request.get<ExportRecord[]>('/exports')
  },

  // 创建导出任务
  createExport(analysisId: string, format = 'excel') {
    return request.post<{ export_id: string }>(`/exports/${analysisId}/export`, null, { params: { format } })
  },

  // 获取导出状态
  getExportStatus(exportId: string) {
    return request.get<{ id: string; status: string; error_message: string | null }>(`/exports/${exportId}/status`)
  },

  // 下载导出文件
  async downloadExport(exportId: string, filename: string) {
    const response = await request.get(`/exports/${exportId}/download`, { responseType: 'blob' })
    // 触发下载
    const url = window.URL.createObjectURL(new Blob([response as any]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }
}
