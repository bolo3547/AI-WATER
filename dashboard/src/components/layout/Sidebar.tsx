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
  ExternalLink
} from 'lucide-react'

// Role-based navigation
const adminNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'Executive View', href: '/executive', icon: Briefcase, badge: 'New' },
  { name: 'Communications', href: '/communications', icon: MessageSquare, badge: 'New' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'AI Intelligence', href: '/ai', icon: Brain, badge: 'AI' },
  { name: 'Predictions', href: '/predictions', icon: Activity, badge: 'New' },
  { name: 'Network Map', href: '/map', icon: MapPin, badge: 'New' },
  { name: 'DMA Management', href: '/dma', icon: Map, badge: '12' },
  { name: 'Alerts Center', href: '/actions', icon: AlertCircle, badge: '3' },
  { name: 'Satellite/Drone', href: '/satellite', icon: Satellite, badge: 'New' },
  { name: 'Autonomous Ops', href: '/autonomous', icon: Bot, badge: 'AI' },
  { name: 'Work Orders', href: '/work-orders', icon: Wrench, badge: '5' },
  { name: 'Public Reports', href: '/lwsc-zambia/public-reports', icon: Users, badge: 'Live' },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/smart-meters', icon: Gauge, badge: 'Live' },
  { name: 'Water Quality', href: '/water-quality', icon: Droplets, badge: 'Live' },
  { name: 'Billing & Revenue', href: '/billing', icon: DollarSign, badge: 'New' },
  { name: 'Inventory', href: '/inventory', icon: Database, badge: null },
  { name: 'Shift Handover', href: '/shift-handover', icon: ClipboardCheck, badge: null },
  { name: 'Customer Portal', href: '/customer-portal', icon: Users, badge: 'New' },
  { name: 'Weather Impact', href: '/weather', icon: CloudRain, badge: null },
  { name: 'Analytics', href: '/analytics', icon: Activity, badge: null },
  { name: 'ROI Calculator', href: '/calculator', icon: Calculator, badge: 'New' },
  { name: 'Revenue Intel', href: '/finance', icon: DollarSign, badge: null },
  { name: 'System Health', href: '/health', icon: Settings, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'Data Export', href: '/export', icon: Download, badge: null },
  { name: 'Audit Trail', href: '/audit', icon: ClipboardCheck, badge: null },
  { name: 'Community', href: '/community', icon: Users, badge: '15' },
  { name: 'Promote Reports', href: '/promote', icon: QrCode, badge: 'New' },
  { name: 'Public Portal', href: '/report-leak', icon: ExternalLink, badge: null, external: true },
  { name: 'User Management', href: '/admin/users', icon: Users, badge: null },
  { name: 'Locations', href: '/admin/locations', icon: Map, badge: null },
  { name: 'System Config', href: '/admin/config', icon: Database, badge: null },
  { name: 'Firmware Generator', href: '/admin/firmware', icon: Cpu, badge: null },
  { name: 'Security', href: '/admin/security', icon: Shield, badge: null },
]

const operatorNavigation = [
  { name: 'Control Room', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'Executive View', href: '/executive', icon: Briefcase, badge: 'New' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'New' },
  { name: 'Network Map', href: '/map', icon: MapPin, badge: 'New' },
  { name: 'DMA Monitoring', href: '/dma', icon: Map, badge: '12' },
  { name: 'Active Alerts', href: '/actions', icon: Bell, badge: '3' },
  { name: 'Predictions', href: '/predictions', icon: Activity, badge: 'New' },
  { name: 'Satellite/Drone', href: '/satellite', icon: Satellite, badge: null },
  { name: 'Work Orders', href: '/work-orders', icon: Wrench, badge: '5' },
  { name: 'Field Crews', href: '/field', icon: UserCheck, badge: '6' },
  { name: 'Smart Meters', href: '/smart-meters', icon: Gauge, badge: 'Live' },
  { name: 'Water Quality', href: '/water-quality', icon: Droplets, badge: 'Live' },
  { name: 'Inventory', href: '/inventory', icon: Database, badge: null },
  { name: 'Shift Handover', href: '/shift-handover', icon: ClipboardCheck, badge: null },
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
      {/* Hamburger Button - Fixed position */}
      <button
        onClick={onToggle}
        className={clsx(
          "fixed z-50 flex items-center justify-center rounded-xl bg-slate-800/90 backdrop-blur-sm border border-white/10 text-white shadow-lg hover:bg-slate-700 transition-all",
          isMobile 
            ? "top-9 sm:top-10 left-2 w-9 h-9 sm:w-10 sm:h-10"
            : "top-9 left-3 w-10 h-10"
        )}
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
        "fixed left-0 top-0 bottom-0 flex flex-col z-50 transition-transform duration-300 ease-in-out",
        "bg-[var(--sidebar-bg)] border-r border-white/5 shadow-2xl",
        isMobile ? "w-80" : "w-72 md:w-80",
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
              
              if ((item as any).external) {
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={clsx(
                      'flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-150',
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
                    <ExternalLink className="w-3 h-3 text-slate-500" />
                  </a>
                )
              }
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-all duration-150',
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
