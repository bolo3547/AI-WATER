'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { 
  Bell, 
  X, 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle, 
  Info,
  Volume2,
  VolumeX,
  Trash2,
  CheckCheck,
  Clock,
  RefreshCw,
  Wifi,
  WifiOff,
  ChevronRight,
  Shield,
  Zap,
  Loader2
} from 'lucide-react'
import { clsx } from 'clsx'
import { useNotificationsApi, ApiNotification, NotificationSeverity } from '@/hooks/useNotificationsApi'

// =============================================================================
// TYPES
// =============================================================================

interface NotificationBellProps {
  /** Custom class name for the bell button */
  className?: string
  /** Position of the dropdown panel */
  position?: 'left' | 'right'
  /** Max height of the notification list */
  maxHeight?: string
  /** Enable sound notifications */
  enableSound?: boolean
  /** Show escalation indicators */
  showEscalations?: boolean
}

// =============================================================================
// HELPERS
// =============================================================================

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function getSeverityIcon(severity: NotificationSeverity) {
  switch (severity) {
    case 'critical':
      return <AlertTriangle className="w-5 h-5 text-red-500" />
    case 'warning':
      return <AlertCircle className="w-5 h-5 text-amber-500" />
    case 'success':
      return <CheckCircle className="w-5 h-5 text-emerald-500" />
    case 'info':
    default:
      return <Info className="w-5 h-5 text-blue-500" />
  }
}

function getSeverityBg(severity: NotificationSeverity, read: boolean): string {
  if (read) return 'bg-white hover:bg-slate-50'
  
  switch (severity) {
    case 'critical':
      return 'bg-red-50 hover:bg-red-100'
    case 'warning':
      return 'bg-amber-50 hover:bg-amber-100'
    case 'success':
      return 'bg-emerald-50 hover:bg-emerald-100'
    case 'info':
    default:
      return 'bg-blue-50 hover:bg-blue-100'
  }
}

function getSeverityBorder(severity: NotificationSeverity, read: boolean): string {
  if (read) return 'border-l-transparent'
  
  switch (severity) {
    case 'critical':
      return 'border-l-red-500'
    case 'warning':
      return 'border-l-amber-500'
    case 'success':
      return 'border-l-emerald-500'
    case 'info':
    default:
      return 'border-l-blue-500'
  }
}

// Audio context for sound notifications
let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  
  if (!audioContext) {
    try {
      audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    } catch {
      return null
    }
  }
  return audioContext
}

function playNotificationSound(severity: NotificationSeverity): void {
  const ctx = getAudioContext()
  if (!ctx) return
  
  if (ctx.state === 'suspended') {
    ctx.resume()
  }
  
  const frequencies: Record<NotificationSeverity, number> = {
    critical: 880,
    warning: 660,
    success: 523,
    info: 440,
  }
  
  const oscillator = ctx.createOscillator()
  const gainNode = ctx.createGain()
  
  oscillator.connect(gainNode)
  gainNode.connect(ctx.destination)
  
  oscillator.frequency.value = frequencies[severity]
  oscillator.type = 'sine'
  
  gainNode.gain.setValueAtTime(0, ctx.currentTime)
  gainNode.gain.linearRampToValueAtTime(0.3, ctx.currentTime + 0.01)
  gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.2)
  
  oscillator.start(ctx.currentTime)
  oscillator.stop(ctx.currentTime + 0.2)
}

// =============================================================================
// NOTIFICATION ITEM COMPONENT
// =============================================================================

interface NotificationItemProps {
  notification: ApiNotification
  onRead: () => void
  onClose: () => void
}

