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
            <el-descriptions-item label="笔记链接">
              <a 
                v-if="post?.publish_link" 
                :href="post.publish_link" 
                target="_blank" 
                class="note-link"
              >
                <el-icon><Link /></el-icon>
                查看原笔记
              </a>
              <span v-else>-</span>
            </el-descriptions-item>
            <el-descriptions-item label="发文时间">{{ formatDate(post?.publish_time) }}</el-descriptions-item>
            <el-descriptions-item label="内容形式">{{ post?.content_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="发文类型">{{ post?.post_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="素材来源">{{ post?.source || '-' }}</el-descriptions-item>
            <el-descriptions-item label="款式信息">{{ post?.style_info || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="card" style="margin-top: 20px">
          <h3>抓取的图文</h3>
          <template v-if="post?.content_title || post?.content_text || post?.cover_image || post?.image_urls?.length">
            <div class="media-section">
              <div class="media-field">
                <div class="label">标题</div>
                <div class="value">{{ post?.content_title || '-' }}</div>
              </div>
              <div class="media-field">
                <div class="label">正文</div>
                <div class="value content-text">{{ post?.content_text || '-' }}</div>
              </div>
              <div v-if="allImages.length" class="media-field">
                <div class="label">图片</div>
                <div class="image-grid">
                  <el-image
                    v-for="(url, idx) in allImages"
                    :key="url + '-' + idx"
                    class="media-image"
                    :src="url"
                    :preview-src-list="allImages"
                    fit="cover"
                  />
                </div>
              </div>
            </div>
          </template>
          <el-empty v-else description="暂无抓取内容" />
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
          <div class="ai-header">
            <h3>
              <el-icon><MagicStick /></el-icon>
              AI分析结果
            </h3>
            <el-button 
              v-if="aiOutput && analysisId"
              type="primary"
              :icon="ChatRound"
              @click="startConversation"
              size="small"
            >
              与AI讨论
            </el-button>
          </div>
          
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
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MagicStick, Link, ChatRound } from '@element-plus/icons-vue'
import { useAnalysisStore } from '@/stores/analysis'
import { createConversationFromAnalysisResult } from '@/api/chat'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const analysisStore = useAnalysisStore()

const postId = route.params.id as string
const analysisId = route.query.analysis_id as string

const post = computed(() => analysisStore.currentPost)
const aiOutput = computed(() => analysisStore.currentAIOutput)

// 合并封面图和图片列表，去重
const allImages = computed(() => {
  const images: string[] = []
  if (post.value?.image_urls?.length) {
    images.push(...post.value.image_urls)
  }
  // 如果只有封面图没有图片列表，则使用封面图
  if (!images.length && post.value?.cover_image) {
    images.push(post.value.cover_image)
  }
  return images
})

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

// 启动对话
const startConversation = async () => {
  if (!analysisId || !aiOutput.value) {
    ElMessage.warning('需要分析结果才能启动对话')
    return
  }
  
  try {
    // 获取 analysis_result_id（需要通过analysis_id和post_id查找）
    const analysisResultId = await getAnalysisResultId()
    
    if (!analysisResultId) {
      ElMessage.error('无法获取分析结果ID')
      return
    }
    
    // 创建对话
    const res = await createConversationFromAnalysisResult(analysisResultId)
    
    // 跳转到对话页面
    router.push(`/chat/${res.data.id}`)
  } catch (error: any) {
    console.error('启动对话失败:', error)
    ElMessage.error(error.response?.data?.detail || '启动对话失败')
  }
}

// 辅助函数：获取分析结果ID
const getAnalysisResultId = async () => {
  try {
    // 调用API获取analysis_result_id
    const { default: axios } = await import('@/api/index')
    const res = await axios.get(`/posts/${postId}/analysis-result-id`, {
      params: { analysis_id: analysisId }
    })
    return res.data.analysis_result_id
  } catch (error) {
    console.error('获取分析结果ID失败:', error)
    return null
  }
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
  .ai-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
  
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

.media-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.media-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.media-field .label {
  font-size: 13px;
  color: #909399;
}

.media-field .value {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
}

.content-text {
  white-space: pre-wrap;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.media-image {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
}

.note-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  
  &:hover {
    color: #66b1ff;
    text-decoration: underline;
  }
}
</style>
