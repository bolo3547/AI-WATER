'use client'

import { useState, useEffect } from 'react'
import { 
  Bell, 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle, 
  Info,
  Volume2,
  VolumeX,
  Trash2,
  CheckCheck,
  Clock,
  Filter,
  Search,
  Settings,
  Smartphone,
  Mail,
  MessageSquare,
  Satellite,
  Bot,
  TrendingUp,
  Droplets,
  MapPin,
  CloudRain,
  Users,
  DollarSign,
  Gauge,
  BellRing,
  BellOff,
  Moon,
  Sun,
  ChevronDown,
  Download,
  Share2,
  MoreVertical,
  RefreshCw,
  Wifi,
  WifiOff,
  Zap
} from 'lucide-react'
import { clsx } from 'clsx'
import { useNotifications, NotificationType } from '@/lib/notifications'
import type { Notification } from '@/lib/notifications'

// Extended notification categories
type NotificationCategory = 
  | 'all' 
  | 'leaks' 
  | 'predictions' 
  | 'satellite' 
  | 'autonomous' 
  | 'field' 
  | 'weather' 
  | 'meters' 
  | 'finance' 
  | 'system'

interface NotificationPreferences {
  push: boolean
  sound: boolean
  email: boolean
  sms: boolean
  quietHours: { enabled: boolean; start: string; end: string }
  categories: Record<NotificationCategory, boolean>
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  return new Date(date).toLocaleDateString()
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'alert':
      return <AlertTriangle className="w-5 h-5 text-red-500" />
    case 'warning':
      return <AlertCircle className="w-5 h-5 text-amber-500" />
    case 'success':
      return <CheckCircle className="w-5 h-5 text-emerald-500" />
    case 'info':
      return <Info className="w-5 h-5 text-blue-500" />
  }
}

function getCategoryIcon(source?: string) {
  const src = (source || '').toLowerCase()
  if (src.includes('leak') || src.includes('sensor')) return <Droplets className="w-4 h-4" />
  if (src.includes('predict') || src.includes('ai')) return <TrendingUp className="w-4 h-4" />
  if (src.includes('satellite') || src.includes('drone')) return <Satellite className="w-4 h-4" />
  if (src.includes('autonomous') || src.includes('valve')) return <Bot className="w-4 h-4" />
  if (src.includes('field') || src.includes('crew')) return <Users className="w-4 h-4" />
  if (src.includes('weather') || src.includes('storm')) return <CloudRain className="w-4 h-4" />
  if (src.includes('meter') || src.includes('ami')) return <Gauge className="w-4 h-4" />
  if (src.includes('revenue') || src.includes('finance')) return <DollarSign className="w-4 h-4" />
  return <Bell className="w-4 h-4" />
}

function getNotificationBg(type: NotificationType, read: boolean) {
  if (read) return 'bg-white hover:bg-slate-50'
  
  switch (type) {
    case 'alert':
      return 'bg-red-50 hover:bg-red-100/70'
    case 'warning':
      return 'bg-amber-50 hover:bg-amber-100/70'
    case 'success':
      return 'bg-emerald-50 hover:bg-emerald-100/70'
    case 'info':
      return 'bg-blue-50 hover:bg-blue-100/70'
  }
}

