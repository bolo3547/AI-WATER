'use client'

import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { NotificationProvider } from '@/lib/notifications'
import { SystemStatusProvider } from '@/contexts/SystemStatusContext'
import AIChatAssistant from '@/components/ai/AIChatAssistant'
import { InstallPrompt } from '@/components/pwa/InstallPrompt'
import { SplashScreen } from '@/components/ui/SplashScreen'
import { SystemStatusBanner } from '@/components/SystemStatus'

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isStaffLoginPage = pathname === '/staff/login'
  const isOldLoginPage = pathname === '/login'
  const isPortalPage = pathname === '/portal'
  const isPublicReportPage = pathname === '/report-leak' || pathname === '/report'
  const isPublicLanding = pathname === '/' || pathname === '/public'
  const isTicketPage = pathname === '/ticket' || pathname.startsWith('/ticket/')
  const isNewsPage = pathname === '/news' || pathname.startsWith('/news/')
  const isTrackPage = pathname === '/track' || pathname.startsWith('/track/')
  const isSharePage = pathname === '/share' || pathname.startsWith('/share/')
  const isPublicPage = isStaffLoginPage || isOldLoginPage || isPortalPage || isPublicReportPage || isPublicLanding || isTicketPage || isNewsPage || isTrackPage || isSharePage
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

      // Redirect to staff login if not authenticated and not on public page
      if (!token && !isPublicPage) {
        window.location.href = '/staff/login'
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
  }, [isPublicPage])

  // Save sidebar state to localStorage
  const handleSidebarToggle = () => {
    const newState = !sidebarExpanded
    setSidebarExpanded(newState)
    if (!isMobile) {
      localStorage.setItem('sidebarExpanded', String(newState))
    }
  }

  // Show splash screen on first load (not on public pages)
  if (showSplash && !isPublicPage) {
    return <SplashScreen onComplete={handleSplashComplete} />
  }

  // Show loading while checking auth (after splash, not on public pages)
  if (isAuthenticated === null && !isPublicPage) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--bg-secondary)' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          <p style={{ color: 'var(--text-muted)' }}>Loading...</p>
        </div>
      </div>
    )
  }

  // Staff login page - no sidebar/topbar
  if (isStaffLoginPage || isOldLoginPage) {
    return <>{children}</>
  }

  // Public pages - no auth required, standalone layout
  if (isPublicPage) {
    return <>{children}</>
  }

  // Not authenticated - show nothing (will redirect)
  if (!isAuthenticated) {
    return null
  }

  // Calculate sidebar width based on state and device
  // Now using hamburger menu on all devices - no sidebar margin needed
  const sidebarWidth = 0  // Menu slides over content

  // Dashboard pages - with sidebar/topbar and notifications
  return (
    <SystemStatusProvider>
      <NotificationProvider>
        <div className="flex min-h-screen">
          {/* Sidebar - Hamburger menu on all devices */}
          <Sidebar isExpanded={sidebarExpanded} onToggle={handleSidebarToggle} isMobile={isMobile} />
          
          {/* Main Content Area - Full width since sidebar is overlay */}
          <div className="flex-1 min-w-0">
            {/* System Status Banner - Shows when data is stale/offline */}
            <div className="fixed top-0 left-0 right-0 z-30">
              <SystemStatusBanner />
            </div>
            
            {/* Top Status Bar */}
            <TopBar />
            
            {/* Page Content - proper padding to avoid hamburger menu */}
            <main className="mt-[76px] sm:mt-[86px] p-3 sm:p-4 lg:p-6 pl-[70px] sm:pl-[76px]">
              {children}
            </main>
          </div>
          
          {/* AI Chat Assistant - floating button */}
          <AIChatAssistant />
          
          {/* PWA Install Prompt */}
          <InstallPrompt />
        </div>
      </NotificationProvider>
    </SystemStatusProvider>
  )
}
