import apiClient from './client'
import type { Post, PostListOut, PostCreatePayload, PostUpdatePayload } from '@/types'

export interface ListPostsParams {
  page?: number
  per_page?: number
  status?: string
  search?: string
  category_id?: number
}

export const postsApi = {
  list: async (params: ListPostsParams = {}): Promise<PostListOut> => {
    const { data } = await apiClient.get<PostListOut>('/posts', { params })
    return data
  },

  get: async (id: number): Promise<Post> => {
    const { data } = await apiClient.get<Post>(`/posts/${id}`)
    return data
  },

  create: async (payload: PostCreatePayload): Promise<Post> => {
    const { data } = await apiClient.post<Post>('/posts', payload)
    return data
  },

  update: async (id: number, payload: PostUpdatePayload): Promise<Post> => {
    const { data } = await apiClient.put<Post>(`/posts/${id}`, payload)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/posts/${id}`)
  },

  // Pages
  listPages: async (params: ListPostsParams = {}): Promise<PostListOut> => {
    const { data } = await apiClient.get<PostListOut>('/pages', { params })
    return data
  },

  getPage: async (id: number): Promise<Post> => {
    const { data } = await apiClient.get<Post>(`/pages/${id}`)
    return data
  },

  createPage: async (payload: PostCreatePayload): Promise<Post> => {
    const { data } = await apiClient.post<Post>('/pages', payload)
    return data
  },

  updatePage: async (id: number, payload: PostUpdatePayload): Promise<Post> => {
    const { data } = await apiClient.put<Post>(`/pages/${id}`, payload)
    return data
  },

  deletePage: async (id: number): Promise<void> => {
    await apiClient.delete(`/pages/${id}`)
  },
}
