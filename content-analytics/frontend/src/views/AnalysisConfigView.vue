<template>
  <div class="page-container">
    <div class="page-header">
      <h1>分析配置</h1>
    </div>

    <div class="card">
      <el-form :model="configForm" label-width="120px">
        <el-form-item label="分析名称">
          <el-input v-model="configForm.name" placeholder="请输入分析名称" />
        </el-form-item>
        <el-form-item label="主要指标">
          <el-checkbox-group v-model="configForm.primaryMetrics">
            <el-checkbox label="read_7d">7天阅读</el-checkbox>
            <el-checkbox label="interact_7d">7天互动</el-checkbox>
            <el-checkbox label="visit_7d">7天好物访问</el-checkbox>
            <el-checkbox label="want_7d">7天好物想要</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="分组依据">
          <el-select v-model="configForm.groupBy" placeholder="请选择">
            <el-option label="内容形式" value="content_type" />
            <el-option label="发文类型" value="post_type" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit">开始分析</el-button>
          <el-button @click="handleCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAnalysisStore } from '@/stores/analysis'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()

const configForm = reactive({
  name: '',
  primaryMetrics: ['read_7d', 'interact_7d'],
  groupBy: 'content_type'
})

const handleSubmit = async () => {
  const datasetId = route.query.dataset_id as string
  if (!datasetId) {
    ElMessage.error('缺少数据集ID')
    return
  }

  try {
    const analysis = await analysisStore.createAnalysis(datasetId, configForm.name, {
      primaryMetrics: configForm.primaryMetrics,
      groupBy: configForm.groupBy
    })
    ElMessage.success('分析任务已创建')
    router.push(`/analyses/${analysis.id}/results`)
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleCancel = () => {
  router.back()
}
</script>
