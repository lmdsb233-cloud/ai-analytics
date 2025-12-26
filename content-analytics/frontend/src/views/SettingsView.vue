<template>
  <div class="settings-page fade-in">
    <!-- AI配置卡片 -->
    <div class="config-card">
      <div class="card-header">
        <div class="header-icon">🤖</div>
        <div class="header-text">
          <h3>AI 服务配置</h3>
          <p>配置AI分析服务的API密钥</p>
        </div>
      </div>

      <div class="tip-box">
        <div class="tip-icon">💡</div>
        <div class="tip-content">
          <p><strong>如何获取API密钥？</strong></p>
          <p>
            <span class="provider-tag deepseek">DeepSeek</span>
            访问 <a href="https://platform.deepseek.com/" target="_blank">platform.deepseek.com</a> 注册获取
          </p>
          <p>
            <span class="provider-tag openai">OpenAI</span>
            访问 <a href="https://platform.openai.com/" target="_blank">platform.openai.com</a> 注册获取
          </p>
          <p>
            <span class="provider-tag iflow">iFlow</span>
            访问 <a href="https://iflow.cn/" target="_blank">iflow.cn</a> 注册获取
          </p>
        </div>
      </div>

      <el-form :model="form" label-position="top" v-loading="loading" class="settings-form">
        <div class="form-section">
          <div class="section-title">选择AI服务商</div>
          <div class="provider-cards">
            <div 
              class="provider-card" 
              :class="{ active: form.ai_provider === 'deepseek' }"
              @click="form.ai_provider = 'deepseek'"
            >
              <div class="provider-icon">🚀</div>
              <div class="provider-info">
                <span class="provider-name">DeepSeek</span>
                <span class="provider-desc">推荐，性价比高</span>
              </div>
              <div class="check-icon" v-if="form.ai_provider === 'deepseek'">✓</div>
            </div>
            <div 
              class="provider-card" 
              :class="{ active: form.ai_provider === 'openai' }"
              @click="form.ai_provider = 'openai'"
            >
              <div class="provider-icon">🧠</div>
              <div class="provider-info">
                <span class="provider-name">OpenAI</span>
                <span class="provider-desc">GPT-4 强大能力</span>
              </div>
              <div class="check-icon" v-if="form.ai_provider === 'openai'">✓</div>
            </div>
            <div 
              class="provider-card" 
              :class="{ active: form.ai_provider === 'iflow' }"
              @click="form.ai_provider = 'iflow'"
            >
              <div class="provider-icon">⚡</div>
              <div class="provider-info">
                <span class="provider-name">iFlow</span>
                <span class="provider-desc">Kimi 多模态</span>
              </div>
              <div class="check-icon" v-if="form.ai_provider === 'iflow'">✓</div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <div class="section-title">API密钥配置</div>
          
          <div class="key-input-group">
            <label>DeepSeek API密钥</label>
            <div class="input-with-status">
              <el-input
                v-model="form.deepseek_api_key"
                type="password"
                show-password
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="large"
              />
              <span class="status-tag" :class="settings?.has_deepseek_key ? 'configured' : 'not-configured'">
                {{ settings?.has_deepseek_key ? '✓ 已配置' : '未配置' }}
              </span>
            </div>
          </div>

          <div class="key-input-group">
            <label>OpenAI API密钥</label>
            <div class="input-with-status">
              <el-input
                v-model="form.openai_api_key"
                type="password"
                show-password
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="large"
              />
              <span class="status-tag" :class="settings?.has_openai_key ? 'configured' : 'not-configured'">
                {{ settings?.has_openai_key ? '✓ 已配置' : '未配置' }}
              </span>
            </div>
          </div>

          <div class="key-input-group">
            <label>iFlow API密钥</label>
            <div class="input-with-status">
              <el-input
                v-model="form.iflow_api_key"
                type="password"
                show-password
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="large"
              />
              <span class="status-tag" :class="settings?.has_iflow_key ? 'configured' : 'not-configured'">
                {{ settings?.has_iflow_key ? '✓ 已配置' : '未配置' }}
              </span>
            </div>
          </div>

          <div class="key-input-group" v-if="form.ai_provider === 'iflow'">
            <label>iFlow 模型（默认 kimi-k2-0905）</label>
            <div class="input-with-status">
              <el-input
                v-model="form.iflow_model"
                placeholder="kimi-k2-0905"
                size="large"
              />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <el-button type="primary" size="large" @click="saveSettings" :loading="saving">
            保存配置
          </el-button>
          <el-button size="large" @click="testKey" :loading="testing">
            测试连接
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- 使用指南卡片 -->
    <div class="guide-card">
      <div class="card-header">
        <div class="header-icon">📖</div>
        <div class="header-text">
          <h3>快速上手指南</h3>
          <p>4步完成小红书数据分析</p>
        </div>
      </div>

      <div class="guide-steps">
        <div class="guide-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>上传数据</h4>
            <p>在数据集页面上传小红书导出的Excel文件</p>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>创建分析</h4>
            <p>选择数据集创建分析任务，自动计算各项指标</p>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>AI诊断</h4>
            <p>AI为每条笔记生成优劣势分析和优化建议</p>
          </div>
        </div>
        <div class="guide-step">
          <div class="step-number">4</div>
          <div class="step-content">
            <h4>导出报告</h4>
            <p>一键导出完整分析报告</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi, type Settings } from '@/api/settings'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const settings = ref<Settings | null>(null)

