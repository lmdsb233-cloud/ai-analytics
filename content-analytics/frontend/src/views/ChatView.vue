<template>
  <div class="chat-view">
    <div class="chat-header">
      <h2>{{ conversation?.title || '对话' }}</h2>
      <el-tag v-if="conversation?.context_type === 'analysis_result'" type="info">
        分析结果讨论
      </el-tag>
      <el-tag v-else-if="conversation?.context_type === 'analysis'" type="success">
        分析任务对话
      </el-tag>
      <div
        class="chat-header-actions"
        v-if="conversation?.context_type === 'analysis_result'"
      >
        <el-button size="small" @click="openHistory">修改历史</el-button>
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="message.id"
        :class="['message', message.role]"
      >
        <div class="message-content">
          <div v-html="formatMessageContent(message.content)"></div>
          
          <!-- 如果消息包含修改建议，显示应用按钮 -->
          <div 
            v-if="message.role === 'assistant' && extractSuggestionUpdate(message.content)"
            class="suggestion-update-actions"
          >
            <el-divider />
            <div class="update-preview">
              <el-icon><EditPen /></el-icon>
              <span>AI 提供了修改建议</span>
            </div>
            <el-button 
              type="primary" 
              size="small"
              :loading="applyingUpdate === index"
              :disabled="applyingUpdate === index || isSuggestionApplied(message.content)"
              @click="applySuggestionUpdate(message.content, index)"
            >
              <el-icon><Check /></el-icon>
              {{ isSuggestionApplied(message.content) ? '已应用' : '应用修改到分析结果' }}
            </el-button>
          </div>
        </div>
        <div class="message-time">{{ formatTime(message.created_at) }}</div>
      </div>
      
      <div v-if="streaming" class="message assistant">
        <div class="message-content">
          <div v-html="formatMessageContent(streamingText)"></div>
        </div>
        <div class="streaming-indicator">正在输入...</div>
      </div>
    </div>
    
    <div class="chat-input-area">
      <div class="quick-actions" v-if="conversation?.context_type === 'analysis_result'">
        <el-button size="small" @click="sendQuickMessage('帮我重新写一下优化建议，更具体一些')">
          重写建议
        </el-button>
        <el-button size="small" @click="sendQuickMessage('这个建议不太适合，能换个角度吗？')">
          换个角度
        </el-button>
        <el-button size="small" @click="sendQuickMessage('帮我补充更多优化建议')">
          补充建议
        </el-button>
      </div>
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入消息，可以询问分析结果、要求修改建议等..."
        @keydown.ctrl.enter="sendMessage"
        :disabled="loading"
      />
      <div class="input-actions">
        <el-button @click="sendMessage" :loading="loading" type="primary">
          发送 (Ctrl+Enter)
        </el-button>
      </div>
    </div>

    <el-drawer v-model="historyVisible" title="修改历史" size="420px">
      <div class="history-content" v-loading="historyLoading">
        <div v-if="!historyItems.length" class="history-empty">暂无修改历史</div>
        <div v-else>
          <div v-for="item in historyItems" :key="item.id" class="history-item">
            <div class="history-meta">
              <span class="history-time">{{ formatDateTime(item.created_at) }}</span>
              <el-tag size="small" type="info">
                {{ item.action === 'rollback' ? '回退前快照' : '修改前快照' }}
              </el-tag>
            </div>
            <div class="history-summary">{{ item.summary || '（无一句话总结）' }}</div>
            <div class="history-actions">
              <el-button
                size="small"
                type="primary"
                :loading="rollbackLoadingId === item.id"
                @click="rollbackHistory(item)"
              >
                回退到此版本
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getConversation, sendMessage as sendMessageAPI } from '@/api/chat'
import {
  updatePostAIOutput,
  getPostAnalysisResult,
  getPostAIOutputHistory,
  rollbackPostAIOutput
} from '@/api/analyses'
import type { ConversationDetail, Message } from '@/api/chat'
import type { AIOutput, AIOutputHistory } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { EditPen, Check } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const conversationId = route.params.id as string

const conversation = ref<ConversationDetail | null>(null)
const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const streaming = ref(false)
const streamingText = ref('')
const pendingStreamText = ref('')
const streamFlushTimer = ref<number | null>(null)
const messagesContainer = ref<HTMLElement>()
const applyingUpdate = ref<number | null>(null)
const currentAIOutput = ref<AIOutput | null>(null)
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyItems = ref<AIOutputHistory[]>([])
const rollbackLoadingId = ref<string | null>(null)

