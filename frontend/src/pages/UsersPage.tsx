import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/api/auth'
import Spinner from '@/components/Spinner'
import apiClient from '@/api/client'
import type { User } from '@/types'
import { format } from 'date-fns'
import { Users } from 'lucide-react'

export default function UsersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await apiClient.get<User[]>('/users')
      return data
    },
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <span className="badge badge-gray">{data?.length ?? 0}</span>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <Spinner className="w-7 h-7 text-blue-600" />
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-100">
                <th className="text-left px-4 py-3 font-medium text-gray-600">User</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden md:table-cell">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden lg:table-cell">Username</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 hidden sm:table-cell">Registered</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data?.map((user) => (
                <tr key={user.ID} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                        {user.display_name?.[0]?.toUpperCase() ?? 'U'}
                      </div>
                      <span className="font-medium text-gray-800">{user.display_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{user.user_email}</td>
                  <td className="px-4 py-3 text-gray-500 hidden lg:table-cell">{user.user_login}</td>
                  <td className="px-4 py-3 text-gray-500 hidden sm:table-cell">
                    {format(new Date(user.user_registered), 'MMM d, yyyy')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
