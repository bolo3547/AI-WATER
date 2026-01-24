'use client'

/**
 * AQUAWATCH NRW - LEAKS LIST PAGE
 * ================================
 * 
 * Production-ready leak alerts page with:
 * - Real API data fetching with SWR
 * - Working action buttons (Acknowledge, Dispatch, Resolve)
 * - Loading skeletons and empty states
 * - No mock/fake data
 */

import React, { useState } from 'react'
import Link from 'next/link'
import {
  AlertTriangle,
  CheckCircle,
  Loader2,
  MapPin,
  RefreshCw,
  Search,
  Users,
  Brain,
  ChevronRight,
  CheckCheck,
  Wrench,
} from 'lucide-react'
import useSWR from 'swr'
import { useSystemStatus } from '@/contexts/SystemStatusContext'
import { 
  EmptyState, 
  NoSearchResults,
  ErrorState 
} from '@/components/ui/EmptyState'
import { StatCardSkeleton, ListItemSkeleton } from '@/components/ui/Skeleton'

// =============================================================================
// TYPES
// =============================================================================

interface Leak {
  _id?: string
  id: string
  location: string
  dma_id: string
  dma_name?: string
  estimated_loss: number
  priority: 'high' | 'medium' | 'low'
  confidence: number
  detected_at: string
  status: 'new' | 'acknowledged' | 'dispatched' | 'resolved'
  acknowledged_by?: string
  acknowledged_at?: string
  dispatched_at?: string
  resolved_at?: string
  notes?: string
  ai_reason?: {
    top_signals: string[]
    explanation: string
    confidence: {
      overall_confidence: number
    }
  } | null
}

interface LeaksResponse {
  success: boolean
  data: Leak[]
  total: number
  message?: string
}

// =============================================================================
// DATA FETCHER
// =============================================================================

const fetcher = async (url: string): Promise<LeaksResponse> => {
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to fetch leaks')
  return res.json()
}

// =============================================================================
// HELPERS
// =============================================================================

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    new: 'bg-red-100 text-red-800 border-red-200',
    acknowledged: 'bg-amber-100 text-amber-800 border-amber-200',
    dispatched: 'bg-blue-100 text-blue-800 border-blue-200',
    resolved: 'bg-green-100 text-green-800 border-green-200',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    high: 'bg-red-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
  }
  return colors[priority] || 'bg-gray-500'
}

const getStatusIcon = (status: string): React.ReactNode => {
  const icons: Record<string, React.ReactNode> = {
    new: <AlertTriangle className="w-4 h-4" />,
    acknowledged: <CheckCircle className="w-4 h-4" />,
    dispatched: <Users className="w-4 h-4" />,
    resolved: <CheckCheck className="w-4 h-4" />,
  }
  return icons[status] || null
}

