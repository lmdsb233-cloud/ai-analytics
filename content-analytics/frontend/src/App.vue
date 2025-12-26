<template>
  <el-config-provider :locale="zhCn">
    <div v-if="loading" class="app-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>
    <router-view v-else />
  </el-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(true)

// 带超时的Promise
const withTimeout = <T>(promise: Promise<T>, ms: number): Promise<T> => {
  const timeout = new Promise<never>((_, reject) => 
    setTimeout(() => reject(new Error('timeout')), ms)
  )
  return Promise.race([promise, timeout])
}

onMounted(async () => {
  // 如果有token，尝试获取用户信息（最多等2秒）
  if (authStore.token) {
    try {
      await withTimeout(authStore.fetchUser(), 2000)
    } catch {
      // 超时或失败时不阻塞加载
    }
  }
  loading.value = false
})
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}

.app-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #fafafa;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f0f0f0;
  border-top-color: #ff2442;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.app-loading p {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}
</style>
