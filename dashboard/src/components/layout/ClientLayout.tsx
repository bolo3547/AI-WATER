'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { NotificationProvider } from '@/lib/notifications'
import AIChatAssistant from '@/components/ai/AIChatAssistant'
import { InstallPrompt } from '@/components/pwa/InstallPrompt'
import { SplashScreen } from '@/components/ui/SplashScreen'

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'
  const isPortalPage = pathname === '/portal'
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [showSplash, setShowSplash] = useState(true)
  const [splashComplete, setSplashComplete] = useState(false)

  useEffect(() => {
    // Check if splash was shown this session
    if (typeof window !== 'undefined') {
      const splashShown = sessionStorage.getItem('splashShown')
      if (splashShown) {
        setShowSplash(false)
        setSplashComplete(true)
      }
    }
  }, [])

  const handleSplashComplete = () => {
    setSplashComplete(true)
    setShowSplash(false)
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('splashShown', 'true')
    }
  }

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

  // Show splash screen on first load (not on login or portal page)
  if (showSplash && !isLoginPage && !isPortalPage) {
    return <SplashScreen onComplete={handleSplashComplete} />
  }

  // Show loading while checking auth (after splash)
  if (isAuthenticated === null && !isLoginPage && !isPortalPage) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          <p style={{ color: 'var(--text-muted)' }}>Loading...</p>
        </div>
      </div>
    )
  }

  // Login page - no sidebar/topbar
  if (isLoginPage) {
    return <>{children}</>
  }

  // Portal page - public, no auth required
  if (isPortalPage) {
    return <>{children}</>
  }
  if (isLoginPage) {
    return <>{children}</>
  }

  // Not authenticated - show nothing (will redirect)
  if (!isAuthenticated) {
    return null
  }

  // Calculate sidebar width based on state and device
  // On mobile, sidebar is a slide-out menu, so no margin needed
  const sidebarWidth = isMobile 
    ? 0  // Mobile: hamburger menu, no sidebar margin
    : (sidebarExpanded ? 256 : 64)  // Desktop: normal sidebar

  // Dashboard pages - with sidebar/topbar and notifications
  return (
    <NotificationProvider>
      <div className="flex min-h-screen">
        {/* Sidebar - Desktop: always visible. Mobile: hamburger menu */}
        <Sidebar isExpanded={sidebarExpanded} onToggle={handleSidebarToggle} isMobile={isMobile} />
        
        {/* Main Content Area - Adjusts margin based on sidebar state */}
        <div 
          className="flex-1 min-w-0 transition-all duration-300"
          style={{ marginLeft: `${sidebarWidth}px` }}
        >
          {/* Top Status Bar */}
          <TopBar />
          
          {/* Page Content - tighter padding on mobile, account for government banner */}
          <main className="mt-[76px] sm:mt-[86px] p-2 sm:p-4 lg:p-6">
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
