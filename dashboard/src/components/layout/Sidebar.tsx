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
  X,
  Briefcase,
  Calculator,
  MapPin,
  Download,
  ClipboardCheck,
  Globe,
  QrCode,
  ExternalLink,
  Ticket
} from 'lucide-react'

// Role-based navigation - Streamlined for core operations
const adminNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'DMA Management', href: '/dma', icon: Map, badge: '12' },
  { name: 'Alerts Center', href: '/actions', icon: AlertCircle, badge: '3' },
  { name: 'AI Intelligence', href: '/ai', icon: Brain, badge: 'AI' },
  { name: 'Work Orders', href: '/work-orders', icon: Wrench, badge: '5' },
  { name: 'Support Tickets', href: '/tickets', icon: Ticket, badge: 'New' },
  { name: 'Public Reports', href: '/lwsc-zambia/public-reports', icon: Users, badge: 'Live' },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/smart-meters', icon: Gauge, badge: 'Live' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'Billing & Revenue', href: '/billing', icon: DollarSign, badge: 'Live' },
  { name: 'ROI Calculator', href: '/calculator', icon: Calculator, badge: null },
  { name: 'Shift Handover', href: '/shift-handover', icon: ClipboardCheck, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'Firmware Generator', href: '/admin/firmware', icon: Cpu, badge: null },
  { name: 'Security', href: '/admin/security', icon: Shield, badge: null },
]

const operatorNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'DMA Management', href: '/dma', icon: Map, badge: '12' },
  { name: 'Alerts Center', href: '/actions', icon: AlertCircle, badge: '3' },
  { name: 'AI Intelligence', href: '/ai', icon: Brain, badge: 'AI' },
  { name: 'Work Orders', href: '/work-orders', icon: Wrench, badge: '5' },
  { name: 'Support Tickets', href: '/tickets', icon: Ticket, badge: 'New' },
  { name: 'Public Reports', href: '/lwsc-zambia/public-reports', icon: Users, badge: 'Live' },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/smart-meters', icon: Gauge, badge: 'Live' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'Billing & Revenue', href: '/billing', icon: DollarSign, badge: 'Live' },
  { name: 'Shift Handover', href: '/shift-handover', icon: ClipboardCheck, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
]

const technicianNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'Work Orders', href: '/work-orders', icon: Wrench, badge: '5' },
  { name: 'Alerts', href: '/actions', icon: AlertCircle, badge: '2' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
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

  // Close menu when route changes
  useEffect(() => {
    if (isExpanded) {
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

  // UNIFIED: Hamburger menu for both desktop and mobile
  return (
    <>
      {/* Hamburger Button - Fixed position, below government banner */}
      <button
        onClick={onToggle}
        className={clsx(
          "fixed z-50 flex items-center justify-center rounded-xl",
          "bg-gradient-to-br from-slate-800/95 to-slate-900/95 backdrop-blur-md",
          "border border-white/10 text-white shadow-xl",
          "hover:bg-slate-700 hover:border-white/20 hover:scale-105",
          "active:scale-95 transition-all duration-200",
          // Position: below the government banner (32px) with some margin
          "top-[42px] sm:top-[44px] left-3 sm:left-4",
          "w-11 h-11 sm:w-12 sm:h-12"
        )}
        aria-label="Toggle menu"
      >
        <div className="relative">
          {isExpanded ? <X className="w-5 h-5 sm:w-6 sm:h-6" /> : <Menu className="w-5 h-5 sm:w-6 sm:h-6" />}
          {/* Indicator dot when menu closed */}
          {!isExpanded && (
            <span className="absolute -top-1 -right-1 w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
          )}
        </div>
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
        "fixed left-0 top-0 bottom-0 flex flex-col z-50 transition-transform duration-300 ease-out",
        "bg-gradient-to-b from-[var(--sidebar-bg)] to-slate-900/98 border-r border-white/10",
        "shadow-[4px_0_30px_rgba(0,0,0,0.5)]",
        "w-[280px] sm:w-[300px] md:w-[320px]",
        isExpanded ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo Header - Updated spacing */}
        <div className="h-[70px] flex items-center justify-between px-5 border-b border-white/5 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="relative flex-shrink-0">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 flex items-center justify-center border border-white/10">
                <img src="/lwsc-logo.png" alt="LWSC" className="w-8 h-8 object-contain" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-slate-900 animate-pulse" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-bold text-white tracking-tight">LWSC Portal</h1>
              <p className={clsx("text-[11px] font-semibold uppercase tracking-widest", roleColor)}>{roleLabel}</p>
            </div>
          </div>
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Stats - Better spacing */}
        <div className="px-5 py-4 border-b border-white/5">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gradient-to-br from-cyan-500/10 to-blue-600/10 rounded-xl p-3 border border-cyan-500/10">
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-medium">NRW Rate</p>
              <p className="text-2xl font-bold text-white mt-1">32.4%</p>
            </div>
            <div className="bg-gradient-to-br from-amber-500/10 to-orange-600/10 rounded-xl p-3 border border-amber-500/10">
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-medium">Active Alerts</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">3</p>
            </div>
          </div>
        </div>

        {/* Navigation - Better text alignment */}
        <nav className="flex-1 py-4 px-4 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          <p className="px-3 py-2 text-[10px] font-semibold text-slate-500 uppercase tracking-[0.15em]">Navigation</p>
          <div className="space-y-1.5">
            {navigation.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/' && pathname.startsWith(item.href))
              
              if ((item as any).external) {
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={clsx(
                      'group flex items-center gap-4 px-4 py-3.5 rounded-xl font-medium transition-all duration-200',
                      isActive 
                        ? 'bg-gradient-to-r from-[var(--sidebar-accent)] to-cyan-600/80 text-white shadow-lg shadow-cyan-500/20' 
                        : 'text-slate-300 hover:bg-white/5 hover:text-white active:bg-white/10'
                    )}
                  >
                    <div className={clsx(
                      'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                      isActive 
                        ? 'bg-white/20' 
                        : 'bg-slate-800/50 group-hover:bg-slate-700/50'
                    )}>
                      <item.icon className={clsx(
                        'w-5 h-5',
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                      )} />
                    </div>
                    <span className="flex-1 text-[14px] truncate">{item.name}</span>
                    <ExternalLink className="w-4 h-4 text-slate-500 flex-shrink-0" />
                  </a>
                )
              }
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'group flex items-center gap-4 px-4 py-3.5 rounded-xl font-medium transition-all duration-200',
                    isActive 
                      ? 'bg-gradient-to-r from-[var(--sidebar-accent)] to-cyan-600/80 text-white shadow-lg shadow-cyan-500/20' 
                      : 'text-slate-300 hover:bg-white/5 hover:text-white active:bg-white/10'
                  )}
                >
                  <div className={clsx(
                    'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors',
                    isActive 
                      ? 'bg-white/20' 
                      : 'bg-slate-800/50 group-hover:bg-slate-700/50'
                  )}>
                    <item.icon className={clsx(
                      'w-5 h-5',
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                    )} />
                  </div>
                  <span className="flex-1 text-[14px] truncate">{item.name}</span>
                  {item.badge && (
                    <span className={clsx(
                      'px-2.5 py-1 rounded-lg text-[11px] font-bold flex-shrink-0',
                      isActive 
                        ? 'bg-white/25 text-white' 
                        : item.badge === 'Live' 
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : item.badge === 'AI' 
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : item.badge === 'New'
                              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    )}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </div>
        </nav>

        {/* AI Status - Better alignment */}
        <div className="px-5 py-4 border-t border-white/5">
          <div className="flex items-center gap-4 px-4 py-3.5 bg-gradient-to-r from-emerald-500/10 to-green-600/10 rounded-xl border border-emerald-500/20">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white">AI Engine Active</p>
              <p className="text-xs text-emerald-400 font-medium">94% confidence level</p>
            </div>
            <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse flex-shrink-0" />
          </div>
        </div>

        {/* Footer - Better alignment */}
        <div className="px-5 py-4 border-t border-white/5 bg-slate-900/50">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 font-medium">Version</span>
              <span className="text-slate-400 font-mono">2.4.1</span>
            </div>
            <div className="flex items-center gap-2 text-emerald-400">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
              <span className="font-medium">System Online</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
