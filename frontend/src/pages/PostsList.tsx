import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Edit2, Trash2, Eye } from 'lucide-react'
import { postsApi } from '@/api/posts'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Spinner from '@/components/Spinner'
import type { Post } from '@/types'

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'publish', label: 'Published' },
  { value: 'draft', label: 'Draft' },
  { value: 'private', label: 'Private' },
  { value: 'pending', label: 'Pending' },
  { value: 'trash', label: 'Trash' },
]

function statusBadgeClass(status: string) {
  const map: Record<string, string> = {
    publish: 'badge-green',
    draft: 'badge-yellow',
    private: 'badge-gray',
    pending: 'badge-yellow',
    trash: 'badge-red',
  }
  return map[status] ?? 'badge-gray'
}

interface PostsListProps {
  isPages?: boolean
}

export default function PostsList({ isPages = false }: PostsListProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const prefix = isPages ? 'pages' : 'posts'
  const label = isPages ? 'Page' : 'Post'

  const { data, isLoading } = useQuery({
    queryKey: [prefix, { page, search, status: statusFilter }],
    queryFn: () =>
      isPages
        ? postsApi.listPages({ page, per_page: 20, search, status: statusFilter || undefined })
        : postsApi.list({ page, per_page: 20, search, status: statusFilter || undefined }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => (isPages ? postsApi.deletePage(id) : postsApi.delete(id)),
    onSuccess: () => {
      toast.success(`${label} deleted`)
      queryClient.invalidateQueries({ queryKey: [prefix] })
    },
    onError: () => toast.error('Failed to delete'),
  })

  const handleDelete = (post: Post) => {
    if (!window.confirm(`Delete "${post.post_title || '(no title)'}"?`)) return
    deleteMutation.mutate(post.ID)
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900 flex-1">{label}s</h1>
        <Link to={`/${prefix}/new`} className="btn-primary">
          <Plus size={16} />
          New {label}
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9"
            placeholder={`Search ${prefix}...`}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select
          className="input sm:w-48"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <Spinner className="w-7 h-7 text-blue-600" />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Title</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">Author</th>
                    {!isPages && (
                      <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">Categories</th>
                    )}
                    <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-600 hidden sm:table-cell">Date</th>
                    <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data?.items.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center py-12 text-gray-400">
                        No {prefix} found.
                      </td>
                    </tr>
                  )}
                  {data?.items.map((post) => (
                    <tr key={post.ID} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <button
                          onClick={() => navigate(`/${prefix}/${post.ID}/edit`)}
                          className="font-medium text-gray-800 hover:text-blue-600 text-left"
                        >
                          {post.post_title || <span className="italic text-gray-400">(no title)</span>}
                        </button>
                        {post.post_name && (
                          <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{post.post_name}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-600 hidden md:table-cell">
                        {post.author?.display_name ?? '—'}
                      </td>
                      {!isPages && (
                        <td className="px-4 py-3 hidden lg:table-cell">
                          <div className="flex flex-wrap gap-1">
                            {post.categories.slice(0, 2).map((c) => (
                              <span key={c.term_taxonomy_id} className="badge badge-gray">{c.name}</span>
                            ))}
                            {post.categories.length > 2 && (
                              <span className="badge badge-gray">+{post.categories.length - 2}</span>
                            )}
                          </div>
                        </td>
                      )}
                      <td className="px-4 py-3">
                        <span className={statusBadgeClass(post.post_status)}>{post.post_status}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 hidden sm:table-cell">
                        {format(new Date(post.post_date), 'MMM d, yyyy')}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            title="Edit"
                            onClick={() => navigate(`/${prefix}/${post.ID}/edit`)}
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          >
                            <Edit2 size={15} />
                          </button>
                          <button
                            title="Delete"
                            onClick={() => handleDelete(post)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data && data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <p className="text-sm text-gray-500">
                  {data.total} {prefix} total
                </p>
                <div className="flex gap-2">
                  <button
                    className="btn-secondary text-xs py-1.5 px-3"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    Previous
                  </button>
                  <span className="flex items-center text-sm text-gray-600 px-2">
                    {page} / {data.pages}
                  </span>
                  <button
                    className="btn-secondary text-xs py-1.5 px-3"
                    disabled={page >= data.pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