// Demo notifications for showing full capabilities
const demoNotifications: Notification[] = [
  {
    id: 'demo-1',
    type: 'alert',
    priority: 'high',
    title: '🚨 Critical Leak Detected - Zone A4',
    message: 'Acoustic sensor detected high-frequency anomaly indicating probable main pipe burst. Estimated water loss: 45,000 L/hr. AI confidence: 94%.',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    read: false,
    source: 'AI Leak Detection',
    actionUrl: '/actions'
  },
  {
    id: 'demo-2',
    type: 'warning',
    priority: 'high',
    title: '⚠️ Pipe Failure Prediction - Chilenje',
    message: 'AI predicts 87% probability of pipe failure within 14 days. Cast iron pipe installed 1978, previous repair in 2019.',
    timestamp: new Date(Date.now() - 25 * 60 * 1000),
    read: false,
    source: 'Predictive AI',
    actionUrl: '/predictions'
  },
  {
    id: 'demo-3',
    type: 'info',
    priority: 'medium',
    title: '🛸 Drone Analysis Complete - Roma Township',
    message: 'Aerial thermal imaging complete. 3 potential leak signatures identified. Full report available for review.',
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    read: false,
    source: 'Satellite & Drone',
    actionUrl: '/satellite'
  },
  {
    id: 'demo-4',
    type: 'success',
    priority: 'medium',
    title: '✅ Autonomous Valve Activated',
    message: 'AI automatically closed valve V-34A to isolate burst in Zone C2. Estimated savings: 12,500 L. Manual override available.',
    timestamp: new Date(Date.now() - 1.5 * 60 * 60 * 1000),
    read: false,
    source: 'Autonomous System',
    actionUrl: '/autonomous'
  },
  {
    id: 'demo-5',
    type: 'info',
    priority: 'low',
    title: '👷 Field Crew Dispatched',
    message: 'Team Alpha (3 technicians) dispatched to Kabulonga leak site. ETA: 15 minutes. Live tracking enabled.',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    read: true,
    source: 'Field Operations',
    actionUrl: '/field'
  },
  {
    id: 'demo-6',
    type: 'warning',
    priority: 'medium',
    title: '🌧️ Storm Warning - Increased Demand',
    message: 'Heavy rainfall forecast for next 48 hours. AI predicts 23% increase in water demand. Recommend pressure zone adjustments.',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
    read: true,
    source: 'Weather Correlation',
    actionUrl: '/weather'
  },
  {
    id: 'demo-7',
    type: 'alert',
    priority: 'high',
    title: '🔋 Smart Meter Battery Critical',
    message: '47 AMI meters reporting battery below 10%. Replacement recommended within 30 days to maintain reading accuracy.',
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
    read: true,
    source: 'AMI Network',
    actionUrl: '/meters'
  },
  {
    id: 'demo-8',
    type: 'success',
    priority: 'low',
    title: '💰 Revenue Recovery Milestone',
    message: 'Monthly NRW reduction target achieved! K2.3M in water recovered this month. Current NRW rate: 34.2% (down from 42%).',
    timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
    read: true,
    source: 'Revenue Intelligence',
    actionUrl: '/finance'
  },
  {
    id: 'demo-9',
    type: 'info',
    priority: 'low',
    title: '📱 Community Report Received',
    message: 'Water leak reported via USSD (*123*LEAK#) from Matero compound. Photo evidence attached. Auto-prioritized as medium severity.',
    timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000),
    read: true,
    source: 'Community Reports',
    actionUrl: '/community'
  },
  {
    id: 'demo-10',
    type: 'success',
    priority: 'low',
    title: '🔄 System Health Check Complete',
    message: 'All 847 sensors online. AI models retrained with latest data. Prediction accuracy improved to 96.3%.',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
    read: true,
    source: 'System Health',
    actionUrl: '/health'
  }
]

