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
  Brain
} from 'lucide-react'

// Role-based navigation
const adminNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'AI Intelligence', href: '/ai', icon: Brain, badge: 'AI' },
  { name: 'DMA Management', href: '/dma', icon: Map, badge: '12' },
  { name: 'Alerts Center', href: '/actions', icon: AlertCircle, badge: '3' },
  { name: 'Analytics', href: '/analytics', icon: Activity, badge: null },
  { name: 'System Health', href: '/health', icon: Settings, badge: null },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'User Management', href: '/admin/users', icon: Users, badge: null },
  { name: 'Locations', href: '/admin/locations', icon: Map, badge: 'New' },
  { name: 'System Config', href: '/admin/config', icon: Database, badge: null },
  { name: 'Firmware Generator', href: '/admin/firmware', icon: Cpu, badge: null },
  { name: 'Security', href: '/admin/security', icon: Shield, badge: null },
]

const operatorNavigation = [
  { name: 'Control Room', href: '/', icon: LayoutDashboard, badge: null },
  { name: 'DMA Monitoring', href: '/dma', icon: Map, badge: '12' },
  { name: 'Active Alerts', href: '/actions', icon: Bell, badge: '3' },
  { name: 'Field Reports', href: '/reports', icon: FileText, badge: null },
  { name: 'System Status', href: '/health', icon: Activity, badge: null },
]

const technicianNavigation = [
  { name: 'My Tasks', href: '/', icon: Wrench, badge: '5' },
  { name: 'Field Map', href: '/dma', icon: Map, badge: null },
  { name: 'Alerts', href: '/actions', icon: AlertCircle, badge: '2' },
  { name: 'Reports', href: '/reports', icon: FileText, badge: null },
]

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
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

  const handleNavClick = () => {
    // Close sidebar on navigation (especially important on mobile)
    if (onClose) onClose()
  }
  
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] sm:w-64 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 flex flex-col shadow-xl z-20">
      {/* Logo - LWSC Branding */}
      <div className="h-16 sm:h-20 px-4 sm:px-5 flex items-center border-b border-white/10 ml-10 sm:ml-12">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="relative">
            <img src="/lwsc-logo.png" alt="LWSC" className="w-10 h-10 sm:w-12 sm:h-12 object-contain" />
            <div className="absolute -top-1 -right-1 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-emerald-400 rounded-full border-2 border-slate-900 pulse-live" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-white tracking-tight">LWSC</h1>
            <p className="text-[8px] sm:text-[9px] text-blue-300 leading-tight">Water Is Life</p>
            <p className={clsx("text-[9px] sm:text-[10px] font-medium uppercase tracking-wider", roleColor)}>{roleLabel}</p>
          </div>
        </div>
      </div>
      
      {/* Quick Stats */}
      <div className="px-3 sm:px-4 py-3 sm:py-4 border-b border-white/10">
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-white/5 rounded-lg p-2.5 sm:p-3">
            <p className="text-[9px] sm:text-[10px] text-slate-400 uppercase tracking-wider">NRW Rate</p>
            <p className="text-lg sm:text-xl font-bold text-white">32.4%</p>
          </div>
          <div className="bg-white/5 rounded-lg p-2.5 sm:p-3">
            <p className="text-[9px] sm:text-[10px] text-slate-400 uppercase tracking-wider">Alerts</p>
            <p className="text-lg sm:text-xl font-bold text-amber-400">3</p>
          </div>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 px-2 sm:px-3 py-3 sm:py-4 space-y-1 overflow-y-auto scrollbar-thin">
        <p className="px-3 py-2 text-[9px] sm:text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Main Menu</p>
        {navigation.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={handleNavClick}
              className={clsx(
                'group flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-2 sm:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-medium transition-all duration-200',
                isActive 
                  ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/25' 
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              )}
            >
              <item.icon className={clsx(
                'w-4 sm:w-5 h-4 sm:h-5 transition-transform group-hover:scale-110 flex-shrink-0',
                isActive ? 'text-white' : 'text-slate-500 group-hover:text-blue-400'
              )} />
              <span className="flex-1 truncate">{item.name}</span>
              {item.badge && (
                <span className={clsx(
                  'px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold',
                  isActive ? 'bg-white/20 text-white' : 'bg-blue-500/20 text-blue-400'
                )}>
                  {item.badge}
                </span>
              )}
              {isActive && <ChevronRight className="w-3 sm:w-4 h-3 sm:h-4 flex-shrink-0" />}
            </Link>
          )
        })}
      </nav>
      
      {/* AI Status */}
      <div className="px-3 sm:px-4 py-2.5 sm:py-3 border-t border-white/10">
        <div className="flex items-center gap-2 sm:gap-3 px-2.5 sm:px-3 py-2.5 sm:py-3 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 rounded-lg sm:rounded-xl border border-emerald-500/20">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
            <Zap className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-emerald-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] sm:text-xs font-semibold text-white truncate">AI Engine Active</p>
            <p className="text-[9px] sm:text-[10px] text-emerald-400">94% confidence</p>
          </div>
          <div className="w-2 h-2 bg-emerald-400 rounded-full pulse-live flex-shrink-0" />
        </div>
      </div>
      
      {/* Footer */}
      <div className="px-3 sm:px-4 py-3 sm:py-4 border-t border-white/10">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[9px] sm:text-[10px] text-slate-500">IWA Compliant</p>
            <p className="text-[10px] sm:text-xs font-medium text-slate-400">v2.4.1</p>
          </div>
          <div className="text-right">
            <p className="text-[9px] sm:text-[10px] text-slate-500">Last sync</p>
            <p className="text-[10px] sm:text-xs font-medium text-emerald-400">Just now</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
