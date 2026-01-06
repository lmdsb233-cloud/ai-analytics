<template>
  <div class="datasets-page fade-in">
    <!-- 顶部统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%)">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ datasetStore.total }}</span>
          <span class="stat-label">数据集总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #00b464 0%, #00d68f 100%)">
          <el-icon><Check /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ completedCount }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #ff9500 0%, #ffb340 100%)">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ processingCount }}</span>
          <span class="stat-label">处理中</span>
        </div>
      </div>
    </div>

    <!-- 数据集列表 -->
    <div class="content-card">
      <div class="card-header">
        <h3>📁 数据集列表</h3>
        <div class="actions">
          <el-button @click="loadData" :loading="datasetStore.loading">刷新</el-button>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传数据集
          </el-button>
        </div>
      </div>
      
      <el-table :data="datasetStore.datasets" v-loading="datasetStore.loading">
        <el-table-column prop="name" label="数据集名称" min-width="180">
          <template #default="{ row }">
            <div class="dataset-name">
              <span class="name-icon">📊</span>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="original_filename" label="文件名" min-width="150" />
        <el-table-column prop="row_count" label="笔记数" width="100" align="center">
          <template #default="{ row }">
            <span class="count-badge">{{ row.row_count || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="180" align="center">
          <template #default="{ row }">
            <div class="status-cell">
              <el-tooltip 
                :content="row.error_message" 
                :disabled="row.status !== 'failed' || !row.error_message"
                placement="top"
              >
                <el-tag :type="getStatusType(row.status)" effect="plain" class="status-tag">
                  <el-icon class="status-icon" :class="{ 'is-loading': row.status === 'processing' }">
                    <component :is="getStatusIcon(row.status)" />
                  </el-icon>
                  <span class="status-text">{{ getStatusText(row.status, row.progress) }}</span>
                </el-tag>
              </el-tooltip>
              <div v-if="row.status === 'completed'" class="status-detail">
                ✓ 数据解析完成
              </div>
              <div v-else-if="row.status === 'processing'" class="status-detail processing">
                正在提取笔记图文...
              </div>
              <div v-else-if="row.status === 'pending'" class="status-detail">
                排队等待中
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small"
              @click="handleViewAnalysis(row)"
              :disabled="row.status !== 'completed'"
            >
              {{ row.status === 'completed' ? '查看分析' : '解析中...' }}
            </el-button>
            <el-button type="danger" size="small" plain @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="datasetStore.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
          background
        />
      </div>
    </div>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传数据集" width="520px" class="upload-dialog">
      <div class="upload-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>上传小红书导出的Excel数据文件，系统将自动解析并分析</span>
      </div>
      
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="数据集名称" required>
          <el-input v-model="uploadForm.name" placeholder="如：2024年12月数据" size="large" />
        </el-form-item>
        <el-form-item label="选择Excel文件" required>
          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
          >
            <div class="upload-content">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                <span class="main-text">拖拽文件到此处，或 <em>点击上传</em></span>
                <span class="sub-text">支持 .xlsx / .xls 格式，最大10MB</span>
              </div>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false" size="large">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload" size="large">
          开始上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadInstance, type UploadFile } from 'element-plus'
import { Upload, FolderOpened, Check, Loading, InfoFilled, UploadFilled, Clock, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { useDatasetStore } from '@/stores/dataset'
import type { Dataset } from '@/types'
import dayjs from 'dayjs'

const router = useRouter()
const datasetStore = useDatasetStore()
const completedCount = computed(() => datasetStore.datasets.filter(d => d.status === 'completed').length)
const processingCount = computed(() => datasetStore.datasets.filter(d => d.status === 'processing' || d.status === 'pending').length)

const currentPage = ref(1)
const pageSize = ref(20)
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadRef = ref<UploadInstance>()

const uploadForm = reactive({
  name: '',
  file: null as File | null
})

onMounted(() => {
  loadData()
})

const loadData = () => {
  datasetStore.fetchDatasets(currentPage.value, pageSize.value)
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadData()
}

const handleFileChange = (file: UploadFile) => {
  uploadForm.file = file.raw || null
}

const handleUpload = async () => {
  if (!uploadForm.name) {
    ElMessage.warning('请输入数据集名称')
    return
  }
  if (!uploadForm.file) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    await datasetStore.uploadDataset(uploadForm.name, uploadForm.file)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.name = ''
    uploadForm.file = null
    uploadRef.value?.clearFiles()
    loadData()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    uploading.value = false
  }
}

const handleViewAnalysis = async () => {
  router.push('/analyses')
}

const handleDelete = (dataset: Dataset) => {
  ElMessageBox.confirm('确定要删除该数据集吗？删除后无法恢复', '确认删除', {
    type: 'warning'
  }).then(async () => {
    await datasetStore.deleteDataset(dataset.id)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

const getStatusType = (status: string): 'info' | 'warning' | 'success' | 'danger' => {
  const map: Record<string, 'info' | 'warning' | 'success' | 'danger'> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusIcon = (status: string) => {
  const map: Record<string, any> = {
    pending: Clock,
    processing: Loading,
    completed: CircleCheck,
    failed: CircleClose
  }
  return map[status] || Clock
}

const getStatusText = (status: string, progress?: string | null) => {
  if (status === 'processing' && progress) {
    return `解析中 (${progress})`
  }
  if (status === 'pending') {
    return '等待解析'
  }
  const map: Record<string, string> = {
    pending: '等待解析',
    processing: '解析中...',
    completed: '已完成',
    failed: '解析失败'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 自动刷新：当有处理中的数据集时，每3秒刷新一次
let refreshTimer: ReturnType<typeof setInterval> | null = null

const startAutoRefresh = () => {
  if (refreshTimer) return
  refreshTimer = setInterval(() => {
    const hasProcessing = datasetStore.datasets.some(d => d.status === 'processing' || d.status === 'pending')
    if (hasProcessing) {
      datasetStore.fetchDatasets(currentPage.value, pageSize.value)
    } else {
      stopAutoRefresh()
    }
  }, 3000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 监听数据变化，启动/停止自动刷新
watch(() => datasetStore.datasets, (datasets) => {
  const hasProcessing = datasets.some(d => d.status === 'processing' || d.status === 'pending')
  if (hasProcessing) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}, { immediate: true })

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.datasets-page {
  .stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 24px;
  }
  
  .stat-card {
    background: #fff;
    border-radius: 16px;
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    
    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 24px;
    }
    
    .stat-info {
      display: flex;
      flex-direction: column;
      
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #333;
      }
      
      .stat-label {
        font-size: 14px;
        color: #999;
        margin-top: 4px;
      }
    }
  }
  
  .content-card {
    background: #fff;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    
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
  
  .dataset-name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
  }
  
  .count-badge {
    background: #f5f5f5;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    color: #666;
  }
  
  .time-text {
    color: #999;
    font-size: 13px;
  }
  
  .status-cell {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }
  
  .status-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-weight: 500;
    
    .status-icon {
      font-size: 14px;
      
      &.is-loading {
        animation: rotating 1.5s linear infinite;
      }
    }
    
    .status-text {
      font-size: 13px;
    }
  }
  
  .status-detail {
    font-size: 11px;
    color: #67c23a;
    
    &.processing {
      color: #e6a23c;
    }
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff0f1;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #ff2442;
  font-size: 14px;
}

.upload-area {
  width: 100%;
  
  :deep(.el-upload-dragger) {
    padding: 40px;
    border-radius: 12px;
  }
  
  .upload-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }
  
  .upload-icon {
    font-size: 48px;
    color: #ff2442;
  }
  
  .upload-text {
    text-align: center;
    
    .main-text {
      display: block;
      color: #666;
      
      em {
        color: #ff2442;
        font-style: normal;
      }
    }
    
    .sub-text {
      display: block;
      color: #999;
      font-size: 12px;
      margin-top: 8px;
    }
  }
}
</style>