// 存储关联的分析信息
const analysisContext = ref<{
  postId: string
  analysisId: string
  analysisResultId: string
} | null>(null)

const loadConversation = async () => {
  try {
    const res = await getConversation(conversationId)
    conversation.value = res.data
    messages.value = res.data.messages || []
    
    // 如果是分析结果对话，获取关联信息
    if (res.data.context_type === 'analysis_result' && res.data.context_analysis_result_id) {
      await loadAnalysisContext(res.data.context_analysis_result_id)
    }
    
    scrollToBottom()
  } catch (error: any) {
    console.error('加载对话失败:', error)
    ElMessage.error('加载对话失败')
  }
}

const loadAnalysisContext = async (analysisResultId: string) => {
  try {
    // 从后端获取分析结果的关联信息
    const { default: axios } = await import('@/api/index')
    const res = await axios.get(`/chat/analysis-results/${analysisResultId}/context`)
    if (res.data) {
      analysisContext.value = {
        postId: res.data.post_id,
        analysisId: res.data.analysis_id,
        analysisResultId: analysisResultId
      }
      await refreshCurrentAIOutput()
    }
  } catch (error) {
    console.error('获取分析上下文失败:', error)
  }
}

const refreshCurrentAIOutput = async () => {
  if (!analysisContext.value) return
  try {
    const res = await getPostAnalysisResult(
      analysisContext.value.postId,
      analysisContext.value.analysisId
    )
    currentAIOutput.value = res.data?.ai_output || null
  } catch (error) {
    console.error('获取当前 AI 输出失败:', error)
  }
}

const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return
  
  const userMessage = inputText.value
  inputText.value = ''
  
  await doSendMessage(userMessage)
}

const sendQuickMessage = async (message: string) => {
  if (loading.value) return
  await doSendMessage(message)
}

const doSendMessage = async (userMessage: string) => {
  // 添加用户消息到界面
  messages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: userMessage,
    created_at: new Date().toISOString()
  })
  
  scrollToBottom()
  loading.value = true
  streaming.value = true
  streamingText.value = ''
  pendingStreamText.value = ''
  if (streamFlushTimer.value !== null) {
    window.clearTimeout(streamFlushTimer.value)
    streamFlushTimer.value = null
  }
  
  try {
    await sendMessageAPI(conversationId, userMessage, {
      onStart: () => {},
      onChunk: (chunk) => {
        pendingStreamText.value += chunk
        scheduleStreamFlush()
      },
      onDone: () => {
        flushPendingStreamText()
        messages.value.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: streamingText.value,
          created_at: new Date().toISOString()
        })
        streaming.value = false
        streamingText.value = ''
        pendingStreamText.value = ''
        loading.value = false
        scrollToBottom()
        loadConversation()
      },
      onError: (error) => {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败: ' + error.message)
        loading.value = false
        streaming.value = false
        flushPendingStreamText()
      }
    })
  } catch (error: any) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
    loading.value = false
    streaming.value = false
    flushPendingStreamText()
  }
}

// 从消息中提取修改建议
const extractSuggestionUpdate = (content: string): any | null => {
  const match = content.match(/```json:suggestion_update\s*([\s\S]*?)\s*```/)
  if (match) {
    try {
      return JSON.parse(match[1])
    } catch (e) {
      console.error('解析修改建议失败:', e)
    }
  }
  return null
}

const isArrayEqual = (a?: string[] | null, b?: string[] | null) => {
  const arrA = a || []
  const arrB = b || []
  if (arrA.length !== arrB.length) return false
  return arrA.every((value, index) => value === arrB[index])
}

const isSuggestionApplied = (content: string): boolean => {
  const updateData = extractSuggestionUpdate(content)
  if (!updateData || !currentAIOutput.value) return false
  const current = currentAIOutput.value

  if (updateData.summary !== undefined && updateData.summary !== current.summary) {
    return false
  }
  if (
    updateData.strengths !== undefined &&
    !isArrayEqual(updateData.strengths, current.strengths)
  ) {
    return false
  }
  if (
    updateData.weaknesses !== undefined &&
    !isArrayEqual(updateData.weaknesses, current.weaknesses)
  ) {
    return false
  }
  if (
    updateData.suggestions !== undefined &&
    !isArrayEqual(updateData.suggestions, current.suggestions)
  ) {
    return false
  }

  return true
}