function getTimeSince(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ago`
  if (diffHours > 0) return `${diffHours}h ago`
  if (diffMins > 0) return `${diffMins}m ago`
  return 'Just now'
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LeaksListPage() {
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'detected_at' | 'confidence' | 'estimated_loss'>('detected_at')
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  
  // System status for connection awareness
  const { status: systemStatus, isLoading: systemLoading, hasAnySensorData } = useSystemStatus()
  
  // Fetch leaks from API
  const { data, error, isLoading, mutate } = useSWR<LeaksResponse>(
    '/api/leaks',
    fetcher,
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
    }
  )
  
  const leaks = data?.data || []
  const hasData = leaks.length > 0

  // =============================================================================
  // ACTION HANDLERS (Real API calls)
  // =============================================================================

  const handleAcknowledge = async (e: React.MouseEvent, leakId: string) => {
    e.preventDefault()
    e.stopPropagation()
    
    setActionLoading(leakId)
    setActionError(null)
    
    try {
      const res = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leakId, action: 'acknowledge' })
      })
      
      if (!res.ok) throw new Error('Failed to acknowledge leak')
      
      await mutate()
    } catch (err) {
      setActionError('Failed to acknowledge leak. Please try again.')
      console.error('Acknowledge error:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDispatch = async (e: React.MouseEvent, leakId: string) => {
    e.preventDefault()
    e.stopPropagation()
    
    setActionLoading(leakId)
    setActionError(null)
    
    try {
      const res = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leakId, action: 'dispatch' })
      })
      
      if (!res.ok) throw new Error('Failed to dispatch crew')
      
      await mutate()
    } catch (err) {
      setActionError('Failed to dispatch crew. Please try again.')
      console.error('Dispatch error:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleResolve = async (e: React.MouseEvent, leakId: string) => {
    e.preventDefault()
    e.stopPropagation()
    
    setActionLoading(leakId)
    setActionError(null)
    
    try {
      const res = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leakId, action: 'resolve' })
      })
      
      if (!res.ok) throw new Error('Failed to resolve leak')
      
      await mutate()
    } catch (err) {
      setActionError('Failed to resolve leak. Please try again.')
      console.error('Resolve error:', err)
    } finally {
      setActionLoading(null)
    }
  }

  // =============================================================================
  // FILTERING & SORTING
  // =============================================================================

  const filteredLeaks = leaks
    .filter(leak => {
      if (filter !== 'all' && leak.status !== filter) return false
      if (search && !leak.location.toLowerCase().includes(search.toLowerCase()) && 
          !leak.id.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'detected_at') {
        return new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime()
      }
      if (sortBy === 'confidence') {
        return b.confidence - a.confidence
      }
      return b.estimated_loss - a.estimated_loss
    })

  // Stats (only from real data)
  const stats = {
    total: leaks.length,
    new: leaks.filter(l => l.status === 'new').length,
    acknowledged: leaks.filter(l => l.status === 'acknowledged').length,
    dispatched: leaks.filter(l => l.status === 'dispatched').length,
    resolved: leaks.filter(l => l.status === 'resolved').length,
    totalLoss: leaks.filter(l => l.status !== 'resolved').reduce((sum, l) => sum + (l.estimated_loss || 0), 0),
  }

  // =============================================================================
  // RENDER
  // =============================================================================

  // Show system offline state
  if (!systemLoading && systemStatus && !systemStatus.database_connected) {
    return (
      <div className="min-h-screen bg-slate-50 p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <ErrorState 
            error="Unable to connect to the database. Please check your connection and try again."
            onRetry={() => mutate()}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Leak Alerts</h1>
            <p className="text-slate-500">
              {hasData 
                ? `AI-detected leaks with explainable insights • ${stats.total} total`
                : 'No leak alerts detected'}
            </p>
          </div>
          <button 
            onClick={() => mutate()}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Error Alert */}
        {actionError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
            <span>{actionError}</span>
            <button onClick={() => setActionError(null)} className="text-red-500 hover:text-red-700">
              ×
            </button>
          </div>
        )}

        {/* API Error */}
        {error && (
          <ErrorState 
            error={error.message || 'Failed to load leak alerts'}
            onRetry={() => mutate()}
          />
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {[...Array(6)].map((_, i) => (
                <StatCardSkeleton key={i} />
              ))}
            </div>
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <ListItemSkeleton key={i} />
              ))}
            </div>
          </div>
        )}

        {/* Data Loaded */}
        {!isLoading && !error && (
          <>
            {/* Stats Cards - Only show real numbers */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="text-2xl font-bold text-slate-900">{hasData ? stats.total : '--'}</div>
                <div className="text-sm text-slate-500">Total Leaks</div>
              </div>
              <div className="bg-red-50 rounded-xl border border-red-200 p-4">
                <div className="text-2xl font-bold text-red-600">{hasData ? stats.new : '--'}</div>
                <div className="text-sm text-red-600">New</div>
              </div>
              <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
                <div className="text-2xl font-bold text-amber-600">{hasData ? stats.acknowledged : '--'}</div>
                <div className="text-sm text-amber-600">Acknowledged</div>
              </div>
              <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
                <div className="text-2xl font-bold text-blue-600">{hasData ? stats.dispatched : '--'}</div>
                <div className="text-sm text-blue-600">Dispatched</div>
              </div>
              <div className="bg-emerald-50 rounded-xl border border-emerald-200 p-4">
                <div className="text-2xl font-bold text-emerald-600">{hasData ? stats.resolved : '--'}</div>
                <div className="text-sm text-emerald-600">Resolved</div>
              </div>
              <div className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="text-2xl font-bold text-red-600">{hasData ? stats.totalLoss.toFixed(0) : '--'}</div>
                <div className="text-sm text-slate-500">m³/day Loss</div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input 
                    type="text"
                    placeholder="Search by location or ID..."
                    className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <select 
                  value={filter} 
                  onChange={(e) => setFilter(e.target.value)}
                  className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="all">All Status</option>
                  <option value="new">New</option>
                  <option value="acknowledged">Acknowledged</option>
                  <option value="dispatched">Dispatched</option>
                  <option value="resolved">Resolved</option>
                </select>
                <select 
                  value={sortBy} 
                  onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                  className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="detected_at">Most Recent</option>
                  <option value="confidence">Highest Confidence</option>
                  <option value="estimated_loss">Highest Loss</option>
                </select>
              </div>
            </div>

            {/* Empty State - No leaks detected */}
            {!hasData && (
              <EmptyState
                icon={<CheckCircle className="w-8 h-8" />}
                title="No Leaks Detected"
                description={
                  hasAnySensorData 
                    ? "Great news! The AI system hasn't detected any leaks. The network is operating normally."
                    : "Connect your ESP32 sensors via MQTT to start receiving real-time leak detection alerts."
                }
                variant={hasAnySensorData ? 'default' : 'no-sensors'}
                action={!hasAnySensorData ? {
                  label: 'Configure Sensors',
                  onClick: () => window.location.href = '/admin/firmware'
                } : undefined}
              />
            )}

            {/* Search found nothing */}
            {hasData && filteredLeaks.length === 0 && (search || filter !== 'all') && (
              <NoSearchResults 
                query={search || filter}
                onClearSearch={() => { setSearch(''); setFilter('all'); }}
              />
            )}

            {/* Leaks List */}
            {filteredLeaks.length > 0 && (
              <div className="space-y-3">
                {filteredLeaks.map((leak) => (
                  <Link key={leak._id || leak.id} href={`/leaks/${leak.id}`}>
                    <div className="bg-white rounded-xl border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all cursor-pointer">
                      <div className="p-4">
                        <div className="flex items-start gap-4">
                          {/* Priority Indicator */}
                          <div className={`w-1 self-stretch rounded-full ${getPriorityColor(leak.priority)}`} />
                          
                          {/* Main Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <span className="font-semibold text-slate-900">{leak.id}</span>
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(leak.status)}`}>
                                {getStatusIcon(leak.status)}
                                <span className="capitalize">{leak.status}</span>
                              </span>
                              <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full text-xs font-medium capitalize">
                                {leak.priority}
                              </span>
                            </div>
                            
                            <p className="text-sm text-slate-500 flex items-center gap-1 mb-2">
                              <MapPin className="w-3 h-3" />
                              {leak.location}
                            </p>
                            
                            {/* AI Insight Preview */}
                            {leak.ai_reason && leak.ai_reason.top_signals && (
                              <div className="flex items-center gap-2 text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded w-fit">
                                <Brain className="w-3 h-3" />
                                <span className="truncate max-w-xs">{leak.ai_reason.top_signals.join(', ')}</span>
                              </div>
                            )}

                            {/* Quick Actions */}
                            <div className="flex items-center gap-2 mt-3">
                              {leak.status === 'new' && (
                                <button
                                  onClick={(e) => handleAcknowledge(e, leak.id)}
                                  disabled={actionLoading === leak.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-amber-100 text-amber-700 rounded-lg text-xs font-medium hover:bg-amber-200 disabled:opacity-50 transition-colors"
                                >
                                  {actionLoading === leak.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <CheckCircle className="w-3 h-3" />
                                  )}
                                  Acknowledge
                                </button>
                              )}
                              {leak.status === 'acknowledged' && (
                                <button
                                  onClick={(e) => handleDispatch(e, leak.id)}
                                  disabled={actionLoading === leak.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-lg text-xs font-medium hover:bg-blue-200 disabled:opacity-50 transition-colors"
                                >
                                  {actionLoading === leak.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <Users className="w-3 h-3" />
                                  )}
                                  Dispatch Crew
                                </button>
                              )}
                              {leak.status === 'dispatched' && (
                                <button
                                  onClick={(e) => handleResolve(e, leak.id)}
                                  disabled={actionLoading === leak.id}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-200 disabled:opacity-50 transition-colors"
                                >
                                  {actionLoading === leak.id ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                  ) : (
                                    <CheckCheck className="w-3 h-3" />
                                  )}
                                  Mark Resolved
                                </button>
                              )}
                              <Link 
                                href={`/work-orders/new?leak_id=${leak.id}`}
                                onClick={(e) => e.stopPropagation()}
                                className="flex items-center gap-1 px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium hover:bg-slate-200 transition-colors"
                              >
                                <Wrench className="w-3 h-3" />
                                Create Work Order
                              </Link>
                            </div>
                          </div>
                          
                          {/* Stats */}
                          <div className="flex items-center gap-6 text-sm">
                            <div className="text-center">
                              <div className="font-bold text-red-600">{leak.estimated_loss || 0}</div>
                              <div className="text-xs text-slate-500">m³/day</div>
                            </div>
                            <div className="text-center">
                              <div className="font-bold text-purple-600">{leak.confidence || 0}%</div>
                              <div className="text-xs text-slate-500">AI conf.</div>
                            </div>
                            <div className="text-center">
                              <div className="font-medium text-slate-700">{getTimeSince(leak.detected_at)}</div>
                              <div className="text-xs text-slate-500">detected</div>
                            </div>
                            <ChevronRight className="w-5 h-5 text-slate-400" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
