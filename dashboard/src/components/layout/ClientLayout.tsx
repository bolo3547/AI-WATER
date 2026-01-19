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

  useEffect(() => {
    // Check authentication on client side
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      setIsAuthenticated(!!token)

      // Redirect to login if not authenticated and not on login page
      if (!token && !isLoginPage) {
        window.location.href = '/login'
      }
    }
  }, [isLoginPage])

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
        {/* Fixed Left Sidebar */}
        <Sidebar />
        
        {/* Main Content Area */}
        <div className="flex-1 ml-sidebar">
          {/* Top Status Bar */}
          <TopBar />
          
          {/* Page Content */}
          <main className="mt-topbar p-6">
            {children}
          </main>
        </div>
        
        {/* AI Chat Assistant - floating button */}
        <AIChatAssistant />
      </div>
    </NotificationProvider>
  )
}