function NotificationItem({ notification, onRead, onClose }: NotificationItemProps) {
  const handleClick = () => {
    if (!notification.read) {
      onRead()
    }
  }
  
  return (
    <div
      onClick={handleClick}
      className={clsx(
        'p-4 transition-colors cursor-pointer border-l-4',
        getSeverityBg(notification.severity, notification.read),
        getSeverityBorder(notification.severity, notification.read)
      )}
    >
      <div className="flex gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getSeverityIcon(notification.severity)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={clsx(
              'text-sm font-semibold truncate',
              notification.read ? 'text-slate-600' : 'text-slate-900'
            )}>
              {notification.title}
            </p>
            {!notification.read && (
              <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5 animate-pulse" />
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1 line-clamp-2">
            {notification.message}
          </p>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatTimeAgo(notification.created_at)}
            </span>
            {notification.severity === 'critical' && (
              <span className="text-[10px] font-medium text-red-600 flex items-center gap-1">
                <Zap className="w-3 h-3" />
                Critical
              </span>
            )}
            {notification.action_url && (
              <Link 
                href={notification.action_url}
                onClick={(e) => {
                  e.stopPropagation()
                  onClose()
                }}
                className="text-[10px] font-medium text-blue-600 hover:text-blue-700 flex items-center"
              >
                View Details
                <ChevronRight className="w-3 h-3" />
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function NotificationBell({
  className,
  position = 'right',
  maxHeight = '400px',
  enableSound = true,
  showEscalations = true,
}: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(enableSound)
  const [prevUnreadCount, setPrevUnreadCount] = useState(0)
  
  const {
    notifications,
    unreadCount,
    loading,
    error,
    hasMore,
    realtimeConnected,
    markAsRead,
    markAllAsRead,
    loadMore,
    refreshNotifications,
    escalations,
    fetchEscalations,
    acknowledgeEscalation,
  } = useNotificationsApi({
    autoFetch: true,
    enableRealtime: true,
  })
  
  // Load sound preference from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('notification_sound_v2')
      if (saved !== null) {
        setSoundEnabled(saved === 'true')
      }
    }
  }, [])
  
  // Play sound when new notification arrives
  useEffect(() => {
    if (soundEnabled && unreadCount > prevUnreadCount && prevUnreadCount > 0) {
      // Find the newest unread notification for severity
      const newestUnread = notifications.find(n => !n.read)
      if (newestUnread) {
        playNotificationSound(newestUnread.severity)
      }
    }
    setPrevUnreadCount(unreadCount)
  }, [unreadCount, prevUnreadCount, soundEnabled, notifications])
  
  // Fetch escalations when panel opens
  useEffect(() => {
    if (isOpen && showEscalations) {
      fetchEscalations()
    }
  }, [isOpen, showEscalations, fetchEscalations])
  
  const toggleSound = useCallback(() => {
    setSoundEnabled(prev => {
      const newValue = !prev
      if (typeof window !== 'undefined') {
        localStorage.setItem('notification_sound_v2', String(newValue))
      }
      return newValue
    })
  }, [])
  
  const handleTestSound = () => {
    playNotificationSound('critical')
  }
  
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await markAsRead(notificationId)
    } catch (err) {
      console.error('Failed to mark as read:', err)
    }
  }
  
  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead()
    } catch (err) {
      console.error('Failed to mark all as read:', err)
    }
  }
  
  // Active escalations that haven't been acknowledged
  const activeEscalations = escalations.filter(e => !e.acknowledged && !e.resolved)
  
  return (
    <div className="relative">
      {/* Bell Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'relative p-2 hover:bg-slate-100 rounded-xl transition-colors',
          isOpen && 'bg-slate-100',
          className
        )}
        aria-label="Notifications"
      >
        <Bell className={clsx(
          'w-5 h-5 transition-colors',
          unreadCount > 0 ? 'text-slate-700' : 'text-slate-500'
        )} />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full ring-2 ring-white px-1 animate-in zoom-in-50">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        
        {/* Escalation Indicator */}
        {activeEscalations.length > 0 && (
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-amber-500 rounded-full ring-2 ring-white animate-pulse" />
        )}
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Panel */}
          <div 
            className={clsx(
              'absolute top-full mt-2 w-[calc(100vw-2rem)] sm:w-[400px] bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden',
              position === 'right' ? 'right-0' : 'left-0'
            )}
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900">Notifications</h3>
                  {realtimeConnected ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-emerald-700 bg-emerald-100 rounded-full">
                      <Wifi className="w-3 h-3" />
                      Live
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-slate-500 bg-slate-100 rounded-full">
                      <WifiOff className="w-3 h-3" />
                      Offline
                    </span>
                  )}
                </div>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
              
              {/* Controls */}
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={toggleSound}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                    soundEnabled 
                      ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' 
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  )}
                >
                  {soundEnabled ? (
                    <>
                      <Volume2 className="w-3.5 h-3.5" />
                      Sound On
                    </>
                  ) : (
                    <>
                      <VolumeX className="w-3.5 h-3.5" />
                      Sound Off
                    </>
                  )}
                </button>
                
                <button
                  onClick={handleTestSound}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg transition-colors"
                >
                  <Bell className="w-3.5 h-3.5" />
                  Test
                </button>
                
                <button
                  onClick={() => refreshNotifications()}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={clsx('w-3.5 h-3.5', loading && 'animate-spin')} />
                  Refresh
                </button>
                
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllAsRead}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg transition-colors ml-auto"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Mark all read
                  </button>
                )}
              </div>
            </div>
            
            {/* Escalation Alert Banner */}
            {activeEscalations.length > 0 && (
              <div className="p-3 bg-amber-50 border-b border-amber-200">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-semibold text-amber-800">
                    {activeEscalations.length} alert{activeEscalations.length !== 1 ? 's' : ''} require{activeEscalations.length === 1 ? 's' : ''} attention
                  </span>
                  <button
                    onClick={() => {
                      activeEscalations.forEach(e => acknowledgeEscalation(e.id))
                    }}
                    className="ml-auto text-xs font-medium text-amber-700 hover:text-amber-900"
                  >
                    Acknowledge All
                  </button>
                </div>
              </div>
            )}
            
            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-50 border-b border-red-200">
                <p className="text-xs text-red-700">{error.message}</p>
              </div>
            )}
            
            {/* Notifications List */}
            <div 
              className="overflow-y-auto divide-y divide-slate-100"
              style={{ maxHeight }}
            >
              {loading && notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-8 h-8 text-slate-300 mx-auto mb-3 animate-spin" />
                  <p className="text-sm text-slate-500">Loading notifications...</p>
                </div>
              ) : notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No notifications</p>
                  <p className="text-sm text-slate-400 mt-1">You&apos;re all caught up!</p>
                </div>
              ) : (
                <>
                  {notifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onRead={() => handleMarkAsRead(notification.id)}
                      onClose={() => setIsOpen(false)}
                    />
                  ))}
                  
                  {/* Load More Button */}
                  {hasMore && (
                    <div className="p-3 text-center">
                      <button
                        onClick={() => loadMore()}
                        disabled={loading}
                        className="text-xs font-medium text-blue-600 hover:text-blue-700 disabled:opacity-50"
                      >
                        {loading ? 'Loading...' : 'Load more notifications'}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
            
            {/* Footer */}
            {notifications.length > 0 && (
              <div className="p-3 border-t border-slate-100 bg-slate-50">
                <div className="flex items-center justify-between">
                  <Link 
                    href="/notifications"
                    onClick={() => setIsOpen(false)}
                    className="text-xs font-medium text-blue-600 hover:text-blue-700"
                  >
                    View all notifications
                  </Link>
                  <button
                    onClick={() => {
                      // Clear is typically for local-only state
                      // For API-backed notifications, we just mark all as read
                      handleMarkAllAsRead()
                    }}
                    className="flex items-center gap-1 text-xs text-slate-500 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    Clear all
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default NotificationBell
