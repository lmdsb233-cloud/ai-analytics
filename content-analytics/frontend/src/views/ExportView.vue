<template>
  <div class="export-page fade-in">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">📤</div>
        <div class="header-text">
          <h1>导出报告</h1>
          <p>导出分析报告为Excel或JSON格式</p>
        </div>
      </div>
    </div>

    <div class="export-card">
      <div class="card-header">
        <h3>导出历史</h3>
        <el-button type="primary" @click="refreshList" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table :data="exports" v-loading="loading" empty-text="暂无导出记录" class="export-table">
        <el-table-column prop="analysis_name" label="分析任务" min-width="180" />
        <el-table-column prop="format" label="格式" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.format === 'excel' ? 'success' : 'info'">
              {{ row.format.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              size="small"
              @click="downloadFile(row)"
              :loading="downloadingId === row.id"
            >
              下载
            </el-button>
            <el-button
              v-else-if="row.status === 'failed'"
              type="danger"
              size="small"
              @click="showError(row)"
            >
              查看错误
            </el-button>
            <span v-else class="processing-text">处理中...</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="tip-card">
      <div class="tip-icon">💡</div>
      <div class="tip-content">
        <h4>如何导出报告？</h4>
        <p>1. 进入「分析任务」页面，选择已完成的分析任务</p>
        <p>2. 点击「导出报告」按钮，选择导出格式</p>
        <p>3. 等待导出完成后，在本页面下载文件</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { exportsApi, type ExportRecord } from '@/api/exports'

const loading = ref(false)
const exports = ref<ExportRecord[]>([])
const downloadingId = ref<string | null>(null)

const fetchExports = async () => {
  loading.value = true
  try {
    const res = await exportsApi.getExports()
    exports.value = res.data || []
  } catch (error) {
    console.error('获取导出列表失败', error)
  } finally {
    loading.value = false
  }
}

const refreshList = () => {
  fetchExports()
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const downloadFile = async (record: ExportRecord) => {
  downloadingId.value = record.id
  try {
    const ext = record.format === 'excel' ? 'xlsx' : record.format
    const filename = `${record.analysis_name}_报告.${ext}`
    await exportsApi.downloadExport(record.id, filename)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  } finally {
    downloadingId.value = null
  }
}

const showError = (record: ExportRecord) => {
  ElMessageBox.alert(record.error_message || '未知错误', '导出失败原因', {
    confirmButtonText: '知道了',
    type: 'error'
  })
}

onMounted(() => {
  fetchExports()
})
</script>

<style lang="scss" scoped>
.export-page {
  max-width: 1200px;
}

.page-header {
  margin-bottom: 24px;
  
  .header-content {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .header-icon {
    font-size: 40px;
  }
  
  .header-text {
    h1 {
      font-size: 24px;
      font-weight: 700;
      color: #333;
      margin-bottom: 4px;
    }
    
    p {
      font-size: 14px;
      color: #999;
    }
  }
}

.export-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(255, 36, 66, 0.06);
  margin-bottom: 24px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h3 {
      font-size: 18px;
      font-weight: 600;
      color: #333;
    }
  }
}

.export-table {
  :deep(.el-table__header th) {
    background: #fafafa;
    color: #666;
    font-weight: 600;
  }
}

.processing-text {
  color: #909399;
  font-size: 13px;
}

.tip-card {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #fff5f6 0%, #fff 100%);
  border-radius: 16px;
  border: 1px solid #ffe4e6;
  
  .tip-icon {
    font-size: 32px;
  }
  
  .tip-content {
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #333;
      margin-bottom: 12px;
    }
    
    p {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>
