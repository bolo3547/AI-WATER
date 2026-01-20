'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { clsx } from 'clsx'
import { 
  LayoutDashboard, 
  Map, 
  AlertCircle, 
  Activity,
  Settings,
  FileText,
  Droplets,
  ChevronRight,
  Zap,
  Users,
  Shield,
  Database,
  Wrench,
  Bell,
  Cpu,
  Brain,
  ChevronLeft,
  PanelLeftClose,
  PanelLeft,
  Satellite,
  Bot,
  DollarSign,
  UserCheck,
  MessageSquare,
  Gauge,
  CloudRain,
  Menu,
  X
} from 'lucide-react'

// Role-based navigation
const adminNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'AI Intelligence', href: '/ai', icon: Brain, badge: 'AI' },
  { name: 'Predictions', href: '/predictions', icon: Activity, badge: 'New' },
  { name: 'DMA Management', href: '/dma', icon: Map, badge: '12' },
  { name: 'Alerts Center', href: '/actions', icon: AlertCircle, badge: '3' },
  { name: 'Satellite/Drone', href: '/satellite', icon: Satellite, badge: 'New' },
  { name: 'Autonomous Ops', href: '/autonomous', icon: Bot, badge: 'AI' },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/meters', icon: Gauge, badge: null },
  { name: 'Weather Impact', href: '/weather', icon: CloudRain, badge: null },
  { name: 'Analytics', href: '/analytics', icon: Activity, badge: null },
  { name: 'Revenue Intel', href: '/finance', icon: DollarSign, badge: null },
  { name: 'System Health', href: '/health', icon: Settings, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'Community', href: '/community', icon: MessageSquare, badge: '15' },
  { name: 'User Management', href: '/admin/users', icon: Users, badge: null },
  { name: 'Locations', href: '/admin/locations', icon: Map, badge: null },
  { name: 'System Config', href: '/admin/config', icon: Database, badge: null },
  { name: 'Firmware Generator', href: '/admin/firmware', icon: Cpu, badge: null },
  { name: 'Security', href: '/admin/security', icon: Shield, badge: null },
]

const operatorNavigation = [
  { name: 'Control Room', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'DMA Monitoring', href: '/dma', icon: Map, badge: '12' },
  { name: 'Active Alerts', href: '/actions', icon: Bell, badge: '3' },
  { name: 'Predictions', href: '/predictions', icon: Activity, badge: 'New' },
  { name: 'Satellite/Drone', href: '/satellite', icon: Satellite, badge: null },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/meters', icon: Gauge, badge: null },
  { name: 'Weather Impact', href: '/weather', icon: CloudRain, badge: null },
  { name: 'Field Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'Community', href: '/community', icon: MessageSquare, badge: '15' },
  { name: 'System Status', href: '/health', icon: Activity, badge: null },
]

const technicianNavigation = [
  { name: 'My Tasks', href: '/', icon: Wrench, badge: '5' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'Field Map', href: '/dma', icon: Map, badge: null },
  { name: 'Alerts', href: '/actions', icon: AlertCircle, badge: '2' },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'Community', href: '/community', icon: MessageSquare, badge: '15' },
]

interface SidebarProps {
  isExpanded: boolean
  onToggle: () => void
  isMobile?: boolean
}

