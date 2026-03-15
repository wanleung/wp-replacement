import apiClient from './client'
import type { Media, MediaListOut } from '@/types'

export const mediaApi = {
  list: async (page = 1, per_page = 20, mime_type?: string): Promise<MediaListOut> => {
    const { data } = await apiClient.get<MediaListOut>('/media', {
      params: { page, per_page, mime_type },
    })
    return data
  },

  get: async (id: number): Promise<Media> => {
    const { data } = await apiClient.get<Media>(`/media/${id}`)
    return data
  },

  upload: async (file: File, onProgress?: (pct: number) => void): Promise<Media> => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<Media>('/media', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100))
        }
      },
    })
    return data
  },

  update: async (id: number, payload: { post_title?: string; alt_text?: string; caption?: string }): Promise<Media> => {
    const { data } = await apiClient.put<Media>(`/media/${id}`, payload)
    return data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/media/${id}`)
  },
}
