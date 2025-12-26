<template>
  <div class="screenshot-view">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>截图分析</span>
          <el-button type="primary" @click="handleUpload" :loading="analyzing">
            {{ analyzing ? '分析中...' : '开始分析' }}
          </el-button>
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        class="screenshot-uploader"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        accept="image/*"
        drag
      >
        <img v-if="imageUrl" :src="imageUrl" class="screenshot-image" />
        <div v-else class="upload-placeholder">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">拖拽图片到此处或点击上传</div>
          <div class="upload-tip">支持 PNG、JPG、JPEG 格式</div>
        </div>
      </el-upload>
    </el-card>

    <el-card v-if="analysisResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>分析结果</span>
          <el-tag type="info">{{ analysisResult.model_name }}</el-tag>
        </div>
      </template>

      <div class="analysis-content">
        <div class="section">
          <h3>总结</h3>
          <p class="summary">{{ analysisResult.summary }}</p>
        </div>

        <div class="section">
          <h3>优点</h3>
          <ul class="list">
            <li v-for="(item, index) in analysisResult.strengths" :key="'strength-' + index">
              {{ item }}
            </li>
          </ul>
        </div>

        <div class="section">
          <h3>问题</h3>
          <ul class="list">
            <li v-for="(item, index) in analysisResult.weaknesses" :key="'weakness-' + index">
              {{ item }}
            </li>
          </ul>
        </div>

        <div class="section">
          <h3>优化建议</h3>
          <ul class="list">
            <li v-for="(item, index) in analysisResult.suggestions" :key="'suggestion-' + index">
              {{ item }}
            </li>
          </ul>
        </div>

        <div v-if="analysisResult.tokens_used" class="tokens-info">
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="Prompt Tokens">
              {{ analysisResult.tokens_used.prompt_tokens }}
            </el-descriptions-item>
            <el-descriptions-item label="Completion Tokens">
              {{ analysisResult.tokens_used.completion_tokens }}
            </el-descriptions-item>
            <el-descriptions-item label="Total Tokens">
              {{ analysisResult.tokens_used.total_tokens }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { analyzeScreenshot, type ScreenshotAnalysisResponse } from '@/api/screenshots'

const uploadRef = ref()
const imageUrl = ref('')
const selectedFile = ref<File | null>(null)
const analyzing = ref(false)
const analysisResult = ref<ScreenshotAnalysisResponse['data'] | null>(null)

const handleFileChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    imageUrl.value = e.target?.result as string
    selectedFile.value = file.raw
  }
  reader.readAsDataURL(file.raw)
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择图片')
    return
  }

  analyzing.value = true
  try {
    const response = await analyzeScreenshot(selectedFile.value)
    if (response.success) {
      analysisResult.value = response.data
      ElMessage.success('分析完成')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '分析失败')
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.screenshot-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-card {
  margin-bottom: 20px;
}

.screenshot-uploader {
  width: 100%;
}

.screenshot-image {
  width: 100%;
  max-height: 600px;
  object-fit: contain;
  display: block;
}

.upload-placeholder {
  padding: 60px 0;
  text-align: center;
}

.upload-icon {
  font-size: 67px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.result-card {
  margin-bottom: 20px;
}

.analysis-content {
  padding: 20px 0;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #ff5a77;
}

.summary {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list li {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  padding-left: 20px;
  position: relative;
}

.list li::before {
  content: '·';
  position: absolute;
  left: 8px;
  color: #ff5a77;
  font-weight: bold;
}

.tokens-info {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}
</style>