import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Eye, ArrowLeft, Image as ImageIcon, X } from 'lucide-react'
import { postsApi } from '@/api/posts'
import { taxonomyApi } from '@/api/taxonomy'
import { mediaApi } from '@/api/media'
import RichEditor from '@/components/RichEditor'
import toast from 'react-hot-toast'
import Spinner from '@/components/Spinner'
import type { Term, Media } from '@/types'

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Draft' },
  { value: 'publish', label: 'Published' },
  { value: 'private', label: 'Private' },
  { value: 'pending', label: 'Pending Review' },
]

interface PostEditorProps {
  isPages?: boolean
}

export default function PostEditor({ isPages = false }: PostEditorProps) {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const prefix = isPages ? 'pages' : 'posts'
  const label = isPages ? 'Page' : 'Post'

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [excerpt, setExcerpt] = useState('')
  const [slug, setSlug] = useState('')
  const [status, setStatus] = useState('draft')
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([])
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [featuredImageId, setFeaturedImageId] = useState<number | null>(null)
  const [featuredImageUrl, setFeaturedImageUrl] = useState<string | null>(null)
  const [showMediaPicker, setShowMediaPicker] = useState(false)

  // Load existing post for editing
  const { isLoading: loadingPost, data: existingPost } = useQuery({
    queryKey: [prefix, id],
    queryFn: () => (isPages ? postsApi.getPage(Number(id)) : postsApi.get(Number(id))),
    enabled: isEdit,
    refetchOnWindowFocus: false,
  })

  // Populate form when existing post loads
  useEffect(() => {
    if (!existingPost) return
    setTitle(existingPost.post_title)
    setContent(existingPost.post_content)
    setExcerpt(existingPost.post_excerpt)
    setSlug(existingPost.post_name)
    setStatus(existingPost.post_status)
    setSelectedCategoryIds(existingPost.categories.map((c) => c.term_taxonomy_id))
    setSelectedTagIds(existingPost.tags.map((t) => t.term_taxonomy_id))
    setFeaturedImageId(existingPost.featured_image_id)
    setFeaturedImageUrl(existingPost.featured_image_url)
  }, [existingPost])

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => taxonomyApi.listCategories(),
    enabled: !isPages,
  })

  const { data: tags } = useQuery({
    queryKey: ['tags'],
    queryFn: () => taxonomyApi.listTags(),
    enabled: !isPages,
  })

  const { data: mediaList, isLoading: loadingMedia } = useQuery({
    queryKey: ['media-picker', showMediaPicker],
    queryFn: () => mediaApi.list(1, 24, 'image/'),
    enabled: showMediaPicker,
  })

  const saveMutation = useMutation({
    mutationFn: (draft: boolean) => {
      const payload = {
        post_title: title,
        post_content: content,
        post_excerpt: excerpt,
        post_name: slug,
        post_status: draft ? 'draft' : status,
        category_ids: selectedCategoryIds,
        tag_ids: selectedTagIds,
        featured_image_id: featuredImageId,
      }
      if (isEdit) {
        return isPages ? postsApi.updatePage(Number(id), payload) : postsApi.update(Number(id), payload)
      }
      return isPages ? postsApi.createPage(payload) : postsApi.create(payload)
    },
    onSuccess: (post) => {
      toast.success(`${label} saved!`)
      queryClient.invalidateQueries({ queryKey: [prefix] })
      if (!isEdit) navigate(`/${prefix}/${post.ID}/edit`, { replace: true })
    },
    onError: () => toast.error('Failed to save'),
  })

  if (isEdit && loadingPost) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-8 h-8 text-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-5 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/${prefix}`)} className="btn-secondary py-1.5">
          <ArrowLeft size={16} />
          Back
        </button>
        <h1 className="text-xl font-bold text-gray-900 flex-1">
          {isEdit ? `Edit ${label}` : `New ${label}`}
        </h1>
        <button
          onClick={() => saveMutation.mutate(true)}
          disabled={saveMutation.isPending}
          className="btn-secondary py-1.5"
        >
          {saveMutation.isPending ? <Spinner className="w-4 h-4" /> : <Save size={16} />}
          Save Draft
        </button>
        <button
          onClick={() => saveMutation.mutate(false)}
          disabled={saveMutation.isPending}
          className="btn-primary py-1.5"
        >
          {saveMutation.isPending ? <Spinner className="w-4 h-4" /> : <Eye size={16} />}
          {status === 'publish' ? 'Update' : 'Publish'}
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-5">
        {/* Main column */}
        <div className="flex-1 space-y-4">
          {/* Title */}
          <div className="card p-4">
            <input
              className="w-full text-2xl font-bold border-0 focus:outline-none focus:ring-0 placeholder-gray-300"
              placeholder="Add title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Content */}
          <div className="card overflow-hidden">
            <RichEditor content={content} onChange={setContent} placeholder="Write your content here..." />
          </div>

          {/* Excerpt */}
          <div className="card p-4">
            <label className="label">Excerpt</label>
            <textarea
              className="input resize-none h-24"
              placeholder="Short summary of this post..."
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
            />
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:w-72 space-y-4">
          {/* Publish settings */}
          <div className="card p-4 space-y-3">
            <h3 className="font-semibold text-gray-800">Publish</h3>
            <div>
              <label className="label">Status</label>
              <select
                className="input"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Slug (URL)</label>
              <input
                className="input text-sm"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="post-url-slug"
              />
            </div>
          </div>

          {/* Featured image */}
          <div className="card p-4 space-y-3">
            <h3 className="font-semibold text-gray-800">Featured Image</h3>
            {featuredImageUrl ? (
              <div className="relative">
                <img
                  src={featuredImageUrl}
                  alt="Featured"
                  className="w-full h-40 object-cover rounded-lg"
                />
                <button
                  onClick={() => { setFeaturedImageId(null); setFeaturedImageUrl(null) }}
                  className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                >
                  <X size={12} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowMediaPicker(true)}
                className="w-full h-32 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center gap-2 text-gray-400 hover:border-blue-400 hover:text-blue-400 transition-colors"
              >
                <ImageIcon size={24} />
                <span className="text-sm">Select image</span>
              </button>
            )}
          </div>

          {/* Categories */}
          {!isPages && categories && (
            <div className="card p-4 space-y-2">
              <h3 className="font-semibold text-gray-800">Categories</h3>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {categories.items.map((cat) => (
                  <label key={cat.term_taxonomy_id} className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={selectedCategoryIds.includes(cat.term_taxonomy_id)}
                      onChange={(e) => {
                        setSelectedCategoryIds(
                          e.target.checked
                            ? [...selectedCategoryIds, cat.term_taxonomy_id]
                            : selectedCategoryIds.filter((id) => id !== cat.term_taxonomy_id)
                        )
                      }}
                    />
                    {cat.name}
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {!isPages && tags && (
            <div className="card p-4 space-y-2">
              <h3 className="font-semibold text-gray-800">Tags</h3>
              <div className="flex flex-wrap gap-1.5">
                {tags.items.map((tag) => {
                  const active = selectedTagIds.includes(tag.term_taxonomy_id)
                  return (
                    <button
                      key={tag.term_taxonomy_id}
                      type="button"
                      onClick={() =>
                        setSelectedTagIds(
                          active
                            ? selectedTagIds.filter((id) => id !== tag.term_taxonomy_id)
                            : [...selectedTagIds, tag.term_taxonomy_id]
                        )
                      }
                      className={`badge cursor-pointer transition-colors ${
                        active ? 'bg-blue-100 text-blue-700' : 'badge-gray hover:bg-gray-200'
                      }`}
                    >
                      {tag.name}
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Media picker modal */}
      {showMediaPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="font-semibold text-gray-900">Select Featured Image</h2>
              <button onClick={() => setShowMediaPicker(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {loadingMedia ? (
                <div className="flex items-center justify-center h-40">
                  <Spinner className="w-6 h-6 text-blue-600" />
                </div>
              ) : (
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                  {mediaList?.items.map((media) => (
                    <button
                      key={media.ID}
                      onClick={() => {
                        setFeaturedImageId(media.ID)
                        setFeaturedImageUrl(media.file_url)
                        setShowMediaPicker(false)
                      }}
                      className="aspect-square rounded-lg overflow-hidden border-2 border-transparent hover:border-blue-400 transition-colors"
                    >
                      <img
                        src={media.thumbnail_url ?? media.file_url}
                        alt={media.alt_text || media.post_title}
                        className="w-full h-full object-cover"
                      />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
