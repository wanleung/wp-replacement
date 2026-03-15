import apiClient from './client'
import type { User } from '@/types'

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', { username, password })
    return data
  },

  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/users/me')
    return data
  },

  updateMe: async (payload: { display_name?: string; user_email?: string; password?: string }): Promise<User> => {
    const { data } = await apiClient.put<User>('/users/me', payload)
    return data
  },
}
