import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, File, Image, MessageSquare, Folder, Tag, Plus, TrendingUp } from 'lucide-react'
import { dashboardApi } from '@/api/dashboard'
import { format } from 'date-fns'
import Spinner from '@/components/Spinner'

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  color,
  link,
}: {
  label: string
  value: number
  sub?: string
  icon: React.ElementType
  color: string
  link: string
}) {
  return (
    <Link to={link} className="card p-5 flex items-center gap-4 hover:shadow-md transition-shadow">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </Link>
  )
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    publish: 'badge-green',
    draft: 'badge-yellow',
    private: 'badge-gray',
    trash: 'badge-red',
  }
  return map[status] ?? 'badge-gray'
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner className="w-8 h-8 text-blue-600" />
      </div>
    )
  }

  const stats = data!

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link to="/posts/new" className="btn-primary">
          <Plus size={16} />
          New Post
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <StatCard
          label="Published Posts"
          value={stats.posts.published}
          sub={`${stats.posts.draft} drafts`}
          icon={FileText}
          color="bg-blue-500"
          link="/posts"
        />
        <StatCard
          label="Published Pages"
          value={stats.pages.published}
          icon={File}
          color="bg-purple-500"
          link="/pages"
        />
        <StatCard
          label="Media Files"
          value={stats.media}
          icon={Image}
          color="bg-green-500"
          link="/media"
        />
        <StatCard
          label="Comments"
          value={stats.comments.approved}
          sub={`${stats.comments.pending} pending`}
          icon={MessageSquare}
          color="bg-orange-500"
          link="/comments"
        />
        <StatCard
          label="Categories"
          value={stats.categories}
          icon={Folder}
          color="bg-teal-500"
          link="/categories"
        />
        <StatCard
          label="Tags"
          value={stats.tags}
          icon={Tag}
          color="bg-pink-500"
          link="/tags"
        />
      </div>

      {/* Recent posts */}
      <div className="card">
        <div className="flex items-center justify-between p-5 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp size={18} className="text-blue-500" />
            Recent Posts
          </h2>
          <Link to="/posts" className="text-sm text-blue-600 hover:underline">View all</Link>
        </div>
        <div className="divide-y divide-gray-50">
          {stats.recent_posts.length === 0 && (
            <p className="p-5 text-sm text-gray-400">No posts yet.</p>
          )}
          {stats.recent_posts.map((post) => (
            <div key={post.ID} className="flex items-center justify-between px-5 py-3">
              <div className="min-w-0">
                <Link
                  to={`/posts/${post.ID}/edit`}
                  className="font-medium text-gray-800 hover:text-blue-600 truncate block"
                >
                  {post.post_title || '(no title)'}
                </Link>
                <p className="text-xs text-gray-400 mt-0.5">
                  {format(new Date(post.post_date), 'MMM d, yyyy')}
                </p>
              </div>
              <span className={statusBadge(post.post_status)}>{post.post_status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
