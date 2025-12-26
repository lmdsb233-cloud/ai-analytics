<template>
  <div class="page-container">
    <div class="page-header">
      <h1>分析任务</h1>
    </div>

    <div class="card">
      <el-table :data="analysisStore.analyses" v-loading="analysisStore.loading" style="width: 100%">
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="100" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewResults(row)" :disabled="row.status === 'pending'">
              查看结果
            </el-button>
            <el-button type="success" link @click="triggerAI(row)" :disabled="row.status !== 'completed'">
              AI分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'
import type { Analysis } from '@/types'
import dayjs from 'dayjs'

const router = useRouter()
const analysisStore = useAnalysisStore()

onMounted(() => {
  analysisStore.fetchAnalyses()
})

const viewResults = (analysis: Analysis) => {
  router.push(`/analyses/${analysis.id}/results`)
}

const triggerAI = async (analysis: Analysis) => {
  try {
    await analysisStore.triggerAI(analysis.id)
    ElMessage.success('AI分析任务已触发')
    analysisStore.fetchAnalyses()
  } catch (error) {
    // Error handled by interceptor
  }
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    analyzing: 'warning',
    ai_processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    analyzing: '分析中',
    ai_processing: 'AI处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}
</script>