// 格式化消息内容（移除 JSON 块，转换换行）
const formatMessageContent = (content: string): string => {
  // 移除 suggestion_update JSON 块（但保留其他内容）
  let formatted = content.replace(/```json:suggestion_update\s*[\s\S]*?\s*```/g, '')
  // 转换换行
  formatted = formatted.replace(/\n/g, '<br>')
  return formatted
}

// 应用修改建议
const applySuggestionUpdate = async (content: string, index: number) => {
  const updateData = extractSuggestionUpdate(content)
  if (!updateData) {
    ElMessage.error('无法解析修改建议')
    return
  }
  if (isSuggestionApplied(content)) {
    ElMessage.info('该修改已应用')
    return
  }
  
  if (!analysisContext.value) {
    ElMessage.error('无法获取分析上下文，请刷新页面重试')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要将 AI 的修改建议应用到分析结果吗？这将更新保存的分析建议。',
      '确认应用修改',
      {
        confirmButtonText: '确定应用',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    applyingUpdate.value = index
    
    const res = await updatePostAIOutput(
      analysisContext.value.postId,
      analysisContext.value.analysisId,
      updateData
    )
    currentAIOutput.value = res.data

    ElMessage.success('修改已应用到分析结果')
    applyingUpdate.value = null
    await loadHistory()
    
  } catch (error: any) {
    applyingUpdate.value = null
    if (error !== 'cancel') {
      console.error('应用修改失败:', error)
      ElMessage.error(error.response?.data?.detail || '应用修改失败')
    }
  }
}

const loadHistory = async () => {
  if (!analysisContext.value) return
  historyLoading.value = true
  try {
    const res = await getPostAIOutputHistory(
      analysisContext.value.postId,
      analysisContext.value.analysisId
    )
    historyItems.value = res.data || []
  } catch (error) {
    console.error('获取修改历史失败:', error)
    ElMessage.error('获取修改历史失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistory = async () => {
  historyVisible.value = true
  await loadHistory()
}

const rollbackHistory = async (item: AIOutputHistory) => {
  if (!analysisContext.value) return
  try {
    await ElMessageBox.confirm(
      '确认回退到这个历史版本吗？当前内容将被覆盖。',
      '确认回退',
      {
        confirmButtonText: '确认回退',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    rollbackLoadingId.value = item.id
    const res = await rollbackPostAIOutput(
      analysisContext.value.postId,
      analysisContext.value.analysisId,
      item.id
    )
    currentAIOutput.value = res.data
    ElMessage.success('已回退到历史版本')
    rollbackLoadingId.value = null
    await loadHistory()
  } catch (error: any) {
    rollbackLoadingId.value = null
    if (error !== 'cancel') {
      console.error('回退失败:', error)
      ElMessage.error(error.response?.data?.detail || '回退失败')
    }
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const scheduleStreamFlush = () => {
  if (streamFlushTimer.value !== null) return
  streamFlushTimer.value = window.setTimeout(() => {
    flushPendingStreamText()
  }, 80)
}

const flushPendingStreamText = () => {
  if (streamFlushTimer.value !== null) {
    window.clearTimeout(streamFlushTimer.value)
    streamFlushTimer.value = null
  }
  if (!pendingStreamText.value) return
  streamingText.value += pendingStreamText.value
  pendingStreamText.value = ''
  scrollToBottom()
}

const formatTime = (time: string) => {
  return dayjs(time).format('HH:mm')
}

const formatDateTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  loadConversation()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.chat-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  gap: 12px;
}
.chat-header-actions {
  margin-left: auto;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
  word-wrap: break-word;
  line-height: 1.6;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.streaming-indicator {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.suggestion-update-actions {
  margin-top: 12px;
  padding-top: 8px;
}

.update-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #409eff;
  font-size: 13px;
  margin-bottom: 8px;
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.quick-actions {
  margin-bottom: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.input-actions {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}

.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}

.history-summary {
  font-size: 13px;
  color: #303133;
  margin-bottom: 8px;
}

.history-actions {
  display: flex;
  justify-content: flex-end;
}

.history-empty {
  color: #909399;
  text-align: center;
  padding: 24px 0;
}
</style>
