'use client'

import { ReactNode, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { useSync } from '@/lib/sync-service'
import { 
  Wrench, 
  Home, 
  User, 
  RefreshCw, 
  Wifi, 
  WifiOff,
  Cloud,
  CloudOff,
  Menu,
  X,
  LogOut,
  Settings,
  Bell
} from 'lucide-react'
import Link from 'next/link'
import { clsx } from 'clsx'

// =============================================================================
// TECHNICIAN LAYOUT
// =============================================================================
// Mobile-first layout for technician mobile experience
// - Bottom navigation
// - Sync status indicator
// - Role protection
// =============================================================================

interface TechLayoutProps {
  children: ReactNode
}

// Allowed roles for technician portal
const ALLOWED_ROLES = ['technician', 'engineer', 'admin', 'operator', 'field_technician']

export default function TechLayout({ children }: TechLayoutProps) {
  const { user, isLoading, isAuthenticated, logout } = useAuth()
  const { isOnline, isSyncing, pendingCount, sync } = useSync()
  const router = useRouter()
  const [showMenu, setShowMenu] = useState(false)
  
  // Role protection
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login')
      return
    }
    
    if (!isLoading && user) {
      const userRole = user.role?.toLowerCase() || ''
      if (!ALLOWED_ROLES.includes(userRole)) {
        // Redirect non-technicians to main dashboard
        router.push('/app')
      }
    }
  }, [isLoading, isAuthenticated, user, router])
  
  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    )
  }
  
  // Not authenticated
  if (!isAuthenticated) {
    return null
  }
  
  // Check role
  const userRole = user?.role?.toLowerCase() || ''
  if (!ALLOWED_ROLES.includes(userRole)) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center max-w-sm">
          <p className="text-red-400 font-medium">Access Denied</p>
          <p className="text-slate-400 text-sm mt-2">
            This portal is for field technicians only.
          </p>
          <Link
            href="/"
            className="mt-4 inline-block px-4 py-2 bg-slate-700 text-white rounded-lg text-sm"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="bg-blue-600 text-white sticky top-0 z-50 safe-area-inset-top">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Wrench className="w-6 h-6" />
            <span className="font-semibold text-lg">AquaWatch Tech</span>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Sync Status */}
            <button
              onClick={() => sync()}
              disabled={isSyncing || !isOnline}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                isSyncing ? 'animate-pulse bg-blue-500' : 'hover:bg-blue-500'
              )}
            >
              {isSyncing ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : isOnline ? (
                <Cloud className="w-5 h-5" />
              ) : (
                <CloudOff className="w-5 h-5" />
              )}
            </button>
            
            {/* Pending badge */}
            {pendingCount > 0 && (
              <span className="bg-amber-500 text-xs font-bold px-2 py-0.5 rounded-full">
                {pendingCount}
              </span>
            )}
            
            {/* Menu button */}
            <button
              onClick={() => setShowMenu(true)}
              className="p-2 hover:bg-blue-500 rounded-lg"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Connection status bar */}
        {!isOnline && (
          <div className="bg-amber-500 px-4 py-1.5 flex items-center justify-center gap-2 text-sm font-medium">
            <WifiOff className="w-4 h-4" />
            Offline Mode - Changes will sync when online
          </div>
        )}
      </header>
      
      {/* Main Content */}
      <main className="flex-1 pb-20">
        {children}
      </main>
      
      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 safe-area-inset-bottom">
        <div className="flex items-center justify-around py-2">
          <NavItem href="/tech" icon={<Home />} label="Home" />
          <NavItem href="/tech/orders" icon={<Wrench />} label="Orders" />
          <NavItem href="/tech/notifications" icon={<Bell />} label="Alerts" badge={pendingCount > 0 ? pendingCount : undefined} />
          <NavItem href="/tech/profile" icon={<User />} label="Profile" />
        </div>
      </nav>
      
      {/* Side Menu */}
      {showMenu && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/50 z-50"
            onClick={() => setShowMenu(false)}
          />
          
          {/* Menu Panel */}
          <div className="fixed top-0 right-0 bottom-0 w-72 bg-white z-50 shadow-xl animate-in slide-in-from-right">
            <div className="p-4 bg-blue-600 text-white">
              <div className="flex items-center justify-between mb-4">
                <span className="font-semibold">Menu</span>
                <button onClick={() => setShowMenu(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-medium">{user?.username}</p>
                  <p className="text-sm text-blue-200 capitalize">{user?.role}</p>
                </div>
              </div>
            </div>
            
            <div className="p-4 space-y-1">
              <MenuItem 
                href="/tech/settings" 
                icon={<Settings />} 
                label="Settings"
                onClick={() => setShowMenu(false)}
              />
              <MenuItem 
                href="/tech/sync" 
                icon={<RefreshCw />} 
                label="Sync Status"
                onClick={() => setShowMenu(false)}
              />
              
              <div className="border-t border-slate-200 my-4" />
              
              {/* Connection Status */}
              <div className="px-4 py-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-2 text-sm">
                  {isOnline ? (
                    <>
                      <Wifi className="w-4 h-4 text-emerald-500" />
                      <span className="text-emerald-700">Online</span>
                    </>
                  ) : (
                    <>
                      <WifiOff className="w-4 h-4 text-amber-500" />
                      <span className="text-amber-700">Offline</span>
                    </>
                  )}
                </div>
                {pendingCount > 0 && (
                  <p className="text-xs text-slate-500 mt-1">
                    {pendingCount} pending change{pendingCount !== 1 ? 's' : ''}
                  </p>
                )}
              </div>
              
              <div className="border-t border-slate-200 my-4" />
              
              <button
                onClick={() => {
                  logout()
                  setShowMenu(false)
                }}
                className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

interface NavItemProps {
  href: string
  icon: ReactNode
  label: string
  badge?: number
}

function NavItem({ href, icon, label, badge }: NavItemProps) {
  // Simple active check based on pathname
  const isActive = typeof window !== 'undefined' && window.location.pathname === href
  
  return (
    <Link
      href={href}
      className={clsx(
        'flex flex-col items-center gap-1 px-4 py-1 rounded-lg transition-colors relative',
        isActive ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'
      )}
    >
      <div className="relative">
        <span className="w-6 h-6">{icon}</span>
        {badge !== undefined && (
          <span className="absolute -top-1 -right-1 min-w-[16px] h-4 flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-1">
            {badge > 9 ? '9+' : badge}
          </span>
        )}
      </div>
      <span className="text-xs font-medium">{label}</span>
    </Link>
  )
}

interface MenuItemProps {
  href: string
  icon: ReactNode
  label: string
  onClick?: () => void
}

function MenuItem({ href, icon, label, onClick }: MenuItemProps) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="flex items-center gap-3 px-4 py-3 text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
    >
      <span className="w-5 h-5 text-slate-500">{icon}</span>
      <span>{label}</span>
    </Link>
  )
}
