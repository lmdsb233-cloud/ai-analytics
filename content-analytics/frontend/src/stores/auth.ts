import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUser()
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password })
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await authApi.getCurrentUser()
      user.value = res.data
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 401) {
        logout()
      }
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    fetchUser,
    logout
  }
})