export function Sidebar({ isExpanded, onToggle, isMobile = false }: SidebarProps) {
  const pathname = usePathname()
  const [userRole, setUserRole] = useState<string>('operator')
  const [username, setUsername] = useState<string>('')
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedUser = localStorage.getItem('user')
      if (storedUser) {
        const user = JSON.parse(storedUser)
        setUserRole(user.role || 'operator')
        setUsername(user.username || 'User')
      }
    }
  }, [])

  // Close mobile menu when route changes
  useEffect(() => {
    if (isMobile && isExpanded) {
      onToggle()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname])

  // Get navigation based on role
  const getNavigation = () => {
    switch (userRole) {
      case 'admin':
        return adminNavigation
      case 'technician':
        return technicianNavigation
      default:
        return operatorNavigation
    }
  }

  const navigation = getNavigation()
  const roleLabel = userRole === 'admin' ? 'Administrator' : userRole === 'technician' ? 'Field Tech' : 'Operator'
  const roleColor = userRole === 'admin' ? 'text-purple-400' : userRole === 'technician' ? 'text-orange-400' : 'text-cyan-400'

  // MOBILE: Hamburger menu that slides in from left
  if (isMobile) {
    return (
      <>
        {/* Hamburger Button - Fixed below government banner */}
        <button
          onClick={onToggle}
          className="fixed top-9 sm:top-10 left-2 z-50 w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center rounded-xl bg-[var(--sidebar-bg)] border border-white/10 text-white shadow-lg"
          aria-label="Toggle menu"
        >
          {isExpanded ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Overlay */}
        {isExpanded && (
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onToggle}
          />
        )}

        {/* Slide-out Menu */}
        <aside className={clsx(
          "fixed left-0 top-0 bottom-0 w-80 flex flex-col z-50 transition-transform duration-300 ease-in-out",
          "bg-[var(--sidebar-bg)] border-r border-white/5 shadow-2xl",
          isExpanded ? "translate-x-0" : "-translate-x-full"
        )}>
          {/* Logo Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-white/5">
            <div className="flex items-center gap-3">
              <div className="relative flex-shrink-0">
                <img src="/lwsc-logo.png" alt="LWSC" className="w-10 h-10 object-contain" />
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-slate-900" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">LWSC</h1>
                <p className={clsx("text-xs font-medium uppercase tracking-wider", roleColor)}>{roleLabel}</p>
              </div>
            </div>
            <button
              onClick={onToggle}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Stats */}
          <div className="px-4 py-3 border-b border-white/5">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">NRW Rate</p>
                <p className="text-xl font-bold text-white">32.4%</p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Active Alerts</p>
                <p className="text-xl font-bold text-amber-400">3</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 py-3 px-3 overflow-y-auto">
            <p className="px-3 py-2 text-[10px] font-medium text-slate-500 uppercase tracking-wider">Menu</p>
            <div className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href || 
                  (item.href !== '/' && pathname.startsWith(item.href))
                
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={clsx(
                      'flex items-center gap-3 px-4 py-3.5 rounded-xl font-medium transition-all duration-150',
                      isActive 
                        ? 'bg-[var(--sidebar-accent)] text-white' 
                        : 'text-slate-400 hover:bg-white/5 hover:text-white active:bg-white/10'
                    )}
                  >
                    <item.icon className={clsx(
                      'w-5 h-5 flex-shrink-0',
                      isActive ? 'text-white' : 'text-slate-500'
                    )} />
                    <span className="flex-1">{item.name}</span>
                    {item.badge && (
                      <span className={clsx(
                        'px-2 py-1 rounded-lg text-xs font-semibold',
                        isActive ? 'bg-white/20 text-white' : 'bg-[var(--sidebar-accent)]/20 text-[var(--primary-light)]'
                      )}>
                        {item.badge}
                      </span>
                    )}
                  </Link>
                )
              })}
            </div>
          </nav>

          {/* AI Status */}
          <div className="px-4 py-3 border-t border-white/5">
            <div className="flex items-center gap-3 px-4 py-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <Zap className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-white">AI Active</p>
                <p className="text-xs text-emerald-400">94% confidence</p>
              </div>
              <div className="w-2 h-2 bg-emerald-400 rounded-full pulse-live" />
            </div>
          </div>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-white/5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">v2.4.1</span>
              <span className="text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span>
                Connected
              </span>
            </div>
          </div>
        </aside>
      </>
    )
  }

  // DESKTOP: Traditional collapsible sidebar
  return (
    <aside className={clsx(
      "fixed left-0 top-7 sm:top-8 bottom-0 flex flex-col z-40 transition-all duration-300 ease-in-out",
      "bg-[var(--sidebar-bg)] border-r border-white/5",
      isExpanded ? 'w-64' : 'w-16'
    )}>
      {/* Logo - LWSC Branding */}
      <div className={clsx(
        "h-12 sm:h-14 flex items-center border-b border-white/5 transition-all duration-300",
        isExpanded ? "px-4" : "px-2 justify-center"
      )}>
        <div className="flex items-center gap-3">
          <div className="relative flex-shrink-0">
            <img src="/lwsc-logo.png" alt="LWSC" className="w-8 h-8 sm:w-9 sm:h-9 object-contain" />
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full border border-slate-900" />
          </div>
          {isExpanded && (
            <div className="overflow-hidden">
              <h1 className="text-sm sm:text-base font-semibold text-white tracking-tight">LWSC</h1>
              <p className={clsx("text-[9px] sm:text-[10px] font-medium uppercase tracking-wider", roleColor)}>{roleLabel}</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Quick Stats - Only show when expanded */}
      {isExpanded && (
        <div className="px-3 py-2 sm:py-2.5 border-b border-white/5">
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 rounded-lg p-2 sm:p-2.5">
              <p className="text-[8px] sm:text-[9px] text-slate-400 uppercase tracking-wider">NRW Rate</p>
              <p className="text-sm sm:text-base font-semibold text-white">32.4%</p>
            </div>
            <div className="bg-white/5 rounded-lg p-2 sm:p-2.5">
              <p className="text-[8px] sm:text-[9px] text-slate-400 uppercase tracking-wider">Alerts</p>
              <p className="text-sm sm:text-base font-semibold text-amber-400">3</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Navigation */}
      <nav className={clsx(
        "flex-1 py-2 space-y-0.5 overflow-y-auto scrollbar-hidden",
        isExpanded ? "px-2" : "px-1"
      )}>
        {isExpanded && (
          <p className="px-3 py-2 text-[10px] font-medium text-slate-500 uppercase tracking-wider">Menu</p>
        )}
        {navigation.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.name}
              href={item.href}
              title={!isExpanded ? item.name : undefined}
              className={clsx(
                'group flex items-center text-[13px] font-medium transition-all duration-150 relative',
                isExpanded 
                  ? 'gap-3 px-3 py-2 rounded-lg mx-1'
                  : 'justify-center p-2.5 rounded-lg mx-1',
                isActive 
                  ? 'bg-[var(--sidebar-accent)] text-white' 
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              )}
            >
              <item.icon className={clsx(
                'w-[18px] h-[18px] flex-shrink-0 transition-colors',
                isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'
              )} />
              {isExpanded && (
                <>
                  <span className="flex-1 truncate">{item.name}</span>
                  {item.badge && (
                    <span className={clsx(
                      'px-1.5 py-0.5 rounded text-[10px] font-semibold',
                      isActive ? 'bg-white/20 text-white' : 'bg-[var(--sidebar-accent)]/20 text-[var(--primary-light)]'
                    )}>
                      {item.badge}
                    </span>
                  )}
                </>
              )}
              {/* Badge indicator when collapsed */}
              {!isExpanded && item.badge && (
                <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-[var(--sidebar-accent)] rounded-full text-[8px] font-bold text-white flex items-center justify-center">
                  {item.badge === 'AI' || item.badge === 'New' ? '•' : item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>
      
      {/* AI Status */}
      <div className={clsx(
        "border-t border-white/5 transition-all duration-300",
        isExpanded ? "px-3 py-2.5" : "px-2 py-2"
      )}>
        {isExpanded ? (
          <div className="flex items-center gap-2.5 px-3 py-2.5 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">AI Active</p>
              <p className="text-[10px] text-emerald-400">94% confidence</p>
            </div>
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full pulse-live flex-shrink-0" />
          </div>
        ) : (
          <div className="flex justify-center p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
            <div className="relative">
              <Zap className="w-4 h-4 text-emerald-400" />
              <div className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-emerald-400 rounded-full pulse-live" />
            </div>
          </div>
        )}
      </div>
      
      {/* Toggle Button & Footer */}
      <div className={clsx(
        "border-t border-white/5 transition-all duration-300",
        isExpanded ? "px-3 py-2.5" : "px-2 py-2"
      )}>
        {/* Toggle Button */}
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center gap-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all duration-150 mb-2"
          title={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
        >
          {isExpanded ? (
            <>
              <PanelLeftClose className="w-4 h-4" />
              <span className="text-xs font-medium">Collapse</span>
            </>
          ) : (
            <PanelLeft className="w-4 h-4" />
          )}
        </button>
        
        {/* Footer Info */}
        {isExpanded ? (
          <div className="flex items-center justify-between px-2 text-[10px]">
            <span className="text-slate-500">v2.4.1</span>
            <span className="text-emerald-400">Connected</span>
          </div>
        ) : (
          <div className="text-center">
            <p className="text-[9px] text-slate-500">v2.4</p>
          </div>
        )}
      </div>
    </aside>
  )
}
