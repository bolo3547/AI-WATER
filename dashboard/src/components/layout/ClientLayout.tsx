'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { NotificationProvider } from '@/lib/notifications'
import AIChatAssistant from '@/components/ai/AIChatAssistant'
import { Menu, X } from 'lucide-react'

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

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

  // Close sidebar when route changes on mobile
  useEffect(() => {
    setSidebarOpen(false)
  }, [pathname])

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
        {/* Mobile Menu Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-slate-900 text-white rounded-lg shadow-lg"
          aria-label="Toggle menu"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>

        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 bg-black/50 z-30"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - hidden on mobile, shown on desktop */}
        <div className={`
          fixed lg:fixed inset-y-0 left-0 z-40
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}>
          <Sidebar />
        </div>
        
        {/* Main Content Area */}
        <div className="flex-1 lg:ml-64 min-w-0">
          {/* Top Status Bar */}
          <TopBar />
          
          {/* Page Content - responsive padding */}
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
