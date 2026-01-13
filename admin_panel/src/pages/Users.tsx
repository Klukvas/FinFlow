import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { UserService } from '@/services/userService';
import { AdminUser, ApiError } from '@/types';
import { 
  FaSearch, 
  FaUserShield, 
  FaUser, 
  FaCheck, 
  FaBan,
  FaTimes,
  FaChevronLeft,
  FaChevronRight
} from 'react-icons/fa';

export const Users: React.FC = () => {
  const { token, logout } = useAuth();
  const queryClient = useQueryClient();
  
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const pageSize = 15;

  const userService = React.useMemo(
    () => new UserService(() => token, logout),
    [token, logout]
  );

  // Fetch users
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-users', search, page, pageSize],
    queryFn: async () => {
      const result = await userService.listUsers({ search, page, pageSize });
      if ('error' in result) throw new Error(result.error);
      return result;
    },
  });

  // Update role mutation
  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: number; role: string }) => {
      const result = await userService.updateUserRole(userId, role);
      if ('error' in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setSelectedUser(null);
    },
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ userId, status }: { userId: number; status: string }) => {
      const result = await userService.updateUserStatus(userId, status);
      if ('error' in result) throw new Error(result.error);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setSelectedUser(null);
    },
  });

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  }, [searchInput]);

  const handleToggleRole = (user: AdminUser) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin';
    updateRoleMutation.mutate({ userId: user.id, role: newRole });
  };

  const handleToggleStatus = (user: AdminUser) => {
    const newStatus = user.status === 'active' ? 'disabled' : 'active';
    updateStatusMutation.mutate({ userId: user.id, status: newStatus });
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">Users Management</h1>
        <p className="text-slate-400">Manage user accounts, roles, and access</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative max-w-md">
          <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by email or username..."
            className="w-full pl-11 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
        </div>
      </form>

      {/* Error state */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
          {error.message}
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500"></div>
        </div>
      ) : (
        <>
          {/* Users table */}
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden mb-6">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">User</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">Role</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">Status</th>
                  <th className="text-left px-6 py-4 text-sm font-semibold text-slate-300">Created</th>
                  <th className="text-right px-6 py-4 text-sm font-semibold text-slate-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((user) => (
                  <tr 
                    key={user.id} 
                    className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="text-white font-medium">{user.username}</p>
                          <p className="text-sm text-slate-400">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                        user.role === 'admin'
                          ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                          : 'bg-slate-600/30 text-slate-300 border border-slate-600/30'
                      }`}>
                        {user.role === 'admin' ? <FaUserShield className="w-3 h-3" /> : <FaUser className="w-3 h-3" />}
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                        user.status === 'active'
                          ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                          : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}>
                        {user.status === 'active' ? <FaCheck className="w-3 h-3" /> : <FaBan className="w-3 h-3" />}
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {user.created_at 
                        ? new Date(user.created_at).toLocaleDateString()
                        : '-'
                      }
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedUser(user)}
                          className="px-3 py-1.5 text-sm text-cyan-400 hover:bg-cyan-500/10 rounded-lg transition-colors"
                        >
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {data?.items.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                No users found
              </div>
            )}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, data.total)} of {data.total} users
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-4 py-2 text-sm text-slate-300">
                  Page {page} of {data.total_pages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                  disabled={page === data.total_pages}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FaChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Edit User Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl border border-slate-700 w-full max-w-md">
            {/* Modal header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <h2 className="text-lg font-semibold text-white">Edit User</h2>
              <button
                onClick={() => setSelectedUser(null)}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              >
                <FaTimes className="w-4 h-4" />
              </button>
            </div>

            {/* Modal content */}
            <div className="p-6 space-y-6">
              {/* User info */}
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-slate-700 rounded-full flex items-center justify-center">
                  <span className="text-xl text-white font-semibold">
                    {selectedUser.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-lg text-white font-medium">{selectedUser.username}</p>
                  <p className="text-sm text-slate-400">{selectedUser.email}</p>
                </div>
              </div>

              {/* Role toggle */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">Role</label>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleToggleRole(selectedUser)}
                    disabled={updateRoleMutation.isPending}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${
                      selectedUser.role === 'user'
                        ? 'bg-slate-700 border-slate-600 text-white'
                        : 'border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <FaUser className="w-4 h-4" />
                    User
                  </button>
                  <button
                    onClick={() => handleToggleRole(selectedUser)}
                    disabled={updateRoleMutation.isPending}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${
                      selectedUser.role === 'admin'
                        ? 'bg-purple-500/20 border-purple-500/30 text-purple-400'
                        : 'border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <FaUserShield className="w-4 h-4" />
                    Admin
                  </button>
                </div>
              </div>

              {/* Status toggle */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">Status</label>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleToggleStatus(selectedUser)}
                    disabled={updateStatusMutation.isPending}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${
                      selectedUser.status === 'active'
                        ? 'bg-green-500/20 border-green-500/30 text-green-400'
                        : 'border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <FaCheck className="w-4 h-4" />
                    Active
                  </button>
                  <button
                    onClick={() => handleToggleStatus(selectedUser)}
                    disabled={updateStatusMutation.isPending}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border transition-all ${
                      selectedUser.status === 'disabled'
                        ? 'bg-red-500/20 border-red-500/30 text-red-400'
                        : 'border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <FaBan className="w-4 h-4" />
                    Disabled
                  </button>
                </div>
              </div>

              {/* Error messages */}
              {(updateRoleMutation.error || updateStatusMutation.error) && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
                  {updateRoleMutation.error?.message || updateStatusMutation.error?.message}
                </div>
              )}
            </div>

            {/* Modal footer */}
            <div className="p-6 border-t border-slate-700">
              <button
                onClick={() => setSelectedUser(null)}
                className="w-full py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-xl transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
