'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { NotificationProvider } from '@/lib/notifications'
import AIChatAssistant from '@/components/ai/AIChatAssistant'

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [sidebarExpanded, setSidebarExpanded] = useState(true)

  useEffect(() => {
    // Check authentication on client side
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      setIsAuthenticated(!!token)

      // Redirect to login if not authenticated and not on login page
      if (!token && !isLoginPage) {
        window.location.href = '/login'
      }
      
      // Load sidebar state from localStorage
      const savedSidebarState = localStorage.getItem('sidebarExpanded')
      if (savedSidebarState !== null) {
        setSidebarExpanded(savedSidebarState === 'true')
      } else {
        // Default: expanded on desktop, collapsed on mobile
        setSidebarExpanded(window.innerWidth >= 768)
      }
    }
  }, [isLoginPage])

  // Save sidebar state to localStorage
  const handleSidebarToggle = () => {
    const newState = !sidebarExpanded
    setSidebarExpanded(newState)
    localStorage.setItem('sidebarExpanded', String(newState))
  }

  // Show loading while checking auth
  if (isAuthenticated === null && !isLoginPage) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          <p className="text-slate-500">Loading...</p>
        </div>
      </div>
    )
  }

  // Login page - no sidebar/topbar
  if (isLoginPage) {
    return <>{children}</>
  }

  // Not authenticated - show nothing (will redirect)
  if (!isAuthenticated) {
    return null
  }

  // Dashboard pages - with sidebar/topbar and notifications
  return (
    <NotificationProvider>
      <div className="flex min-h-screen">
        {/* Sidebar - Always visible, expands/collapses like ChatGPT */}
        <Sidebar isExpanded={sidebarExpanded} onToggle={handleSidebarToggle} />
        
        {/* Main Content Area - Adjusts margin based on sidebar state */}
        <div 
          className="flex-1 min-w-0 transition-all duration-300"
          style={{ marginLeft: sidebarExpanded ? '256px' : '64px' }}
        >
          {/* Top Status Bar */}
          <TopBar />
          
          {/* Page Content */}
          <main className="mt-16 p-3 sm:p-4 lg:p-6">
            {children}
          </main>
        </div>
        
        {/* AI Chat Assistant - floating button */}
        <AIChatAssistant />
      </div>
    </NotificationProvider>
  )
}
