import apiClient from './client'
import type { Term, TermListOut } from '@/types'

export interface TermCreatePayload {
  name: string
  slug?: string
  description?: string
  parent?: number
}

export const taxonomyApi = {
  // Categories
  listCategories: async (search = ''): Promise<TermListOut> => {
    const { data } = await apiClient.get<TermListOut>('/categories', { params: { search } })
    return data
  },

  createCategory: async (payload: TermCreatePayload): Promise<Term> => {
    const { data } = await apiClient.post<Term>('/categories', payload)
    return data
  },

  updateCategory: async (id: number, payload: Partial<TermCreatePayload>): Promise<Term> => {
    const { data } = await apiClient.put<Term>(`/categories/${id}`, payload)
    return data
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}`)
  },

  // Tags
  listTags: async (search = ''): Promise<TermListOut> => {
    const { data } = await apiClient.get<TermListOut>('/tags', { params: { search } })
    return data
  },

  createTag: async (payload: TermCreatePayload): Promise<Term> => {
    const { data } = await apiClient.post<Term>('/tags', payload)
    return data
  },

  updateTag: async (id: number, payload: Partial<TermCreatePayload>): Promise<Term> => {
    const { data } = await apiClient.put<Term>(`/tags/${id}`, payload)
    return data
  },

  deleteTag: async (id: number): Promise<void> => {
    await apiClient.delete(`/tags/${id}`)
  },
}
