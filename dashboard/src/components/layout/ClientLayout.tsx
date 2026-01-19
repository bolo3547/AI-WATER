'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { NotificationProvider } from '@/lib/notifications'
import AIChatAssistant from '@/components/ai/AIChatAssistant'
import { InstallPrompt } from '@/components/pwa/InstallPrompt'

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    // Check authentication on client side
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      setIsAuthenticated(!!token)

      // Redirect to login if not authenticated and not on login page
      if (!token && !isLoginPage) {
        window.location.href = '/login'
      }
      
      // Check if mobile
      const checkMobile = () => {
        setIsMobile(window.innerWidth < 768)
      }
      checkMobile()
      window.addEventListener('resize', checkMobile)
      
      // Load sidebar state from localStorage (only for desktop)
      const savedSidebarState = localStorage.getItem('sidebarExpanded')
      if (savedSidebarState !== null && window.innerWidth >= 768) {
        setSidebarExpanded(savedSidebarState === 'true')
      } else {
        // Default: collapsed on all devices initially
        setSidebarExpanded(false)
      }
      
      return () => window.removeEventListener('resize', checkMobile)
    }
  }, [isLoginPage])

  // Save sidebar state to localStorage
  const handleSidebarToggle = () => {
    const newState = !sidebarExpanded
    setSidebarExpanded(newState)
    if (!isMobile) {
      localStorage.setItem('sidebarExpanded', String(newState))
    }
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

  // Calculate sidebar width based on state and device
  const sidebarWidth = isMobile 
    ? (sidebarExpanded ? 240 : 56)  // Smaller on mobile
    : (sidebarExpanded ? 256 : 64)  // Normal on desktop

  // Dashboard pages - with sidebar/topbar and notifications
  return (
    <NotificationProvider>
      <div className="flex min-h-screen">
        {/* Sidebar - Always visible, expands/collapses like ChatGPT */}
        <Sidebar isExpanded={sidebarExpanded} onToggle={handleSidebarToggle} isMobile={isMobile} />
        
        {/* Main Content Area - Adjusts margin based on sidebar state */}
        <div 
          className="flex-1 min-w-0 transition-all duration-300"
          style={{ marginLeft: `${sidebarWidth}px` }}
        >
          {/* Top Status Bar */}
          <TopBar />
          
          {/* Page Content - tighter padding on mobile */}
          <main className="mt-14 sm:mt-16 p-2 sm:p-4 lg:p-6">
            {children}
          </main>
        </div>
        
        {/* AI Chat Assistant - floating button */}
        <AIChatAssistant />
        
        {/* PWA Install Prompt */}
        <InstallPrompt />
      </div>
    </NotificationProvider>
  )
}
