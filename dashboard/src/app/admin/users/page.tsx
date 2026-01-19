'use client'

import { useState, useEffect } from 'react'
import { Users, UserPlus, Shield, Trash2, Edit, Search, Filter, AlertTriangle, X, Check, Eye, EyeOff, RefreshCw } from 'lucide-react'

interface User {
  user_id: string
  username: string
  email: string
  role: string
  is_active: boolean
  last_login?: string
  isSystem?: boolean
}

interface NewUserForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  role: string
  fullName: string
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [userToDelete, setUserToDelete] = useState<User | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [createSuccess, setCreateSuccess] = useState(false)
  const [createError, setCreateError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  
  const [newUserForm, setNewUserForm] = useState<NewUserForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'operator',
    fullName: ''
  })

  // Load users from MongoDB on mount
  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/auth/login')
      if (response.ok) {
        const data = await response.json()
        setUsers(data.users || [])
      } else {
        // Fallback to default users if API fails
        setUsers([
          { user_id: '1', username: 'admin', email: 'admin@lwsc.local', role: 'admin', is_active: true, last_login: '2026-01-18 08:30', isSystem: true },
          { user_id: '2', username: 'operator', email: 'operator@lwsc.local', role: 'operator', is_active: true, last_login: '2026-01-18 07:45', isSystem: true },
          { user_id: '3', username: 'technician', email: 'tech@lwsc.local', role: 'technician', is_active: true, last_login: '2026-01-17 14:20', isSystem: true },
        ])
      }
    } catch (error) {
      console.error('Failed to load users:', error)
      // Fallback users
      setUsers([
        { user_id: '1', username: 'admin', email: 'admin@lwsc.local', role: 'admin', is_active: true, isSystem: true },
        { user_id: '2', username: 'operator', email: 'operator@lwsc.local', role: 'operator', is_active: true, isSystem: true },
        { user_id: '3', username: 'technician', email: 'tech@lwsc.local', role: 'technician', is_active: true, isSystem: true },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user)
    setShowDeleteModal(true)
    setDeleteConfirmText('')
  }

  const handleConfirmDelete = async () => {
    if (userToDelete && deleteConfirmText === userToDelete.username) {
      try {
        const response = await fetch(`/api/auth/login?username=${userToDelete.username}`, {
          method: 'DELETE'
        })
        
        if (response.ok) {
          // Reload users from server
          await loadUsers()
        } else {
          // Remove locally if API fails
          setUsers(users.filter(u => u.user_id !== userToDelete.user_id))
        }
      } catch (e) {
        // Remove locally if request fails
        setUsers(users.filter(u => u.user_id !== userToDelete.user_id))
      }
      
      setShowDeleteModal(false)
      setUserToDelete(null)
      setDeleteConfirmText('')
    }
  }

  const handleCancelDelete = () => {
    setShowDeleteModal(false)
    setUserToDelete(null)
    setDeleteConfirmText('')
  }

  const handleCreateUser = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setCreateError('')
    setIsCreating(true)

    // Validation
    if (!newUserForm.username || !newUserForm.password) {
      setCreateError('Username and password are required')
      setIsCreating(false)
      return
    }

    if (newUserForm.password !== newUserForm.confirmPassword) {
      setCreateError('Passwords do not match')
      setIsCreating(false)
      return
    }

    if (newUserForm.password.length < 6) {
      setCreateError('Password must be at least 6 characters')
      setIsCreating(false)
      return
    }

    // Check if username exists
    if (users.some(u => u.username.toLowerCase() === newUserForm.username.toLowerCase())) {
      setCreateError('Username already exists')
      setIsCreating(false)
      return
    }

    try {
      // Register user with MongoDB API
      const response = await fetch('/api/auth/login', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: newUserForm.username,
          password: newUserForm.password,
          role: newUserForm.role,
          name: newUserForm.fullName || newUserForm.username,
          email: newUserForm.email || `${newUserForm.username}@lwsc.local`
        })
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to create user')
      }

      // Show success and reload users from server
      setCreateSuccess(true)
      await loadUsers()
      
      setTimeout(() => {
        setCreateSuccess(false)
        setShowAddModal(false)
        setNewUserForm({
          username: '',
          email: '',
          password: '',
          confirmPassword: '',
          role: 'operator',
          fullName: ''
        })
      }, 2000)

    } catch (error) {
      setCreateError(error instanceof Error ? error.message : 'Failed to create user')
    } finally {
      setIsCreating(false)
    }
  }

  const handleCloseAddModal = () => {
    setShowAddModal(false)
    setNewUserForm({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      role: 'operator',
      fullName: ''
    })
    setCreateError('')
    setCreateSuccess(false)
  }

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'operator': return 'bg-cyan-100 text-cyan-700 border-cyan-200'
      case 'technician': return 'bg-orange-100 text-orange-700 border-orange-200'
      default: return 'bg-slate-100 text-slate-700 border-slate-200'
    }
  }

  const filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900">User Management</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 sm:mt-1">Manage system users and permissions</p>
        </div>
        <button 
          onClick={() => setShowAddModal(true)}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/25"
        >
          <UserPlus className="w-4 h-4" />
          <span className="hidden sm:inline">Add User</span>
          <span className="sm:hidden">Add</span>
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{users.length}</p>
              <p className="text-xs text-slate-500">Total Users</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{users.filter(u => u.is_active).length}</p>
              <p className="text-xs text-slate-500">Active</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{users.filter(u => u.role === 'admin').length}</p>
              <p className="text-xs text-slate-500">Admins</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Users className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{users.filter(u => u.role === 'operator').length}</p>
              <p className="text-xs text-slate-500">Operators</p>
            </div>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {/* Search Bar */}
        <div className="p-4 border-b border-slate-200 flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <Filter className="w-4 h-4 text-slate-500" />
            <span className="text-sm text-slate-600">Filter</span>
          </button>
        </div>

        {/* Table */}
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">User</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Role</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Last Login</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredUsers.map((user) => (
              <tr key={user.user_id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                      <span className="text-sm font-bold text-white">{user.username.substring(0, 2).toUpperCase()}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{user.username}</p>
                      <p className="text-xs text-slate-500">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getRoleBadgeColor(user.role)}`}>
                    {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`flex items-center gap-1.5 text-xs font-medium ${user.is_active ? 'text-emerald-600' : 'text-slate-400'}`}>
                    <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-slate-500">{user.last_login || 'Never'}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors" title="Edit">
                      <Edit className="w-4 h-4 text-slate-500" />
                    </button>
                    <button 
                      onClick={() => handleDeleteClick(user)}
                      disabled={user.username === 'admin'}
                      className={`p-1.5 rounded-lg transition-colors ${
                        user.username === 'admin' 
                          ? 'opacity-30 cursor-not-allowed' 
                          : 'hover:bg-red-50'
                      }`} 
                      title={user.username === 'admin' ? 'Cannot delete main admin' : 'Delete user'}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg shadow-xl max-h-[90vh] flex flex-col">
            {/* Sticky Header with Add Button */}
            <div className="flex items-center justify-between p-5 border-b border-slate-200 bg-white rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                  <UserPlus className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Add New Team Member</h2>
                  <p className="text-xs text-slate-500">Fill in the details below</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={handleCloseAddModal}
                  className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleCreateUser}
                  disabled={isCreating || !newUserForm.username || !newUserForm.password || newUserForm.password.length < 6 || newUserForm.password !== newUserForm.confirmPassword}
                  className="px-4 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isCreating ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                      </svg>
                      Adding...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4" />
                      Add User
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* Scrollable Content */}
            <div className="overflow-y-auto flex-1 p-5">
              {createSuccess ? (
                <div className="py-8 text-center">
                  <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                    <Check className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">User Created Successfully!</h3>
                  <p className="text-sm text-slate-500 mb-4">
                    <strong>{newUserForm.username}</strong> can now log in with their credentials.
                  </p>
                  <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200 text-left max-w-xs mx-auto">
                    <p className="text-xs text-emerald-800 font-medium mb-2">Login Details:</p>
                    <p className="text-sm text-emerald-700">Username: <strong>{newUserForm.username}</strong></p>
                    <p className="text-sm text-emerald-700">Password: <strong>••••••••</strong></p>
                    <p className="text-sm text-emerald-700">Role: <strong>{newUserForm.role}</strong></p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {createError && (
                    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      {createError}
                    </div>
                  )}

                  {/* Form Progress Indicator */}
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`h-1 flex-1 rounded-full ${newUserForm.username ? 'bg-blue-500' : 'bg-slate-200'}`} />
                    <div className={`h-1 flex-1 rounded-full ${newUserForm.password ? 'bg-blue-500' : 'bg-slate-200'}`} />
                    <div className={`h-1 flex-1 rounded-full ${newUserForm.confirmPassword && newUserForm.password === newUserForm.confirmPassword ? 'bg-blue-500' : 'bg-slate-200'}`} />
                    <div className={`h-1 flex-1 rounded-full ${newUserForm.role ? 'bg-blue-500' : 'bg-slate-200'}`} />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Username <span className="text-red-500">*</span>
                      </label>
                      <input 
                        type="text" 
                        value={newUserForm.username}
                        onChange={(e) => setNewUserForm({...newUserForm, username: e.target.value.toLowerCase().replace(/\s/g, '')})}
                        placeholder="e.g., john.smith"
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                        autoFocus
                      />
                      <p className="text-xs text-slate-400 mt-1">This will be used to log in (no spaces)</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                      <input 
                        type="text" 
                        value={newUserForm.fullName}
                        onChange={(e) => setNewUserForm({...newUserForm, fullName: e.target.value})}
                        placeholder="e.g., John Smith"
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                      <input 
                        type="email" 
                        value={newUserForm.email}
                        onChange={(e) => setNewUserForm({...newUserForm, email: e.target.value})}
                        placeholder="e.g., john@lwsc.local"
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                      />
                    </div>
                    
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Role <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          type="button"
                          onClick={() => setNewUserForm({...newUserForm, role: 'operator'})}
                          className={`p-3 rounded-lg border-2 text-left transition-all ${
                            newUserForm.role === 'operator' 
                              ? 'border-cyan-500 bg-cyan-50' 
                              : 'border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <p className={`text-sm font-medium ${newUserForm.role === 'operator' ? 'text-cyan-700' : 'text-slate-700'}`}>Operator</p>
                          <p className="text-[10px] text-slate-500">Monitor & alerts</p>
                        </button>
                        <button
                          type="button"
                          onClick={() => setNewUserForm({...newUserForm, role: 'technician'})}
                          className={`p-3 rounded-lg border-2 text-left transition-all ${
                            newUserForm.role === 'technician' 
                              ? 'border-orange-500 bg-orange-50' 
                              : 'border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <p className={`text-sm font-medium ${newUserForm.role === 'technician' ? 'text-orange-700' : 'text-slate-700'}`}>Technician</p>
                          <p className="text-[10px] text-slate-500">Field tasks</p>
                        </button>
                        <button
                          type="button"
                          onClick={() => setNewUserForm({...newUserForm, role: 'admin'})}
                          className={`p-3 rounded-lg border-2 text-left transition-all ${
                            newUserForm.role === 'admin' 
                              ? 'border-purple-500 bg-purple-50' 
                              : 'border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <p className={`text-sm font-medium ${newUserForm.role === 'admin' ? 'text-purple-700' : 'text-slate-700'}`}>Admin</p>
                          <p className="text-[10px] text-slate-500">Full access</p>
                        </button>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Password <span className="text-red-500">*</span>
                      </label>
                      <div className="relative">
                        <input 
                          type={showPassword ? 'text' : 'password'}
                          value={newUserForm.password}
                          onChange={(e) => setNewUserForm({...newUserForm, password: e.target.value})}
                          placeholder="Min 6 characters"
                          className="w-full px-3 py-2.5 pr-10 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm" 
                        />
                        <button 
                          type="button" 
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                        >
                          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>
                      {newUserForm.password && newUserForm.password.length < 6 && (
                        <p className="text-xs text-amber-600 mt-1">At least 6 characters needed</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        Confirm Password <span className="text-red-500">*</span>
                      </label>
                      <input 
                        type={showPassword ? 'text' : 'password'}
                        value={newUserForm.confirmPassword}
                        onChange={(e) => setNewUserForm({...newUserForm, confirmPassword: e.target.value})}
                        placeholder="Re-enter password"
                        className={`w-full px-3 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-sm ${
                          newUserForm.confirmPassword && newUserForm.password !== newUserForm.confirmPassword 
                            ? 'border-red-300 focus:border-red-500' 
                            : newUserForm.confirmPassword && newUserForm.password === newUserForm.confirmPassword
                            ? 'border-emerald-300 focus:border-emerald-500'
                            : 'border-slate-200 focus:border-blue-500'
                        }`}
                      />
                      {newUserForm.confirmPassword && newUserForm.password !== newUserForm.confirmPassword && (
                        <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                      )}
                      {newUserForm.confirmPassword && newUserForm.password === newUserForm.confirmPassword && (
                        <p className="text-xs text-emerald-600 mt-1 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Passwords match
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-200 mt-4">
                    <p className="text-xs text-slate-600">
                      <strong>Note:</strong> Share the login credentials securely with the new team member. They can change their password after first login.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && userToDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Delete User</h2>
              </div>
              <button onClick={handleCancelDelete} className="p-1 hover:bg-slate-100 rounded-lg">
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            
            <div className="mb-4">
              <p className="text-slate-600 mb-3">
                You are about to permanently delete the user account:
              </p>
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                    <span className="text-sm font-bold text-white">{userToDelete.username.substring(0, 2).toUpperCase()}</span>
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900">{userToDelete.username}</p>
                    <p className="text-sm text-slate-500">{userToDelete.email}</p>
                  </div>
                  <span className={`ml-auto px-2.5 py-1 rounded-full text-xs font-medium border ${
                    userToDelete.role === 'admin' ? 'bg-purple-100 text-purple-700 border-purple-200' :
                    userToDelete.role === 'operator' ? 'bg-cyan-100 text-cyan-700 border-cyan-200' :
                    'bg-orange-100 text-orange-700 border-orange-200'
                  }`}>
                    {userToDelete.role.charAt(0).toUpperCase() + userToDelete.role.slice(1)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-red-700">
                <strong>Warning:</strong> This action cannot be undone. All data associated with this user will be permanently removed.
              </p>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Type <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-red-600">{userToDelete.username}</span> to confirm:
              </label>
              <input 
                type="text" 
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="Enter username to confirm"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500" 
              />
            </div>
            
            <div className="flex gap-3">
              <button 
                type="button" 
                onClick={handleCancelDelete} 
                className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button 
                type="button"
                onClick={handleConfirmDelete}
                disabled={deleteConfirmText !== userToDelete.username}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors font-medium flex items-center justify-center gap-2 ${
                  deleteConfirmText === userToDelete.username
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                }`}
              >
                <Trash2 className="w-4 h-4" />
                Delete User
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
