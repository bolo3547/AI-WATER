'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  Bell, 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle, 
  Info,
  Clock,
  Filter,
  Search,
  ChevronRight,
  ChevronDown,
  Shield,
  Zap,
  CheckCheck,
  RefreshCw,
  Settings,
  Trash2,
  Loader2,
  X
} from 'lucide-react'
import { clsx } from 'clsx'
import { 
  useNotificationsApi, 
  ApiNotification, 
  NotificationSeverity,
  NotificationRule,
  EscalationTracker
} from '@/hooks/useNotificationsApi'

// =============================================================================
// TYPES
// =============================================================================

type TabType = 'all' | 'unread' | 'escalations' | 'rules'
type SeverityFilter = 'all' | NotificationSeverity

// =============================================================================
// HELPERS
// =============================================================================

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  return new Date(dateStr).toLocaleDateString()
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

function getSeverityIcon(severity: NotificationSeverity, size = 'w-5 h-5') {
  switch (severity) {
    case 'critical':
      return <AlertTriangle className={`${size} text-red-500`} />
    case 'warning':
      return <AlertCircle className={`${size} text-amber-500`} />
    case 'success':
      return <CheckCircle className={`${size} text-emerald-500`} />
    case 'info':
    default:
      return <Info className={`${size} text-blue-500`} />
  }
}

function getSeverityBadge(severity: NotificationSeverity) {
  const colors: Record<NotificationSeverity, string> = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    warning: 'bg-amber-100 text-amber-800 border-amber-200',
    success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
  }
  
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
      colors[severity]
    )}>
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  )
}

// =============================================================================
// TAB BUTTON COMPONENT
// =============================================================================

interface TabButtonProps {
  active: boolean
  onClick: () => void
  children: React.ReactNode
  count?: number
}

function TabButton({ active, onClick, children, count }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'px-4 py-2 text-sm font-medium rounded-lg transition-colors flex items-center gap-2',
        active
          ? 'bg-blue-100 text-blue-700'
          : 'text-slate-600 hover:bg-slate-100'
      )}
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className={clsx(
          'min-w-[20px] h-5 flex items-center justify-center rounded-full text-xs font-bold',
          active ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
        )}>
          {count > 99 ? '99+' : count}
        </span>
      )}
    </button>
  )
}

// =============================================================================
// NOTIFICATION CARD COMPONENT
// =============================================================================

interface NotificationCardProps {
  notification: ApiNotification
  onMarkRead: () => void
  expanded?: boolean
  onToggleExpand: () => void
}

