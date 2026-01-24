'use client'

/**
 * AQUAWATCH NRW - LEAKS LIST PAGE
 * ================================
 * 
 * Step 8: Enhanced leaks list with AI confidence indicators
 * Shows all detected leaks with quick AI insights
 */

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Droplets,
  Filter,
  Loader2,
  MapPin,
  RefreshCw,
  Search,
  Users,
  Brain,
  ChevronRight,
  ArrowUpDown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// =============================================================================
// TYPES
// =============================================================================

interface Leak {
  id: string
  location: string
  dma_id: string
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
    resolved: <CheckCircle className="w-4 h-4" />,
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
  return `${diffMins}m ago`
}

// =============================================================================
// MOCK DATA
// =============================================================================

const mockLeaks: Leak[] = [
  {
    id: 'LEAK-001',
    location: 'Chilenje South, Plot 234, Main Distribution Line',
    dma_id: 'DMA-001',
    estimated_loss: 45,
    priority: 'high',
    confidence: 87,
    detected_at: new Date(Date.now() - 3600000).toISOString(),
    status: 'new',
    ai_reason: {
      top_signals: ['multi_sensor_agreement', 'pressure_drop', 'flow_rise'],
      explanation: 'High confidence leak detection. Multiple sensors showing correlated anomalies.',
      confidence: { overall_confidence: 0.87 }
    }
  },
  {
    id: 'LEAK-002',
    location: 'Kabwata Zone 5, Near Main Road Junction',
    dma_id: 'DMA-002',
    estimated_loss: 28,
    priority: 'medium',
    confidence: 72,
    detected_at: new Date(Date.now() - 7200000).toISOString(),
    status: 'acknowledged',
    acknowledged_at: new Date(Date.now() - 5400000).toISOString(),
    ai_reason: {
      top_signals: ['pressure_drop', 'flow_rise'],
      explanation: 'Moderate confidence detection based on pressure and flow anomalies.',
      confidence: { overall_confidence: 0.72 }
    }
  },
  {
    id: 'LEAK-003',
    location: 'Mtendere East, Block 12',
    dma_id: 'DMA-003',
    estimated_loss: 65,
    priority: 'high',
    confidence: 92,
    detected_at: new Date(Date.now() - 10800000).toISOString(),
    status: 'dispatched',
    acknowledged_at: new Date(Date.now() - 9000000).toISOString(),
    dispatched_at: new Date(Date.now() - 7200000).toISOString(),
    ai_reason: {
      top_signals: ['acoustic_anomaly', 'multi_sensor_agreement', 'pressure_drop'],
      explanation: 'Very high confidence detection with acoustic confirmation.',
      confidence: { overall_confidence: 0.92 }
    }
  },
  {
    id: 'LEAK-004',
    location: 'Kalingalinga Main, Service Connection 456',
    dma_id: 'DMA-001',
    estimated_loss: 12,
    priority: 'low',
    confidence: 58,
    detected_at: new Date(Date.now() - 86400000).toISOString(),
    status: 'resolved',
    resolved_at: new Date(Date.now() - 43200000).toISOString(),
    ai_reason: {
      top_signals: ['night_flow_deviation'],
      explanation: 'Low confidence detection based on night flow analysis.',
      confidence: { overall_confidence: 0.58 }
    }
  },
]

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LeaksListPage() {
  const [leaks, setLeaks] = useState<Leak[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<'detected_at' | 'confidence' | 'estimated_loss'>('detected_at')

  useEffect(() => {
    const fetchLeaks = async () => {
      try {
        const response = await fetch('/api/leaks')
        const data = await response.json()
        if (data.success && data.data.length > 0) {
          setLeaks(data.data)
        } else {
          // Use mock data if no leaks found
          setLeaks(mockLeaks)
        }
      } catch (err) {
        console.error('Error fetching leaks:', err)
        setLeaks(mockLeaks)
      } finally {
        setLoading(false)
      }
    }
    fetchLeaks()
  }, [])

  // Filter and sort leaks
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

  // Stats
  const stats = {
    total: leaks.length,
    new: leaks.filter(l => l.status === 'new').length,
    acknowledged: leaks.filter(l => l.status === 'acknowledged').length,
    dispatched: leaks.filter(l => l.status === 'dispatched').length,
    resolved: leaks.filter(l => l.status === 'resolved').length,
    totalLoss: leaks.filter(l => l.status !== 'resolved').reduce((sum, l) => sum + l.estimated_loss, 0),
  }

  return (
    <div className="min-h-screen bg-muted/30 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold">Leak Alerts</h1>
            <p className="text-muted-foreground">
              AI-detected leaks with explainable insights
            </p>
          </div>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-sm text-muted-foreground">Total Leaks</div>
            </CardContent>
          </Card>
          <Card className="border-red-200 bg-red-50/50">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{stats.new}</div>
              <div className="text-sm text-red-600">New</div>
            </CardContent>
          </Card>
          <Card className="border-amber-200 bg-amber-50/50">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-amber-600">{stats.acknowledged}</div>
              <div className="text-sm text-amber-600">Acknowledged</div>
            </CardContent>
          </Card>
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">{stats.dispatched}</div>
              <div className="text-sm text-blue-600">Dispatched</div>
            </CardContent>
          </Card>
          <Card className="border-green-200 bg-green-50/50">
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{stats.resolved}</div>
              <div className="text-sm text-green-600">Resolved</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{stats.totalLoss}</div>
              <div className="text-sm text-muted-foreground">m³/day Loss</div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  placeholder="Search by location or ID..."
                  className="pl-10"
                  value={search}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
                />
              </div>
              <Select value={filter} onValueChange={setFilter}>
                <SelectTrigger className="w-full sm:w-40">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="dispatched">Dispatched</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
              <Select value={sortBy} onValueChange={(v: string) => setSortBy(v as typeof sortBy)}>
                <SelectTrigger className="w-full sm:w-40">
                  <ArrowUpDown className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="detected_at">Most Recent</SelectItem>
                  <SelectItem value="confidence">Highest Confidence</SelectItem>
                  <SelectItem value="estimated_loss">Highest Loss</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Leaks List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : filteredLeaks.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold">No Leaks Found</h3>
              <p className="text-muted-foreground">
                {search || filter !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'No active leak alerts at this time'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredLeaks.map((leak) => (
              <Link key={leak.id} href={`/leaks/${leak.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      {/* Priority Indicator */}
                      <div className={`w-1 self-stretch rounded-full ${getPriorityColor(leak.priority)}`} />
                      
                      {/* Main Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="font-semibold">{leak.id}</span>
                          <Badge className={getStatusColor(leak.status)}>
                            {getStatusIcon(leak.status)}
                            <span className="ml-1 capitalize">{leak.status}</span>
                          </Badge>
                          <Badge variant="outline" className="capitalize">{leak.priority}</Badge>
                        </div>
                        
                        <p className="text-sm text-muted-foreground flex items-center gap-1 mb-2">
                          <MapPin className="w-3 h-3" />
                          {leak.location}
                        </p>
                        
                        {/* AI Insight Preview */}
                        {leak.ai_reason && (
                          <div className="flex items-center gap-2 text-xs text-purple-600 bg-purple-50 dark:bg-purple-950/20 px-2 py-1 rounded w-fit">
                            <Brain className="w-3 h-3" />
                            <span className="truncate max-w-xs">{leak.ai_reason.top_signals.join(', ')}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Stats */}
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-center">
                          <div className="font-bold text-red-600">{leak.estimated_loss}</div>
                          <div className="text-xs text-muted-foreground">m³/day</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-purple-600">{leak.confidence}%</div>
                          <div className="text-xs text-muted-foreground">AI conf.</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">{getTimeSince(leak.detected_at)}</div>
                          <div className="text-xs text-muted-foreground">detected</div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
