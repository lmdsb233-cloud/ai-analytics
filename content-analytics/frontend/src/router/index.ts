import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/datasets'
      },
      {
        path: 'datasets',
        name: 'Datasets',
        component: () => import('@/views/DatasetsView.vue')
      },
      {
        path: 'analyses',
        name: 'Analyses',
        component: () => import('@/views/AnalysesView.vue')
      },
      {
        path: 'analyses/:id/config',
        name: 'AnalysisConfig',
        component: () => import('@/views/AnalysisConfigView.vue')
      },
      {
        path: 'analyses/:id/results',
        name: 'AnalysisResults',
        component: () => import('@/views/AnalysisResultView.vue')
      },
      {
        path: 'posts/:id',
        name: 'PostDetail',
        component: () => import('@/views/PostDetailView.vue')
      },
      {
        path: 'exports',
        name: 'Exports',
        component: () => import('@/views/ExportView.vue')
      },
      {
        path: 'screenshot',
        name: 'Screenshot',
        component: () => import('@/views/ScreenshotView.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue')
      },
      {
        path: 'chat/:id',
        name: 'Chat',
        component: () => import('@/views/ChatView.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  void from
  
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