export default function NotificationsPage() {
  const { 
    notifications: liveNotifications, 
    unreadCount, 
    soundEnabled, 
    sensorStatus,
    markAsRead, 
    markAllAsRead, 
    clearAll,
    toggleSound,
    playAlertSound,
    addNotification
  } = useNotifications()
  
  const [activeCategory, setActiveCategory] = useState<NotificationCategory>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const [showDemo, setShowDemo] = useState(true)
  const [pushPermission, setPushPermission] = useState<NotificationPermission>('default')
  
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    push: false,
    sound: soundEnabled,
    email: true,
    sms: false,
    quietHours: { enabled: false, start: '22:00', end: '07:00' },
    categories: {
      all: true,
      leaks: true,
      predictions: true,
      satellite: true,
      autonomous: true,
      field: true,
      weather: true,
      meters: true,
      finance: true,
      system: true
    }
  })

  // Combine live and demo notifications
  const allNotifications = showDemo 
    ? [...liveNotifications, ...demoNotifications.filter(d => !liveNotifications.some(l => l.id === d.id))]
    : liveNotifications

  // Check push notification permission
  useEffect(() => {
    if ('Notification' in window) {
      setPushPermission(Notification.permission)
    }
  }, [])

  // Request push notification permission
  const requestPushPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      setPushPermission(permission)
      if (permission === 'granted') {
        setPreferences(p => ({ ...p, push: true }))
        // Show test notification
        new Notification('🔔 LWSC Notifications Enabled', {
          body: 'You will now receive real-time alerts for leaks and system events.',
          icon: '/icon-192.png',
          badge: '/icon-192.png'
        })
      }
    }
  }

  // Filter notifications
  const filteredNotifications = allNotifications.filter(n => {
    const matchesSearch = searchQuery === '' || 
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.message.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesCategory = activeCategory === 'all' || 
      (n.source?.toLowerCase().includes(activeCategory) ?? false)
    
    return matchesSearch && matchesCategory
  })

  // Group notifications by date
  const groupedNotifications = filteredNotifications.reduce((groups, notification) => {
    const date = new Date(notification.timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    
    let group: string
    if (date.toDateString() === today.toDateString()) {
      group = 'Today'
    } else if (date.toDateString() === yesterday.toDateString()) {
      group = 'Yesterday'
    } else {
      group = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    }
    
    if (!groups[group]) groups[group] = []
    groups[group].push(notification)
    return groups
  }, {} as Record<string, Notification[]>)

  const categories: { id: NotificationCategory; label: string; icon: React.ReactNode }[] = [
    { id: 'all', label: 'All', icon: <Bell className="w-4 h-4" /> },
    { id: 'leaks', label: 'Leaks', icon: <Droplets className="w-4 h-4" /> },
    { id: 'predictions', label: 'Predictions', icon: <TrendingUp className="w-4 h-4" /> },
    { id: 'satellite', label: 'Satellite', icon: <Satellite className="w-4 h-4" /> },
    { id: 'autonomous', label: 'Autonomous', icon: <Bot className="w-4 h-4" /> },
    { id: 'field', label: 'Field', icon: <Users className="w-4 h-4" /> },
    { id: 'weather', label: 'Weather', icon: <CloudRain className="w-4 h-4" /> },
    { id: 'meters', label: 'Meters', icon: <Gauge className="w-4 h-4" /> },
    { id: 'finance', label: 'Finance', icon: <DollarSign className="w-4 h-4" /> },
    { id: 'system', label: 'System', icon: <Settings className="w-4 h-4" /> },
  ]

  const stats = {
    total: allNotifications.length,
    unread: allNotifications.filter(n => !n.read).length,
    critical: allNotifications.filter(n => n.type === 'alert' && n.priority === 'high').length,
    today: allNotifications.filter(n => new Date(n.timestamp).toDateString() === new Date().toDateString()).length
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 p-4 md:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-slate-900 flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl text-white">
                  <Bell className="w-6 h-6" />
                </div>
                Notification Center
              </h1>
              <p className="text-slate-500 mt-1">
                Manage alerts from all AI systems
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowDemo(!showDemo)}
                className={clsx(
                  "px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                  showDemo ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"
                )}
              >
                {showDemo ? 'Showing Demo' : 'Live Only'}
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5 text-slate-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Bell className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                <p className="text-xs text-slate-500">Total</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <BellRing className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.unread}</p>
                <p className="text-xs text-slate-500">Unread</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.critical}</p>
                <p className="text-xs text-slate-500">Critical</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Clock className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.today}</p>
                <p className="text-xs text-slate-500">Today</p>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-lg mb-6 p-6">
            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Notification Preferences
            </h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              {/* Delivery Methods */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Delivery Methods</h4>
                <div className="space-y-3">
                  <label className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100">
                    <div className="flex items-center gap-3">
                      <Smartphone className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Push Notifications</p>
                        <p className="text-xs text-slate-500">Receive alerts in browser/device</p>
                      </div>
                    </div>
                    {pushPermission === 'granted' ? (
                      <input 
                        type="checkbox" 
                        checked={preferences.push}
                        onChange={(e) => setPreferences(p => ({ ...p, push: e.target.checked }))}
                        className="w-5 h-5 rounded text-blue-600"
                      />
                    ) : (
                      <button
                        onClick={requestPushPermission}
                        className="px-3 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                      >
                        Enable
                      </button>
                    )}
                  </label>
                  
                  <label className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100">
                    <div className="flex items-center gap-3">
                      <Volume2 className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Sound Alerts</p>
                        <p className="text-xs text-slate-500">Audio tones for new alerts</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => playAlertSound('alert')}
                        className="px-2 py-1 text-xs bg-slate-200 rounded hover:bg-slate-300"
                      >
                        Test
                      </button>
                      <input 
                        type="checkbox" 
                        checked={soundEnabled}
                        onChange={toggleSound}
                        className="w-5 h-5 rounded text-blue-600"
                      />
                    </div>
                  </label>
                  
                  <label className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100">
                    <div className="flex items-center gap-3">
                      <Mail className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Email Notifications</p>
                        <p className="text-xs text-slate-500">Critical alerts via email</p>
                      </div>
                    </div>
                    <input 
                      type="checkbox" 
                      checked={preferences.email}
                      onChange={(e) => setPreferences(p => ({ ...p, email: e.target.checked }))}
                      className="w-5 h-5 rounded text-blue-600"
                    />
                  </label>
                  
                  <label className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100">
                    <div className="flex items-center gap-3">
                      <MessageSquare className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">SMS Alerts</p>
                        <p className="text-xs text-slate-500">Critical alerts via SMS</p>
                      </div>
                    </div>
                    <input 
                      type="checkbox" 
                      checked={preferences.sms}
                      onChange={(e) => setPreferences(p => ({ ...p, sms: e.target.checked }))}
                      className="w-5 h-5 rounded text-blue-600"
                    />
                  </label>
                </div>
              </div>
              
              {/* Quiet Hours */}
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-3">Quiet Hours</h4>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <label className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Moon className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-700">Enable Quiet Hours</p>
                        <p className="text-xs text-slate-500">Silence non-critical alerts</p>
                      </div>
                    </div>
                    <input 
                      type="checkbox" 
                      checked={preferences.quietHours.enabled}
                      onChange={(e) => setPreferences(p => ({ 
                        ...p, 
                        quietHours: { ...p.quietHours, enabled: e.target.checked }
                      }))}
                      className="w-5 h-5 rounded text-blue-600"
                    />
                  </label>
                  
                  {preferences.quietHours.enabled && (
                    <div className="flex items-center gap-4 mt-3">
                      <div>
                        <label className="text-xs text-slate-500">From</label>
                        <input 
                          type="time"
                          value={preferences.quietHours.start}
                          onChange={(e) => setPreferences(p => ({ 
                            ...p, 
                            quietHours: { ...p.quietHours, start: e.target.value }
                          }))}
                          className="block mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">To</label>
                        <input 
                          type="time"
                          value={preferences.quietHours.end}
                          onChange={(e) => setPreferences(p => ({ 
                            ...p, 
                            quietHours: { ...p.quietHours, end: e.target.value }
                          }))}
                          className="block mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
                        />
                      </div>
                    </div>
                  )}
                </div>
                
                <p className="text-xs text-amber-600 mt-3 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Critical leak alerts will always come through
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Connection Status */}
        <div className={clsx(
          "mb-6 p-4 rounded-xl border flex items-center gap-3",
          sensorStatus.connected 
            ? "bg-emerald-50 border-emerald-200" 
            : "bg-amber-50 border-amber-200"
        )}>
          {sensorStatus.connected ? (
            <>
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Wifi className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-emerald-800">
                  {sensorStatus.count} Sensor{sensorStatus.count !== 1 ? 's' : ''} Connected
                </p>
                <p className="text-xs text-emerald-600">Real-time alerts active</p>
              </div>
              <div className="ml-auto flex items-center gap-1">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                <span className="text-xs text-emerald-600">Live</span>
              </div>
            </>
          ) : (
            <>
              <div className="p-2 bg-amber-100 rounded-lg">
                <WifiOff className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-amber-800">No Sensors Connected</p>
                <p className="text-xs text-amber-600">Showing demo notifications</p>
              </div>
              <button className="ml-auto px-3 py-1.5 text-xs font-medium bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200">
                Connect Sensors
              </button>
            </>
          )}
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Categories Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 sticky top-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Categories</h3>
              <div className="space-y-1">
                {categories.map((cat) => {
                  const count = cat.id === 'all' 
                    ? allNotifications.length 
                    : allNotifications.filter(n => n.source?.toLowerCase().includes(cat.id)).length
                  
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setActiveCategory(cat.id)}
                      className={clsx(
                        "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors",
                        activeCategory === cat.id 
                          ? "bg-blue-50 text-blue-700 font-medium" 
                          : "text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {cat.icon}
                        {cat.label}
                      </div>
                      {count > 0 && (
                        <span className={clsx(
                          "px-2 py-0.5 text-xs rounded-full",
                          activeCategory === cat.id 
                            ? "bg-blue-100 text-blue-700" 
                            : "bg-slate-100 text-slate-500"
                        )}>
                          {count}
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Notifications List */}
          <div className="lg:col-span-3">
            {/* Search and Actions */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm mb-4 p-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search notifications..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  {stats.unread > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      <CheckCheck className="w-4 h-4" />
                      Mark all read
                    </button>
                  )}
                  <button
                    onClick={clearAll}
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear all
                  </button>
                </div>
              </div>
            </div>

            {/* Grouped Notifications */}
            {Object.keys(groupedNotifications).length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center">
                <BellOff className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-700">No notifications</h3>
                <p className="text-slate-500 mt-1">
                  {searchQuery ? 'No notifications match your search' : "You're all caught up!"}
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(groupedNotifications).map(([group, notifications]) => (
                  <div key={group}>
                    <h3 className="text-sm font-semibold text-slate-500 mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      {group}
                    </h3>
                    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
                      {notifications.map((notification) => (
                        <div 
                          key={notification.id}
                          onClick={() => markAsRead(notification.id)}
                          className={clsx(
                            "p-4 cursor-pointer transition-colors",
                            getNotificationBg(notification.type, notification.read)
                          )}
                        >
                          <div className="flex gap-4">
                            <div className="flex-shrink-0 mt-1">
                              {getNotificationIcon(notification.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-3">
                                <h4 className={clsx(
                                  "text-sm font-semibold",
                                  notification.read ? "text-slate-700" : "text-slate-900"
                                )}>
                                  {notification.title}
                                </h4>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  {!notification.read && (
                                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                                  )}
                                  <span className={clsx(
                                    "px-2 py-0.5 text-xs font-medium rounded-full",
                                    notification.priority === 'high' && "bg-red-100 text-red-700",
                                    notification.priority === 'medium' && "bg-amber-100 text-amber-700",
                                    notification.priority === 'low' && "bg-slate-100 text-slate-600"
                                  )}>
                                    {notification.priority}
                                  </span>
                                </div>
                              </div>
                              <p className="text-sm text-slate-600 mt-1">
                                {notification.message}
                              </p>
                              <div className="flex items-center flex-wrap gap-3 mt-3">
                                <span className="text-xs text-slate-400 flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {formatDate(notification.timestamp)}
                                </span>
                                {notification.source && (
                                  <span className="text-xs text-slate-500 flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded-full">
                                    {getCategoryIcon(notification.source)}
                                    {notification.source}
                                  </span>
                                )}
                                {notification.actionUrl && (
                                  <a 
                                    href={notification.actionUrl}
                                    onClick={(e) => e.stopPropagation()}
                                    className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
                                  >
                                    <Zap className="w-3 h-3" />
                                    Take Action →
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
