import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Edit2, Trash2, Check, X } from 'lucide-react'
import { taxonomyApi } from '@/api/taxonomy'
import toast from 'react-hot-toast'
import Spinner from '@/components/Spinner'
import type { Term } from '@/types'

interface TermManagerProps {
  taxonomy: 'categories' | 'tags'
}

export default function TermManager({ taxonomy }: TermManagerProps) {
  const isCategory = taxonomy === 'categories'
  const label = isCategory ? 'Category' : 'Tag'
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: [taxonomy, search],
    queryFn: () =>
      isCategory ? taxonomyApi.listCategories(search) : taxonomyApi.listTags(search),
  })

  const createMutation = useMutation({
    mutationFn: () =>
      isCategory
        ? taxonomyApi.createCategory({ name: newName, description: newDesc })
        : taxonomyApi.createTag({ name: newName, description: newDesc }),
    onSuccess: () => {
      toast.success(`${label} created`)
      setNewName('')
      setNewDesc('')
      queryClient.invalidateQueries({ queryKey: [taxonomy] })
    },
    onError: () => toast.error('Failed to create'),
  })

  const updateMutation = useMutation({
    mutationFn: (id: number) =>
      isCategory
        ? taxonomyApi.updateCategory(id, { name: editName, description: editDesc })
        : taxonomyApi.updateTag(id, { name: editName, description: editDesc }),
    onSuccess: () => {
      toast.success(`${label} updated`)
      setEditingId(null)
      queryClient.invalidateQueries({ queryKey: [taxonomy] })
    },
    onError: () => toast.error('Failed to update'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      isCategory ? taxonomyApi.deleteCategory(id) : taxonomyApi.deleteTag(id),
    onSuccess: () => {
      toast.success(`${label} deleted`)
      queryClient.invalidateQueries({ queryKey: [taxonomy] })
    },
    onError: () => toast.error('Failed to delete'),
  })

  const startEdit = (term: Term) => {
    setEditingId(term.term_taxonomy_id)
    setEditName(term.name)
    setEditDesc(term.description)
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">{label}s</h1>

      <div className="flex flex-col lg:flex-row gap-5">
        {/* Create form */}
        <div className="lg:w-80 card p-5 space-y-3 self-start">
          <h2 className="font-semibold text-gray-800">Add New {label}</h2>
          <div>
            <label className="label">Name</label>
            <input
              className="input"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={`${label} name`}
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              className="input resize-none h-20"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Optional description"
            />
          </div>
          <button
            disabled={!newName.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate()}
            className="btn-primary w-full justify-center"
          >
            {createMutation.isPending ? <Spinner className="w-4 h-4" /> : <Plus size={16} />}
            Add {label}
          </button>
        </div>

        {/* List */}
        <div className="flex-1 card overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <input
              className="input"
              placeholder={`Search ${taxonomy}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-40">
              <Spinner className="w-7 h-7 text-blue-600" />
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">Slug</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">Description</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">Count</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data?.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-center py-10 text-gray-400">No {taxonomy} found.</td>
                  </tr>
                )}
                {data?.items.map((term) => (
                  <tr key={term.term_taxonomy_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      {editingId === term.term_taxonomy_id ? (
                        <input
                          className="input text-sm py-1"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          autoFocus
                        />
                      ) : (
                        <span className="font-medium text-gray-800">{term.name}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 hidden md:table-cell">{term.slug}</td>
                    <td className="px-4 py-3 text-gray-500 hidden lg:table-cell">
                      {editingId === term.term_taxonomy_id ? (
                        <input
                          className="input text-sm py-1"
                          value={editDesc}
                          onChange={(e) => setEditDesc(e.target.value)}
                        />
                      ) : (
                        <span className="truncate block max-w-xs">{term.description || '—'}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">{term.count}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {editingId === term.term_taxonomy_id ? (
                          <>
                            <button
                              onClick={() => updateMutation.mutate(term.term_taxonomy_id)}
                              className="p-1.5 text-green-600 hover:bg-green-50 rounded-lg"
                              disabled={updateMutation.isPending}
                            >
                              <Check size={15} />
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-lg"
                            >
                              <X size={15} />
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => startEdit(term)}
                              className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                            >
                              <Edit2 size={15} />
                            </button>
                            <button
                              onClick={() => {
                                if (!window.confirm(`Delete "${term.name}"?`)) return
                                deleteMutation.mutate(term.term_taxonomy_id)
                              }}
                              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                            >
                              <Trash2 size={15} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