function NotificationCard({ 
  notification, 
  onMarkRead, 
  expanded,
  onToggleExpand 
}: NotificationCardProps) {
  return (
    <div
      className={clsx(
        'border rounded-xl transition-all',
        notification.read 
          ? 'bg-white border-slate-200' 
          : 'bg-blue-50/50 border-blue-200 shadow-sm'
      )}
    >
      <div 
        className="p-4 cursor-pointer"
        onClick={onToggleExpand}
      >
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={clsx(
            'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
            notification.severity === 'critical' && 'bg-red-100',
            notification.severity === 'warning' && 'bg-amber-100',
            notification.severity === 'success' && 'bg-emerald-100',
            notification.severity === 'info' && 'bg-blue-100'
          )}>
            {getSeverityIcon(notification.severity)}
          </div>
          
          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h4 className={clsx(
                  'font-semibold',
                  notification.read ? 'text-slate-700' : 'text-slate-900'
                )}>
                  {notification.title}
                </h4>
                <p className={clsx(
                  'text-sm mt-1',
                  expanded ? '' : 'line-clamp-2',
                  notification.read ? 'text-slate-500' : 'text-slate-600'
                )}>
                  {notification.message}
                </p>
              </div>
              
              <div className="flex items-center gap-2 flex-shrink-0">
                {!notification.read && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                )}
                <ChevronDown className={clsx(
                  'w-4 h-4 text-slate-400 transition-transform',
                  expanded && 'rotate-180'
                )} />
              </div>
            </div>
            
            {/* Meta info */}
            <div className="flex items-center gap-4 mt-3">
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {formatTimeAgo(notification.created_at)}
              </span>
              
              {getSeverityBadge(notification.severity)}
              
              <span className="text-xs text-slate-400 capitalize">
                {notification.channel.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-slate-100 mt-2">
          <div className="pl-14 space-y-3">
            {/* Full message */}
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Full Message</p>
              <p className="text-sm text-slate-700">{notification.message}</p>
            </div>
            
            {/* Metadata */}
            {notification.metadata && Object.keys(notification.metadata).length > 0 && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Details</p>
                <div className="bg-slate-50 rounded-lg p-2 text-xs font-mono text-slate-600 overflow-auto max-h-32">
                  {JSON.stringify(notification.metadata, null, 2)}
                </div>
              </div>
            )}
            
            {/* Timestamps */}
            <div className="flex items-center gap-6 text-xs text-slate-500">
              <span>Created: {formatDateTime(notification.created_at)}</span>
              {notification.read_at && (
                <span>Read: {formatDateTime(notification.read_at)}</span>
              )}
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-2 pt-2">
              {!notification.read && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onMarkRead()
                  }}
                  className="px-3 py-1.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors flex items-center gap-1"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  Mark as Read
                </button>
              )}
              
              {notification.action_url && (
                <Link
                  href={notification.action_url}
                  className="px-3 py-1.5 text-xs font-medium bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-1"
                >
                  View Details
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// ESCALATION CARD COMPONENT
// =============================================================================

interface EscalationCardProps {
  escalation: EscalationTracker
  onAcknowledge: () => void
  onResolve: () => void
}

function EscalationCard({ escalation, onAcknowledge, onResolve }: EscalationCardProps) {
  const isUrgent = !escalation.acknowledged && 
    escalation.next_escalation_at && 
    new Date(escalation.next_escalation_at) < new Date(Date.now() + 5 * 60 * 1000)
  
  return (
    <div className={clsx(
      'border rounded-xl p-4 transition-all',
      escalation.resolved 
        ? 'bg-slate-50 border-slate-200'
        : escalation.acknowledged
          ? 'bg-amber-50 border-amber-200'
          : 'bg-red-50 border-red-200'
    )}>
      <div className="flex items-start gap-4">
        <div className={clsx(
          'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
          escalation.resolved 
            ? 'bg-slate-200' 
            : escalation.acknowledged 
              ? 'bg-amber-200' 
              : 'bg-red-200'
        )}>
          <Shield className={clsx(
            'w-5 h-5',
            escalation.resolved 
              ? 'text-slate-600' 
              : escalation.acknowledged 
                ? 'text-amber-600' 
                : 'text-red-600'
          )} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-slate-900">
              Alert Escalation
            </h4>
            {isUrgent && !escalation.resolved && (
              <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-red-700 bg-red-100 rounded-full animate-pulse">
                <Zap className="w-3 h-3" />
                Urgent
              </span>
            )}
          </div>
          
          <p className="text-sm text-slate-600 mt-1">
            Alert ID: {escalation.alert_id}
          </p>
          
          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
            <span>Level: {escalation.current_level} / {escalation.max_level}</span>
            <span>Created: {formatTimeAgo(escalation.created_at)}</span>
            {escalation.next_escalation_at && !escalation.resolved && !escalation.acknowledged && (
              <span className="text-red-600 font-medium">
                Next escalation: {formatTimeAgo(escalation.next_escalation_at)}
              </span>
            )}
          </div>
          
          {/* Status badges */}
          <div className="flex items-center gap-2 mt-3">
            {escalation.resolved ? (
              <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">
                <CheckCircle className="w-3.5 h-3.5" />
                Resolved
              </span>
            ) : escalation.acknowledged ? (
              <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
                <CheckCheck className="w-3.5 h-3.5" />
                Acknowledged
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full animate-pulse">
                <AlertTriangle className="w-3.5 h-3.5" />
                Requires Attention
              </span>
            )}
          </div>
          
          {/* Actions */}
          {!escalation.resolved && (
            <div className="flex items-center gap-2 mt-3">
              {!escalation.acknowledged && (
                <button
                  onClick={onAcknowledge}
                  className="px-3 py-1.5 text-xs font-medium bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                  Acknowledge
                </button>
              )}
              <button
                onClick={onResolve}
                className="px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
              >
                Resolve
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// RULE CARD COMPONENT
// =============================================================================

interface RuleCardProps {
  rule: NotificationRule
  onDelete: () => void
}

function RuleCard({ rule, onDelete }: RuleCardProps) {
  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-white">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-slate-900">{rule.name}</h4>
            {!rule.active && (
              <span className="px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-500 rounded-full">
                Disabled
              </span>
            )}
          </div>
          
          {rule.description && (
            <p className="text-sm text-slate-600 mt-1">{rule.description}</p>
          )}
          
          <div className="flex flex-wrap items-center gap-2 mt-3">
            {getSeverityBadge(rule.severity)}
            
            <span className="text-xs text-slate-500">
              Event: {rule.event_type}
            </span>
            
            <span className="text-xs text-slate-500">
              Roles: {rule.target_roles.join(', ')}
            </span>
            
            <span className="text-xs text-slate-500">
              Channels: {rule.channels.join(', ')}
            </span>
          </div>
          
          {rule.escalation?.enabled && (
            <div className="mt-2 text-xs text-amber-600 flex items-center gap-1">
              <Shield className="w-3.5 h-3.5" />
              Escalation enabled ({rule.escalation.levels.length} levels)
            </div>
          )}
        </div>
        
        <button
          onClick={onDelete}
          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function NotificationDrawer() {
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  
  const {
    notifications,
    unreadCount,
    loading,
    error,
    hasMore,
    total,
    markAsRead,
    markAllAsRead,
    loadMore,
    refreshNotifications,
    rules,
    fetchRules,
    deleteRule,
    escalations,
    fetchEscalations,
    acknowledgeEscalation,
    resolveEscalation,
    realtimeConnected,
  } = useNotificationsApi({
    autoFetch: true,
    enableRealtime: true,
    pageSize: 20,
  })
  
  // Fetch rules and escalations on tab change
  useEffect(() => {
    if (activeTab === 'rules') {
      fetchRules()
    } else if (activeTab === 'escalations') {
      fetchEscalations()
    }
  }, [activeTab, fetchRules, fetchEscalations])
  
  // Filter notifications
  const filteredNotifications = notifications.filter(n => {
    // Tab filter
    if (activeTab === 'unread' && n.read) return false
    
    // Severity filter
    if (severityFilter !== 'all' && n.severity !== severityFilter) return false
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        n.title.toLowerCase().includes(query) ||
        n.message.toLowerCase().includes(query)
      )
    }
    
    return true
  })
  
  // Active escalations count
  const activeEscalationsCount = escalations.filter(e => !e.resolved && !e.acknowledged).length
  
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
                <Bell className="w-7 h-7 text-blue-600" />
                Notifications
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                {total} total • {unreadCount} unread
                {realtimeConnected && (
                  <span className="ml-2 text-emerald-600">• Live updates enabled</span>
                )}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => refreshNotifications()}
                disabled={loading}
                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
              >
                <RefreshCw className={clsx('w-5 h-5', loading && 'animate-spin')} />
              </button>
              
              <Link
                href="/settings/notifications"
                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5" />
              </Link>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="flex items-center gap-2 mt-6 overflow-x-auto pb-2">
            <TabButton 
              active={activeTab === 'all'} 
              onClick={() => setActiveTab('all')}
              count={total}
            >
              All
            </TabButton>
            <TabButton 
              active={activeTab === 'unread'} 
              onClick={() => setActiveTab('unread')}
              count={unreadCount}
            >
              Unread
            </TabButton>
            <TabButton 
              active={activeTab === 'escalations'} 
              onClick={() => setActiveTab('escalations')}
              count={activeEscalationsCount}
            >
              <Shield className="w-4 h-4" />
              Escalations
            </TabButton>
            <TabButton 
              active={activeTab === 'rules'} 
              onClick={() => setActiveTab('rules')}
              count={rules.length}
            >
              <Settings className="w-4 h-4" />
              Rules
            </TabButton>
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Notifications Tab */}
        {(activeTab === 'all' || activeTab === 'unread') && (
          <>
            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search notifications..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2"
                  >
                    <X className="w-4 h-4 text-slate-400 hover:text-slate-600" />
                  </button>
                )}
              </div>
              
              {/* Filter toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  'p-2 rounded-lg transition-colors flex items-center gap-2',
                  showFilters 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'text-slate-500 hover:bg-slate-100'
                )}
              >
                <Filter className="w-4 h-4" />
              </button>
              
              {/* Mark all as read */}
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllAsRead()}
                  className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-2"
                >
                  <CheckCheck className="w-4 h-4" />
                  Mark all as read
                </button>
              )}
            </div>
            
            {/* Filter options */}
            {showFilters && (
              <div className="mb-6 p-4 bg-white border border-slate-200 rounded-xl">
                <p className="text-sm font-medium text-slate-700 mb-3">Filter by severity</p>
                <div className="flex flex-wrap gap-2">
                  {(['all', 'critical', 'warning', 'info', 'success'] as const).map((severity) => (
                    <button
                      key={severity}
                      onClick={() => setSeverityFilter(severity)}
                      className={clsx(
                        'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors capitalize',
                        severityFilter === severity
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      )}
                    >
                      {severity}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Error state */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
                <p className="text-sm text-red-700">{error.message}</p>
              </div>
            )}
            
            {/* Notifications list */}
            <div className="space-y-3">
              {loading && filteredNotifications.length === 0 ? (
                <div className="text-center py-12">
                  <Loader2 className="w-8 h-8 text-slate-300 mx-auto animate-spin" />
                  <p className="text-sm text-slate-500 mt-3">Loading notifications...</p>
                </div>
              ) : filteredNotifications.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
                  <Bell className="w-12 h-12 text-slate-300 mx-auto" />
                  <p className="text-slate-600 font-medium mt-3">No notifications</p>
                  <p className="text-sm text-slate-400 mt-1">
                    {activeTab === 'unread' 
                      ? "You're all caught up!" 
                      : "No notifications match your filters"}
                  </p>
                </div>
              ) : (
                <>
                  {filteredNotifications.map((notification) => (
                    <NotificationCard
                      key={notification.id}
                      notification={notification}
                      onMarkRead={() => markAsRead(notification.id)}
                      expanded={expandedId === notification.id}
                      onToggleExpand={() => setExpandedId(
                        expandedId === notification.id ? null : notification.id
                      )}
                    />
                  ))}
                  
                  {/* Load more */}
                  {hasMore && (
                    <div className="text-center py-4">
                      <button
                        onClick={() => loadMore()}
                        disabled={loading}
                        className="px-6 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Loading...' : 'Load more'}
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </>
        )}
        
        {/* Escalations Tab */}
        {activeTab === 'escalations' && (
          <div className="space-y-4">
            {escalations.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
                <Shield className="w-12 h-12 text-slate-300 mx-auto" />
                <p className="text-slate-600 font-medium mt-3">No escalations</p>
                <p className="text-sm text-slate-400 mt-1">
                  All alerts are under control
                </p>
              </div>
            ) : (
              escalations.map((escalation) => (
                <EscalationCard
                  key={escalation.id}
                  escalation={escalation}
                  onAcknowledge={() => acknowledgeEscalation(escalation.id)}
                  onResolve={() => resolveEscalation(escalation.id)}
                />
              ))
            )}
          </div>
        )}
        
        {/* Rules Tab */}
        {activeTab === 'rules' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-slate-500">
                Configure notification rules for different event types
              </p>
              <Link
                href="/settings/notification-rules/new"
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Rule
              </Link>
            </div>
            
            {rules.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
                <Settings className="w-12 h-12 text-slate-300 mx-auto" />
                <p className="text-slate-600 font-medium mt-3">No notification rules</p>
                <p className="text-sm text-slate-400 mt-1">
                  Create rules to automate notifications
                </p>
              </div>
            ) : (
              rules.map((rule) => (
                <RuleCard
                  key={rule.id}
                  rule={rule}
                  onDelete={() => deleteRule(rule.id)}
                />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default NotificationDrawer
