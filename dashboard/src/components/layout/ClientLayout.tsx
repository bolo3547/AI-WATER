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

  // Close sidebar when route changes
  useEffect(() => {
    setSidebarOpen(false)
  }, [pathname])

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handleResize = () => {
      // Auto-close on very small screens when resizing
      if (window.innerWidth < 640 && sidebarOpen) {
        // Keep open, user will close manually
      }
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [sidebarOpen])

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
        {/* Menu Toggle Button - Always visible */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className={`fixed top-4 z-50 p-2.5 bg-slate-900 text-white rounded-lg shadow-lg transition-all duration-300 ${
            sidebarOpen ? 'left-[216px] sm:left-[232px]' : 'left-4'
          }`}
          aria-label="Toggle menu"
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Overlay - closes sidebar when clicked */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - Slides in/out on all devices */}
        <div className={`
          fixed inset-y-0 left-0 z-40
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <Sidebar onClose={() => setSidebarOpen(false)} />
        </div>
        
        {/* Main Content Area - Full width always */}
        <div className="flex-1 min-w-0 w-full">
          {/* Top Status Bar */}
          <TopBar sidebarOpen={sidebarOpen} />
          
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
