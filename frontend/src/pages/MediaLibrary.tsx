import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, Trash2, X, Image as ImageIcon, Film, Music, File } from 'lucide-react'
import { useDropzone } from 'react-dropzone'
import { mediaApi } from '@/api/media'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Spinner from '@/components/Spinner'
import type { Media } from '@/types'

function MediaIcon({ mimeType }: { mimeType: string }) {
  if (mimeType.startsWith('image/')) return <ImageIcon size={32} className="text-blue-400" />
  if (mimeType.startsWith('video/')) return <Film size={32} className="text-purple-400" />
  if (mimeType.startsWith('audio/')) return <Music size={32} className="text-green-400" />
  return <File size={32} className="text-gray-400" />
}

function formatBytes(bytes: number | null): string {
  if (!bytes) return '–'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function MediaLibrary() {
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Media | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['media', page],
    queryFn: () => mediaApi.list(page, 24),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => mediaApi.delete(id),
    onSuccess: () => {
      toast.success('Media deleted')
      setSelected(null)
      queryClient.invalidateQueries({ queryKey: ['media'] })
    },
    onError: () => toast.error('Failed to delete'),
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      setUploading(true)
      setUploadProgress(0)
      try {
        await mediaApi.upload(file, setUploadProgress)
        toast.success(`"${file.name}" uploaded`)
        queryClient.invalidateQueries({ queryKey: ['media'] })
      } catch {
        toast.error(`Failed to upload "${file.name}"`)
      } finally {
        setUploading(false)
        setUploadProgress(0)
      }
    }
  }, [queryClient])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': [],
      'video/*': [],
      'audio/*': [],
      'application/pdf': ['.pdf'],
    },
  })

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Media Library</h1>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`card p-8 border-2 border-dashed text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="space-y-2">
            <Spinner className="w-8 h-8 text-blue-600 mx-auto" />
            <p className="text-sm text-gray-600">Uploading... {uploadProgress}%</p>
            <div className="w-48 mx-auto h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Upload size={32} className="mx-auto text-gray-400" />
            <p className="font-medium text-gray-700">
              {isDragActive ? 'Drop files here' : 'Drag & drop files or click to browse'}
            </p>
            <p className="text-sm text-gray-400">Images, videos, audio, PDF — max 50 MB</p>
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="flex gap-5">
        <div className="flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Spinner className="w-8 h-8 text-blue-600" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
                {data?.items.map((item) => (
                  <button
                    key={item.ID}
                    onClick={() => setSelected(item)}
                    className={`aspect-square card overflow-hidden hover:ring-2 hover:ring-blue-400 transition-all ${
                      selected?.ID === item.ID ? 'ring-2 ring-blue-600' : ''
                    }`}
                  >
                    {item.post_mime_type.startsWith('image/') ? (
                      <img
                        src={item.thumbnail_url ?? item.file_url}
                        alt={item.alt_text || item.post_title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-1 bg-gray-50">
                        <MediaIcon mimeType={item.post_mime_type} />
                        <p className="text-xs text-gray-500 truncate w-full px-2 text-center">
                          {item.post_title}
                        </p>
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Pagination */}
              {data && Math.ceil(data.total / 24) > 1 && (
                <div className="flex items-center justify-center gap-3 mt-5">
                  <button
                    className="btn-secondary text-xs py-1.5 px-3"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >Previous</button>
                  <span className="text-sm text-gray-600">{page} / {Math.ceil(data.total / 24)}</span>
                  <button
                    className="btn-secondary text-xs py-1.5 px-3"
                    disabled={page >= Math.ceil(data.total / 24)}
                    onClick={() => setPage(page + 1)}
                  >Next</button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-64 flex-shrink-0 card p-4 space-y-3 self-start">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-800 text-sm">Details</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">
                <X size={16} />
              </button>
            </div>

            {selected.post_mime_type.startsWith('image/') ? (
              <img
                src={selected.thumbnail_url ?? selected.file_url}
                alt={selected.alt_text}
                className="w-full rounded-lg"
              />
            ) : (
              <div className="flex items-center justify-center h-24 bg-gray-50 rounded-lg">
                <MediaIcon mimeType={selected.post_mime_type} />
              </div>
            )}

            <div className="space-y-1.5 text-xs text-gray-600">
              <div>
                <span className="font-medium">File name:</span>{' '}
                <span className="text-gray-500 break-all">{selected.post_title}</span>
              </div>
              <div>
                <span className="font-medium">Type:</span>{' '}
                <span className="text-gray-500">{selected.post_mime_type}</span>
              </div>
              <div>
                <span className="font-medium">Size:</span>{' '}
                <span className="text-gray-500">{formatBytes(selected.file_size)}</span>
              </div>
              <div>
                <span className="font-medium">Uploaded:</span>{' '}
                <span className="text-gray-500">
                  {format(new Date(selected.post_date), 'MMM d, yyyy')}
                </span>
              </div>
            </div>

            <a
              href={selected.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary w-full justify-center text-xs py-1.5"
            >
              View file
            </a>

            <button
              onClick={() => {
                if (!window.confirm('Delete this file permanently?')) return
                deleteMutation.mutate(selected.ID)
              }}
              disabled={deleteMutation.isPending}
              className="btn-danger w-full justify-center text-xs py-1.5"
            >
              {deleteMutation.isPending ? <Spinner className="w-3 h-3" /> : <Trash2 size={13} />}
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
