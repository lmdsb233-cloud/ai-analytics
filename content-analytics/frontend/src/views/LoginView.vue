<template>
  <div class="login-container">
    <!-- 左侧品牌区域 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="logo">
          <img src="/logo.png" alt="logo" class="logo-img" />
          <span class="logo-text">内容数据分析</span>
        </div>
        <h1 class="brand-title">让数据驱动内容增长</h1>
        <p class="brand-desc">智能分析笔记数据，AI辅助内容优化，助力账号快速成长</p>
        <div class="features">
          <div class="feature-item">
            <span class="feature-icon">📈</span>
            <span>数据可视化分析</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">🤖</span>
            <span>AI智能诊断建议</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">📋</span>
            <span>一键导出分析报告</span>
          </div>
        </div>
      </div>
      <div class="brand-decoration"></div>
    </div>
    
    <!-- 右侧登录区域 -->
    <div class="login-section">
      <div class="login-box">
        <h2 class="welcome-text">欢迎回来 👋</h2>
        <p class="welcome-desc">登录您的账号开始分析</p>
        
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" @submit.prevent="handleLogin">
              <el-form-item prop="username">
                <el-input v-model="loginForm.username" placeholder="请输入用户名" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="submit-btn">
                登 录
              </el-button>
            </el-form>
          </el-tab-pane>
          
          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" @submit.prevent="handleRegister">
              <el-form-item prop="username">
                <el-input v-model="registerForm.username" placeholder="请输入用户名" prefix-icon="User" size="large" />
              </el-form-item>
              <el-form-item prop="email">
                <el-input v-model="registerForm.email" placeholder="请输入邮箱" prefix-icon="Message" size="large" />
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-form-item prop="confirmPassword">
                <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" prefix-icon="Lock" size="large" show-password />
              </el-form-item>
              <el-button type="primary" size="large" :loading="loading" @click="handleRegister" class="submit-btn">
                注 册
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  void _rule
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await authStore.login(loginForm.username, loginForm.password)
      ElMessage.success('登录成功')
      router.push('/')
    } catch (error) {
      // Error handled by interceptor
    } finally {
      loading.value = false
    }
  })
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await authStore.register(registerForm.username, registerForm.email, registerForm.password)
      ElMessage.success('注册成功，请登录')
      activeTab.value = 'login'
      loginForm.username = registerForm.username
    } catch (error) {
      // Error handled by interceptor
    } finally {
      loading.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  height: 100vh;
  display: flex;
  background: #fff;
}

.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  
  .brand-content {
    position: relative;
    z-index: 2;
    padding: 60px;
    color: #fff;
    max-width: 500px;
  }
  
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 40px;
    
    .logo-img {
      width: 44px;
      height: 44px;
      object-fit: contain;
      flex-shrink: 0;
    }
    
    .logo-text {
      font-size: 24px;
      font-weight: 700;
    }
  }
  
  .brand-title {
    font-size: 42px;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 20px;
  }
  
  .brand-desc {
    font-size: 18px;
    opacity: 0.9;
    line-height: 1.6;
    margin-bottom: 40px;
  }
  
  .features {
    display: flex;
    flex-direction: column;
    gap: 16px;
    
    .feature-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 16px;
      padding: 12px 20px;
      background: rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      backdrop-filter: blur(10px);
      
      .feature-icon {
        font-size: 24px;
      }
    }
  }
  
  .brand-decoration {
    position: absolute;
    right: -100px;
    bottom: -100px;
    width: 400px;
    height: 400px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 50%;
  }
}

.login-section {
  flex: 0 0 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.login-box {
  width: 380px;
  padding: 40px;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 4px 30px rgba(255, 36, 66, 0.1);
  
  .welcome-text {
    font-size: 28px;
    font-weight: 700;
    color: #333;
    margin-bottom: 8px;
  }
  
  .welcome-desc {
    font-size: 14px;
    color: #999;
    margin-bottom: 32px;
  }
}

.login-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }
  
  :deep(.el-tabs__item) {
    font-size: 16px;
    font-weight: 500;
    color: #999;
    
    &.is-active {
      color: #ff2442;
    }
  }
  
  :deep(.el-tabs__active-bar) {
    background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
    height: 3px;
    border-radius: 2px;
  }
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 16px;
  border-radius: 12px !important;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
  padding: 8px 16px;
  border-radius: 12px !important;
}

@media (max-width: 1024px) {
  .brand-section {
    display: none;
  }
  
  .login-section {
    flex: 1;
  }
}
</style>
