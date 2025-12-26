<template>
  <div class="page-container">
    <div class="page-header">
      <h1>分析结果 - {{ analysisStore.currentAnalysis?.name }}</h1>
      <div class="actions">
        <el-tag :type="getStatusType(analysisStore.currentAnalysis?.status)">
          {{ getStatusText(analysisStore.currentAnalysis?.status) }}
        </el-tag>
        <el-button type="primary" @click="handleExport">导出报告</el-button>
      </div>
    </div>

    <div class="filter-bar card">
      <el-select v-model="filterPerformance" placeholder="筛选表现" clearable @change="loadResults">
        <el-option label="全部" value="" />
        <el-option label="优秀" value="优秀" />
        <el-option label="正常" value="正常" />
        <el-option label="偏低" value="偏低" />
        <el-option label="较差" value="较差" />
      </el-select>
    </div>

    <div class="card">
      <el-table :data="analysisStore.results" v-loading="analysisStore.loading" style="width: 100%">
        <el-table-column prop="post_data_id" label="笔记ID" width="120" />
        <el-table-column prop="post_content_type" label="内容形式" width="100" />
        <el-table-column prop="post_type" label="发文类型" min-width="120" />
        <el-table-column prop="performance" label="表现" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getPerformanceType(row.performance)" size="small">
              {{ row.performance }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="问题指标" min-width="150">
          <template #default="{ row }">
            <span v-if="row.result_data?.problem_metrics?.length">
              {{ row.result_data.problem_metrics.join('、') }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="亮点指标" min-width="150">
          <template #default="{ row }">
            <span v-if="row.result_data?.highlight_metrics?.length">
              {{ row.result_data.highlight_metrics.join('、') }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'
import { exportsApi } from '@/api/exports'
import type { AnalysisResult } from '@/types'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()

const filterPerformance = ref('')
const analysisId = route.params.id as string

onMounted(() => {
  analysisStore.fetchAnalysis(analysisId)
  loadResults()
})

const loadResults = () => {
  analysisStore.fetchResults(analysisId, filterPerformance.value || undefined)
}

const viewDetail = (result: AnalysisResult) => {
  router.push({
    path: `/posts/${result.post_id}`,
    query: { analysis_id: analysisId }
  })
}

const handleExport = async () => {
  try {
    await exportsApi.createExport(analysisId, 'excel')
    ElMessage.success('导出任务已创建，请到导出页面下载')
  } catch (error) {
    ElMessage.error('创建导出任务失败')
  }
}

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    analyzing: 'warning',
    ai_processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    analyzing: '分析中',
    ai_processing: 'AI处理中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status || ''] || ''
}

const getPerformanceType = (performance: string) => {
  const map: Record<string, string> = {
    '优秀': 'success',
    '正常': '',
    '偏低': 'warning',
    '较差': 'danger'
  }
  return map[performance] || 'info'
}
</script>

<style lang="scss" scoped>
.page-header {
  .actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.filter-bar {
  margin-bottom: 20px;
  padding: 16px;
}

.text-muted {
  color: #909399;
}
</style>
