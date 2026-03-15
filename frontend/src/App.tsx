import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/Login'
import DashboardPage from '@/pages/Dashboard'
import PostsList from '@/pages/PostsList'
import PostEditor from '@/pages/PostEditor'
import MediaLibrary from '@/pages/MediaLibrary'
import TermManager from '@/pages/TermManager'
import CommentsPage from '@/pages/CommentsPage'
import UsersPage from '@/pages/UsersPage'

function AppLayout() {
  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* All protected routes are wrapped in the sidebar layout */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />

            {/* Posts */}
            <Route path="posts" element={<PostsList />} />
            <Route path="posts/new" element={<PostEditor />} />
            <Route path="posts/:id/edit" element={<PostEditor />} />

            {/* Pages */}
            <Route path="pages" element={<PostsList isPages />} />
            <Route path="pages/new" element={<PostEditor isPages />} />
            <Route path="pages/:id/edit" element={<PostEditor isPages />} />

            {/* Media */}
            <Route path="media" element={<MediaLibrary />} />

            {/* Taxonomy */}
            <Route path="categories" element={<TermManager taxonomy="categories" />} />
            <Route path="tags" element={<TermManager taxonomy="tags" />} />

            {/* Comments */}
            <Route path="comments" element={<CommentsPage />} />

            {/* Users */}
            <Route path="users" element={<UsersPage />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
