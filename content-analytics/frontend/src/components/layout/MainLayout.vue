<template>
  <el-container class="main-layout">
    <el-aside width="240px" class="sidebar">
      <div class="logo">
        <img src="/logo.png" alt="logo" class="logo-img" />
        <span class="logo-text">内容数据分析</span>
      </div>
      
      <div class="menu-section">
        <div class="menu-label">数据管理</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#666"
          active-text-color="#ff2442"
        >
          <el-menu-item index="/datasets">
            <el-icon><FolderOpened /></el-icon>
            <span>数据集</span>
          </el-menu-item>
          <el-menu-item index="/analyses">
            <el-icon><DataAnalysis /></el-icon>
            <span>分析任务</span>
          </el-menu-item>
          <el-menu-item index="/exports">
            <el-icon><Download /></el-icon>
            <span>导出报告</span>
          </el-menu-item>
        </el-menu>
        
        <div class="menu-label">系统设置</div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#666"
          active-text-color="#ff2442"
        >
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>AI配置</span>
          </el-menu-item>
        </el-menu>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <el-avatar :size="36" class="user-avatar">
            {{ authStore.user?.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="user-detail">
            <span class="user-name">{{ authStore.user?.username }}</span>
            <span class="user-role">管理员</span>
          </div>
        </div>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <h2 class="page-title">{{ currentRoute }}</h2>
        </div>
        <div class="header-right">
          <el-button class="logout-btn" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { FolderOpened, DataAnalysis, Download, Setting, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

const routeNames: Record<string, string> = {
  '/datasets': '数据集管理',
  '/analyses': '分析任务',
  '/exports': '导出报告',
  '/settings': 'AI设置'
}

const currentRoute = computed(() => {
  const path = route.path.split('/')[1]
  return routeNames[`/${path}`] || ''
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  
  .logo {
    height: 70px;
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 10px;
    border-bottom: 1px solid #f0f0f0;
    
    .logo-img {
      width: 32px;
      height: 32px;
      object-fit: contain;
    }
    
    .logo-text {
      font-size: 16px;
      font-weight: 700;
      background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }
  
  .menu-section {
    flex: 1;
    padding: 16px 12px;
    overflow-y: auto;
  }
  
  .menu-label {
    font-size: 12px;
    color: #999;
    font-weight: 500;
    padding: 12px 12px 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  :deep(.el-menu) {
    border: none;
    
    .el-menu-item {
      height: 44px;
      line-height: 44px;
      margin: 4px 0;
      border-radius: 10px;
      font-weight: 500;
      transition: all 0.2s ease;
      
      &:hover {
        background: #fff0f1;
        color: #ff2442;
      }
      
      &.is-active {
        background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
        color: #fff !important;
        
        .el-icon {
          color: #fff;
        }
      }
      
      .el-icon {
        font-size: 18px;
        margin-right: 10px;
      }
    }
  }
  
  .sidebar-footer {
    padding: 16px;
    border-top: 1px solid #f0f0f0;
    
    .user-info {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      background: #fafafa;
      border-radius: 12px;
    }
    
    .user-avatar {
      background: linear-gradient(135deg, #ff2442 0%, #ff6b81 100%);
      color: #fff;
      font-weight: 600;
    }
    
    .user-detail {
      display: flex;
      flex-direction: column;
      
      .user-name {
        font-weight: 600;
        color: #333;
        font-size: 14px;
      }
      
      .user-role {
        font-size: 12px;
        color: #999;
      }
    }
  }
}

.header {
  height: 70px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #f0f0f0;
  
  .page-title {
    font-size: 20px;
    font-weight: 700;
    color: #333;
  }
  
  .logout-btn {
    color: #666;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    
    &:hover {
      color: #ff2442;
      border-color: #ff2442;
      background: #fff0f1;
    }
  }
}

.main-content {
  background: #fafafa;
  padding: 24px;
  overflow-y: auto;
}
</style>