const form = reactive({
  ai_provider: 'deepseek',
  deepseek_api_key: '',
  openai_api_key: '',
  iflow_api_key: '',
  iflow_model: 'kimi-k2-0905'
})

const fetchSettings = async () => {
  loading.value = true
  try {
    const res = await settingsApi.getSettings()
    settings.value = res.data
    form.ai_provider = res.data.ai_provider
    form.iflow_model = res.data.iflow_model || 'kimi-k2-0905'
  } catch (error) {
    console.error('获取设置失败', error)
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const updateData: any = {
      ai_provider: form.ai_provider
    }
    if (form.deepseek_api_key) {
      updateData.deepseek_api_key = form.deepseek_api_key
    }
    if (form.openai_api_key) {
      updateData.openai_api_key = form.openai_api_key
    }
    if (form.iflow_api_key) {
      updateData.iflow_api_key = form.iflow_api_key
    }
    if (form.ai_provider === 'iflow') {
      updateData.iflow_model = form.iflow_model || 'kimi-k2-0905'
    }
    
    const res = await settingsApi.updateSettings(updateData)
    settings.value = res.data
    form.deepseek_api_key = ''
    form.openai_api_key = ''
    form.iflow_api_key = ''
    ElMessage.success('设置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testKey = async () => {
  testing.value = true
  try {
    await settingsApi.testApiKey()
    ElMessage.success('API密钥配置正确')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '测试失败')
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style lang="scss" scoped>
.settings-page {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
  max-width: 1200px;
}

.config-card, .guide-card {
  background: #fff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 2px 16px rgba(255, 36, 66, 0.06);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  
  .header-icon {
    font-size: 32px;
  }
  
  .header-text {
    h3 {
      font-size: 20px;
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

.tip-box {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fff5f6 0%, #fff 100%);
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid #ffe4e6;
  
  .tip-icon {
    font-size: 24px;
  }
  
  .tip-content {
    p {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      a {
        color: #ff2442;
        text-decoration: underline;
      }
    }
  }
  
  .provider-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 8px;
    
    &.deepseek {
      background: #e8f5e9;
      color: #2e7d32;
    }
    
    &.openai {
      background: #e3f2fd;
      color: #1565c0;
    }
    
    &.iflow {
      background: #fff3e0;
      color: #e65100;
    }
  }
}

.form-section {
  margin-bottom: 28px;
  
  .section-title {
    font-size: 15px;
    font-weight: 600;
    color: #333;
    margin-bottom: 16px;
  }
}

.provider-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.provider-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border: 2px solid #f0f0f0;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  
  &:hover {
    border-color: #ffcdd2;
    background: #fff5f6;
  }
  
  &.active {
    border-color: #ff2442;
    background: linear-gradient(135deg, #fff5f6 0%, #fff 100%);
  }
  
  .provider-icon {
    font-size: 28px;
  }
  
  .provider-info {
    display: flex;
    flex-direction: column;
    
    .provider-name {
      font-weight: 600;
      color: #333;
    }
    
    .provider-desc {
      font-size: 12px;
      color: #999;
      margin-top: 2px;
    }
  }
  
  .check-icon {
    position: absolute;
    right: 16px;
    width: 24px;
    height: 24px;
    background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
  }
}

.key-input-group {
  margin-bottom: 20px;
  
  label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: #666;
    margin-bottom: 8px;
  }
  
  .input-with-status {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .status-tag {
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 20px;
    white-space: nowrap;
    
    &.configured {
      background: #e8f5e9;
      color: #2e7d32;
    }
    
    &.not-configured {
      background: #f5f5f5;
      color: #999;
    }
  }
  
  :deep(.el-input) {
    flex: 1;
    max-width: 400px;
  }
}

.form-actions {
  display: flex;
  gap: 12px;
  padding-top: 8px;
}

.guide-card {
  height: fit-content;
  position: sticky;
  top: 24px;
}

.guide-steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.guide-step {
  display: flex;
  gap: 16px;
  
  .step-number {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
    color: #fff;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
  }
  
  .step-content {
    h4 {
      font-size: 15px;
      font-weight: 600;
      color: #333;
      margin-bottom: 4px;
    }
    
    p {
      font-size: 13px;
      color: #999;
      line-height: 1.5;
    }
  }
}

@media (max-width: 900px) {
  .settings-page {
    grid-template-columns: 1fr;
  }
  
  .guide-card {
    position: static;
  }
}
</style>
