<template>
  <div class="page-container">
    <div class="page-header">
      <h1>分析任务</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建分析任务
      </el-button>
    </div>

    <div class="card">
      <el-table :data="analysisStore.analyses" v-loading="analysisStore.loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)">{{ getStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewResults(row)" :disabled="row.status === 'pending'">
              查看结果
            </el-button>
            <el-button 
              v-if="row.status === 'analyzing' || row.status === 'ai_processing'" 
              type="danger" 
              link 
              @click="handleStop(row)"
            >
              停止
            </el-button>
            <el-button 
              v-else
              type="success" 
              link 
              @click="triggerAI(row)" 
              :disabled="row.status !== 'completed'"
            >
              AI分析
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建分析任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建分析任务" width="500px">
      <el-form label-width="100px">
        <el-form-item label="选择数据集">
          <el-select v-model="selectedDatasetId" placeholder="请选择数据集" style="width: 100%">
            <el-option 
              v-for="ds in datasets" 
              :key="ds.id" 
              :label="ds.name" 
              :value="ds.id"
              :disabled="ds.status !== 'completed'"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名称">
          <el-input v-model="analysisName" placeholder="可选，默认使用数据集名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating" :disabled="!selectedDatasetId">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'
import { createAnalysis } from '@/api/analyses'
import { getDatasets } from '@/api/datasets'
import type { Analysis } from '@/types'
import dayjs from 'dayjs'

const router = useRouter()
const analysisStore = useAnalysisStore()

// 新建分析相关
const showCreateDialog = ref(false)
const selectedDatasetId = ref('')
const analysisName = ref('')
const creating = ref(false)
const datasets = ref<any[]>([])

let timer: ReturnType<typeof setInterval> | null = null

const runningIds = () =>
  analysisStore.analyses
    .filter(a => ['pending', 'analyzing', 'ai_processing'].includes(a.status))
    .map(a => a.id)

const startPolling = () => {
  stopPolling()
  const ids = runningIds()
  if (!ids.length) return
  timer = setInterval(async () => {
    const currentIds = runningIds()
    if (!currentIds.length) {
      stopPolling()
      return
    }
    // 仅刷新运行中的任务，减少整体重渲染
    await Promise.all(currentIds.map(id => analysisStore.fetchAnalysis(id)))
  }, 5000)
}

const stopPolling = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

// 获取数据集列表
const fetchDatasets = async () => {
  try {
    const res = await getDatasets()
    datasets.value = res.data.items || []
  } catch (error) {
    console.error('获取数据集失败', error)
  }
}

// 创建分析任务
const handleCreate = async () => {
  if (!selectedDatasetId.value) return
  creating.value = true
  try {
    const ds = datasets.value.find(d => d.id === selectedDatasetId.value)
    const name = analysisName.value || (ds ? `${ds.name}的分析` : '新分析任务')
    await createAnalysis({ dataset_id: selectedDatasetId.value, name })
    ElMessage.success('分析任务创建成功')
    showCreateDialog.value = false
    selectedDatasetId.value = ''
    analysisName.value = ''
    await analysisStore.fetchAnalyses()
    startPolling()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await analysisStore.fetchAnalyses()
  await fetchDatasets()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})

const viewResults = (analysis: Analysis) => {
  router.push(`/analyses/${analysis.id}/results`)
}

const triggerAI = async (analysis: Analysis) => {
  try {
    await analysisStore.triggerAI(analysis.id)
    ElMessage.success('AI分析任务已触发')
    await analysisStore.fetchAnalyses()
    startPolling()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleStop = async (analysis: Analysis) => {
  try {
    await analysisStore.stopAnalysis(analysis.id)
    ElMessage.success('分析任务已停止')
    await analysisStore.fetchAnalyses()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleDelete = async (analysis: Analysis) => {
  try {
    await ElMessageBox.confirm('确定要删除该分析任务吗？删除后无法恢复', '确认删除', {
      type: 'warning'
    })
    await analysisStore.deleteAnalysis(analysis.id)
    ElMessage.success('分析任务已删除')
    await analysisStore.fetchAnalyses()
  } catch (error) {
    // 用户取消或其他错误
  }
}

const getStatusType = (analysis: Analysis) => {
  if (analysis.status === 'failed') return 'danger'
  if (analysis.status === 'pending') return 'info'
  if (analysis.status === 'analyzing' || analysis.status === 'ai_processing') return 'warning'
  if (analysis.status === 'completed') {
    if (analysis.ai_status === 'partial') return 'warning'
    return 'success'
  }
  return 'info'
}

const getStatusText = (analysis: Analysis) => {
  if (analysis.status === 'pending') return '等待解析'
  if (analysis.status === 'analyzing') return '数据解析中'
  if (analysis.status === 'ai_processing') return 'AI分析中'
  if (analysis.status === 'failed') return '失败'
  if (analysis.status === 'completed') {
    if (analysis.ai_status === 'completed') return 'AI分析完成'
    if (analysis.ai_status === 'partial') return 'AI部分完成'
    if (analysis.ai_status === 'processing') return 'AI分析中'
    return '待AI分析'
  }
  return analysis.status
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}
</script>
