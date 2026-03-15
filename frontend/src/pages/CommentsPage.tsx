import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, X, Trash2, MessageSquare } from 'lucide-react'
import apiClient from '@/api/client'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Spinner from '@/components/Spinner'
import type { CommentListOut, Comment } from '@/types'

export default function CommentsPage() {
  const [page, setPage] = useState(1)
  const [approvedOnly, setApprovedOnly] = useState(false)
  const queryClient = useQueryClient()

  // We need a post_id for the comments endpoint; use 0 to list all comments via custom route
  // For a global comments view, we call the endpoint with a broad query
  const { data, isLoading } = useQuery({
    queryKey: ['comments-all', page, approvedOnly],
    queryFn: async () => {
      const { data } = await apiClient.get<CommentListOut>('/comments', {
        params: { post_id: 0, page, per_page: 20, approved_only: approvedOnly },
      })
      return data
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, approved }: { id: number; approved: string }) =>
      apiClient.put(`/comments/${id}`, { comment_approved: approved }),
    onSuccess: () => {
      toast.success('Comment updated')
      queryClient.invalidateQueries({ queryKey: ['comments-all'] })
    },
    onError: () => toast.error('Failed to update comment'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/comments/${id}`),
    onSuccess: () => {
      toast.success('Comment deleted')
      queryClient.invalidateQueries({ queryKey: ['comments-all'] })
    },
    onError: () => toast.error('Failed to delete comment'),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MessageSquare size={22} className="text-blue-500" />
          Comments
        </h1>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            checked={approvedOnly}
            onChange={(e) => setApprovedOnly(e.target.checked)}
          />
          Approved only
        </label>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <Spinner className="w-7 h-7 text-blue-600" />
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {data?.items.length === 0 && (
              <p className="py-12 text-center text-gray-400">No comments found.</p>
            )}
            {data?.items.map((comment) => (
              <div key={comment.comment_ID} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0 text-gray-500 font-medium text-sm">
                    {comment.comment_author?.[0]?.toUpperCase() ?? '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-medium text-gray-800 text-sm">{comment.comment_author}</span>
                      {comment.comment_author_email && (
                        <span className="text-xs text-gray-400">{comment.comment_author_email}</span>
                      )}
                      <span
                        className={`badge ${comment.comment_approved === '1' ? 'badge-green' : 'badge-yellow'}`}
                      >
                        {comment.comment_approved === '1' ? 'Approved' : 'Pending'}
                      </span>
                      <span className="text-xs text-gray-400 ml-auto">
                        {format(new Date(comment.comment_date), 'MMM d, yyyy HH:mm')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">{comment.comment_content}</p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {comment.comment_approved !== '1' ? (
                      <button
                        title="Approve"
                        onClick={() => updateMutation.mutate({ id: comment.comment_ID, approved: '1' })}
                        className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                      >
                        <Check size={15} />
                      </button>
                    ) : (
                      <button
                        title="Unapprove"
                        onClick={() => updateMutation.mutate({ id: comment.comment_ID, approved: '0' })}
                        className="p-1.5 text-gray-400 hover:text-yellow-600 hover:bg-yellow-50 rounded-lg"
                      >
                        <X size={15} />
                      </button>
                    )}
                    <button
                      title="Delete"
                      onClick={() => {
                        if (!window.confirm('Delete this comment?')) return
                        deleteMutation.mutate(comment.comment_ID)
                      }}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {data && data.total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <p className="text-sm text-gray-500">{data.total} comments total</p>
            <div className="flex gap-2">
              <button className="btn-secondary text-xs py-1.5 px-3" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
              <button className="btn-secondary text-xs py-1.5 px-3" disabled={data.items.length < 20} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
