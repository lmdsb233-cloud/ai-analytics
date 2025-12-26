import request from './index'
import type { ApiResponse, User, LoginForm, RegisterForm } from '@/types'

export function login(data: LoginForm): Promise<ApiResponse<{ access_token: string }>> {
  return request.post('/auth/login', data)
}

export function register(data: RegisterForm): Promise<ApiResponse<User>> {
  return request.post('/auth/register', data)
}

export function getCurrentUser(): Promise<ApiResponse<User>> {
  return request.get('/auth/me')
}
