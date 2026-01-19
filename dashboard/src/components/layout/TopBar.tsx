'use client'

import { useState, useEffect } from 'react'
import { User, Clock, ChevronDown, Wifi, WifiOff, Database, Cpu, Search, LogOut } from 'lucide-react'
import { clsx } from 'clsx'
import { NotificationPanel } from '@/components/notifications/NotificationPanel'
import { useNotifications } from '@/lib/notifications'

interface TopBarProps {
  utilityName?: string
  sidebarOpen?: boolean
}

interface UserInfo {
  username: string
  role: string
  email?: string
}

export function TopBar({ utilityName = 'LWSC', sidebarOpen = false }: TopBarProps) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [systemStatus, setSystemStatus] = useState<'green' | 'amber' | 'red'>('green')
  const [showUserMenu, setShowUserMenu] = useState(false)
  const { sensorStatus } = useNotifications()

  useEffect(() => {
    // Load user from localStorage (only on client)
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        setUser(JSON.parse(storedUser))
      }
    }
  }, [])
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  // Update system status based on sensor connection
  useEffect(() => {
    if (!sensorStatus.connected) {
      setSystemStatus('amber')
    } else {
      setSystemStatus('green')
    }
  }, [sensorStatus.connected])

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
  }
  
  const getStatusColor = () => {
    switch (systemStatus) {
      case 'green': return 'bg-emerald-500'
      case 'amber': return 'bg-amber-500'
      case 'red': return 'bg-red-500'
    }
  }
  
  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 z-10">
      <div className="h-full px-4 lg:px-6 flex items-center justify-between">
        {/* Left: Breadcrumb & Utility Name - with space for menu button */}
        <div className="flex items-center gap-4 ml-14">
          <div>
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider hidden sm:block">Control Room</p>
            <h2 className="text-sm font-semibold text-slate-900">
              {utilityName}
            </h2>
          </div>
        </div>
        
        {/* Center: Quick System Status - hidden on small screens */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 rounded-full border border-slate-200">
            <div className="flex items-center gap-1.5">
              {sensorStatus.connected ? (
                <>
                  <Wifi className="w-3 h-3 text-emerald-500" />
                  <span className="text-[10px] font-medium text-emerald-600">{sensorStatus.count}</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-amber-500" />
                  <span className="text-[10px] font-medium text-amber-600">0</span>
                </>
              )}
            </div>
            <div className="w-px h-3 bg-slate-200" />
            <div className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-emerald-500" />
              <span className="text-[10px] font-medium text-slate-600">OK</span>
            </div>
            <div className="w-px h-3 bg-slate-200" />
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3 text-emerald-500" />
              <span className="text-[10px] font-medium text-slate-600">AI</span>
            </div>
          </div>
        </div>
        
        {/* Right: Status and Controls */}
        <div className="flex items-center gap-2 sm:gap-4">
          {/* Search - hidden on mobile */}
          <div className="relative hidden xl:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search..." 
              className="w-48 pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
            />
          </div>
          
          {/* System Status */}
          <div className={clsx(
            "flex items-center gap-1.5 px-2 sm:px-2.5 py-1 border rounded-full",
            sensorStatus.connected 
              ? "bg-emerald-50 border-emerald-200" 
              : "bg-amber-50 border-amber-200"
          )}>
            <div className={clsx(
              'w-1.5 h-1.5 rounded-full',
              sensorStatus.connected ? 'bg-emerald-500 pulse-live' : 'bg-amber-500'
            )} />
            <span className={clsx(
              "text-[10px] font-semibold hidden sm:inline",
              sensorStatus.connected ? "text-emerald-700" : "text-amber-700"
            )}>
              {sensorStatus.connected ? 'Live' : 'Offline'}
            </span>
          </div>
          
          {/* Current Time - hidden on very small screens */}
          <div className="hidden sm:flex flex-col items-end">
            <span className="text-xs font-bold text-slate-900 font-mono">
              {currentTime.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          
          {/* Divider - hidden on mobile */}
          <div className="hidden sm:block w-px h-8 bg-slate-200" />
          
          {/* Notifications */}
          <NotificationPanel />
          
          {/* User */}
          <div className="relative">
            <button 
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 hover:bg-slate-100 rounded-xl transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-sm">
                <span className="text-xs font-bold text-white">
                  {user?.username?.substring(0, 2).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="text-left hidden lg:block">
                <p className="text-xs font-semibold text-slate-900">{user?.username || 'User'}</p>
                <p className="text-[10px] text-slate-400 capitalize">{user?.role || 'Operator'}</p>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
                <div className="px-4 py-2 border-b border-slate-100">
                  <p className="text-sm font-medium text-slate-900">{user?.username}</p>
                  <p className="text-xs text-slate-500">{user?.email || `${user?.username}@aquawatch.local`}</p>
                </div>
                <button
                  onClick={() => {
                    setShowUserMenu(false)
                    handleLogout()
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
