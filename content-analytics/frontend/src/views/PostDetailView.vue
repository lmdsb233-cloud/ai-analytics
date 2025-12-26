<template>
  <div class="page-container">
    <div class="page-header">
      <h1>笔记详情</h1>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card">
          <h3>基本信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="笔记ID">{{ post?.data_id }}</el-descriptions-item>
            <el-descriptions-item label="发文时间">{{ formatDate(post?.publish_time) }}</el-descriptions-item>
            <el-descriptions-item label="内容形式">{{ post?.content_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发文类型">{{ post?.post_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="素材来源">{{ post?.source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="款式信息">{{ post?.style_info || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="card" style="margin-top: 20px">
          <h3>指标数据</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="7天阅读">{{ post?.read_7d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="14天阅读">{{ post?.read_14d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="7天互动">{{ post?.interact_7d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="14天互动">{{ post?.interact_14d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="7天好物访问">{{ post?.visit_7d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="14天好物访问">{{ post?.visit_14d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="7天好物想要">{{ post?.want_7d ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="14天好物想要">{{ post?.want_14d ?? '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="card ai-output">
          <h3>
            <el-icon><MagicStick /></el-icon>
            AI分析结果
          </h3>
          
          <template v-if="aiOutput">
            <div class="ai-section">
              <h4>一句话总结</h4>
              <p>{{ aiOutput.summary || '暂无' }}</p>
            </div>

            <div class="ai-section">
              <h4>优点</h4>
              <ul v-if="aiOutput.strengths?.length">
                <li v-for="(item, idx) in aiOutput.strengths" :key="idx">{{ item }}</li>
              </ul>
              <p v-else class="text-muted">暂无</p>
            </div>

            <div class="ai-section">
              <h4>问题</h4>
              <ul v-if="aiOutput.weaknesses?.length">
                <li v-for="(item, idx) in aiOutput.weaknesses" :key="idx">{{ item }}</li>
              </ul>
              <p v-else class="text-muted">暂无</p>
            </div>

            <div class="ai-section">
              <h4>优化建议</h4>
              <ul v-if="aiOutput.suggestions?.length">
                <li v-for="(item, idx) in aiOutput.suggestions" :key="idx">{{ item }}</li>
              </ul>
              <p v-else class="text-muted">暂无</p>
            </div>

            <div class="ai-meta">
              <span>模型: {{ aiOutput.model_name }}</span>
              <span>生成时间: {{ formatDate(aiOutput.created_at) }}</span>
            </div>
          </template>
          
          <el-empty v-else description="暂无AI分析结果" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MagicStick } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()

const postId = route.params.id as string
const analysisId = route.query.analysis_id as string

const post = computed(() => analysisStore.currentPost)
const aiOutput = computed(() => analysisStore.currentAIOutput)

onMounted(async () => {
  await analysisStore.fetchPost(postId)
  if (analysisId) {
    await analysisStore.fetchAIOutput(postId, analysisId)
  }
})

const formatDate = (date?: string) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}
</script>

<style lang="scss" scoped>
.card {
  h3 {
    margin-bottom: 16px;
    font-size: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.ai-output {
  .ai-section {
    margin-bottom: 20px;
    
    h4 {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }
    
    p {
      margin: 0;
      line-height: 1.6;
    }
    
    ul {
      margin: 0;
      padding-left: 20px;
      
      li {
        line-height: 1.8;
      }
    }
  }
  
  .ai-meta {
    margin-top: 20px;
    padding-top: 12px;
    border-top: 1px solid #ebeef5;
    font-size: 12px;
    color: #909399;
    display: flex;
    gap: 20px;
  }
}

.text-muted {
  color: #909399;
}
</style>
