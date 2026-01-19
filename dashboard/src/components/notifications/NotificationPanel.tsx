'use client'

import { useState } from 'react'
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
  Clock
} from 'lucide-react'
import { clsx } from 'clsx'
import { useNotifications, NotificationType } from '@/lib/notifications'

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
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

function getNotificationBg(type: NotificationType, read: boolean) {
  if (read) return 'bg-white'
  
  switch (type) {
    case 'alert':
      return 'bg-red-50'
    case 'warning':
      return 'bg-amber-50'
    case 'success':
      return 'bg-emerald-50'
    case 'info':
      return 'bg-blue-50'
  }
}

export function NotificationPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const { 
    notifications, 
    unreadCount, 
    soundEnabled, 
    sensorStatus,
    markAsRead, 
    markAllAsRead, 
    clearAll,
    toggleSound,
    playAlertSound
  } = useNotifications()

  const handleTestSound = () => {
    playAlertSound('alert')
  }

  return (
    <div className="relative">
      {/* Bell Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-slate-100 rounded-xl transition-colors"
      >
        <Bell className={clsx(
          "w-5 h-5",
          unreadCount > 0 ? "text-slate-700" : "text-slate-500"
        )} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full ring-2 ring-white px-1">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
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
          <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 z-50 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-slate-900">Notifications</h3>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
              
              {/* Controls */}
              <div className="flex items-center gap-2">
                <button
                  onClick={toggleSound}
                  className={clsx(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors",
                    soundEnabled 
                      ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200" 
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
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
                  Test Sound
                </button>
                
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-lg transition-colors ml-auto"
                  >
                    <CheckCheck className="w-3.5 h-3.5" />
                    Mark all read
                  </button>
                )}
              </div>
            </div>
            
            {/* Notifications List */}
            <div className="max-h-[400px] overflow-y-auto">
              {/* Sensor Status Banner */}
              {!sensorStatus.connected && (
                <div className="p-4 bg-amber-50 border-b border-amber-100">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                      <AlertCircle className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-amber-800">No Sensors Connected</p>
                      <p className="text-xs text-amber-600">Connect sensors to receive real-time alerts</p>
                    </div>
                  </div>
                </div>
              )}
              
              {sensorStatus.connected && (
                <div className="p-3 bg-emerald-50 border-b border-emerald-100">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-xs font-medium text-emerald-700">
                      {sensorStatus.count} sensor{sensorStatus.count !== 1 ? 's' : ''} connected
                    </span>
                  </div>
                </div>
              )}
              
              {notifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 font-medium">No notifications</p>
                  <p className="text-sm text-slate-400">
                    {sensorStatus.connected 
                      ? "You're all caught up!" 
                      : "Connect sensors to receive alerts"}
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {notifications.map((notification) => (
                    <div 
                      key={notification.id}
                      onClick={() => markAsRead(notification.id)}
                      className={clsx(
                        "p-4 hover:bg-slate-50 transition-colors cursor-pointer",
                        getNotificationBg(notification.type, notification.read)
                      )}
                    >
                      <div className="flex gap-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className={clsx(
                              "text-sm font-semibold truncate",
                              notification.read ? "text-slate-700" : "text-slate-900"
                            )}>
                              {notification.title}
                            </p>
                            {!notification.read && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-[10px] text-slate-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatTimeAgo(notification.timestamp)}
                            </span>
                            {notification.source && (
                              <span className="text-[10px] text-slate-400">
                                {notification.source}
                              </span>
                            )}
                            {notification.actionUrl && (
                              <Link 
                                href={notification.actionUrl}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  setIsOpen(false)
                                }}
                                className="text-[10px] font-medium text-blue-600 hover:text-blue-700"
                              >
                                View Details →
                              </Link>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Footer */}
            {notifications.length > 0 && (
              <div className="p-3 border-t border-slate-100 bg-slate-50">
                <div className="flex items-center justify-between">
                  <Link 
                    href="/actions"
                    onClick={() => setIsOpen(false)}
                    className="text-xs font-medium text-blue-600 hover:text-blue-700"
                  >
                    View all alerts
                  </Link>
                  <button
                    onClick={clearAll}
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
