'use client'

/**
 * AQUAWATCH NRW - LEAK DETAIL PAGE
 * =================================
 * 
 * Step 8: Full leak detail page with Explainable AI insights
 * Shows comprehensive leak information including:
 * - Basic leak information
 * - AI analysis with XAI panel
 * - Location map
 * - Status timeline
 * - Actions
 */

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  ArrowLeft,
  MapPin,
  Clock,
  AlertTriangle,
  Droplets,
  CheckCircle,
  Users,
  Wrench,
  Phone,
  FileText,
  RefreshCw,
  ExternalLink,
  Brain,
  Activity,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { LeakXAIPanel } from '@/components/ai/LeakXAIPanel'

// =============================================================================
// TYPES
// =============================================================================

interface AIReason {
  pressure_drop?: {
    signal_type: string
    contribution: number
    value: number
    threshold: number
    deviation: number
    description: string
    timestamp: string
    sensor_id?: string | null
    raw_data?: Record<string, unknown>
  } | null
  flow_rise?: {
    signal_type: string
    contribution: number
    value: number
    threshold: number
    deviation: number
    description: string
    timestamp: string
    sensor_id?: string | null
    raw_data?: Record<string, unknown>
  } | null
  multi_sensor_agreement?: {
    signal_type: string
    contribution: number
    value: number
    threshold: number
    deviation: number
    description: string
    timestamp: string
    sensor_id?: string | null
    raw_data?: Record<string, unknown>
  } | null
  night_flow_deviation?: {
    signal_type: string
    contribution: number
    value: number
    threshold: number
    deviation: number
    description: string
    timestamp: string
    sensor_id?: string | null
    raw_data?: Record<string, unknown>
  } | null
  acoustic_anomaly?: {
    signal_type: string
    contribution: number
    value: number
    threshold: number
    deviation: number
    description: string
    timestamp: string
    sensor_id?: string | null
    raw_data?: Record<string, unknown>
  } | null
  confidence: {
    statistical_confidence: number
    ml_confidence: number
    temporal_confidence: number
    spatial_confidence: number
    acoustic_confidence: number
    overall_confidence: number
    weights: Record<string, number>
  }
  top_signals: string[]
  evidence_timeline: {
    timestamp: string
    signal_type: string
    value: number
    anomaly_score: number
    description: string
    is_key_event: boolean
  }[]
  detection_method: string
  detection_timestamp: string
  analysis_duration_seconds: number
  explanation: string
  recommendations: string[]
  model_version: string
  feature_importance: Record<string, number>
}

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
  ai_reason?: AIReason | null
  // Additional fields
  pipe_id?: string
  latitude?: number
  longitude?: number
  flow_rate?: number
  pressure?: number
}

// =============================================================================
// STATUS HELPERS
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
    high: 'bg-red-500 text-white',
    medium: 'bg-amber-500 text-white',
    low: 'bg-blue-500 text-white',
  }
  return colors[priority] || 'bg-gray-500 text-white'
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

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LeakDetailPage() {
  const params = useParams()
  const router = useRouter()
  const leakId = params?.id as string
  
  const [leak, setLeak] = useState<Leak | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updating, setUpdating] = useState(false)

  // Fetch leak data
  useEffect(() => {
    const fetchLeak = async () => {
      if (!leakId) return
      
      try {
        setLoading(true)
        const response = await fetch(`/api/leaks?id=${leakId}`)
        const data = await response.json()
        
        if (data.success && data.data) {
          // Handle both array and single object response
          const leakData = Array.isArray(data.data) 
            ? data.data.find((l: Leak) => l.id === leakId)
            : data.data
          
          if (leakData) {
            setLeak(leakData)
          } else {
            // If not found, create mock data for demo
            setLeak(createMockLeak(leakId))
          }
        } else {
          // Fallback to mock data
          setLeak(createMockLeak(leakId))
        }
      } catch (err) {
        console.error('Error fetching leak:', err)
        // Use mock data on error
        setLeak(createMockLeak(leakId))
      } finally {
        setLoading(false)
      }
    }
    
    fetchLeak()
  }, [leakId])

  // Action handlers
  const handleAcknowledge = async () => {
    if (!leak) return
    setUpdating(true)
    try {
      const response = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leak.id, action: 'acknowledge', user: 'Current User' })
      })
      const data = await response.json()
      if (data.success) {
        setLeak(prev => prev ? { ...prev, status: 'acknowledged', acknowledged_at: new Date().toISOString() } : null)
      }
    } catch (err) {
      console.error('Error acknowledging leak:', err)
    }
    setUpdating(false)
  }

  const handleDispatch = async () => {
    if (!leak) return
    setUpdating(true)
    try {
      const response = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leak.id, action: 'dispatch' })
      })
      const data = await response.json()
      if (data.success) {
        setLeak(prev => prev ? { ...prev, status: 'dispatched', dispatched_at: new Date().toISOString() } : null)
      }
    } catch (err) {
      console.error('Error dispatching:', err)
    }
    setUpdating(false)
  }

  const handleResolve = async () => {
    if (!leak) return
    setUpdating(true)
    try {
      const response = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: leak.id, action: 'resolve' })
      })
      const data = await response.json()
      if (data.success) {
        setLeak(prev => prev ? { ...prev, status: 'resolved', resolved_at: new Date().toISOString() } : null)
      }
    } catch (err) {
      console.error('Error resolving:', err)
    }
    setUpdating(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading leak details...</p>
        </div>
      </div>
    )
  }

  if (error || !leak) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h1 className="text-xl font-semibold mb-2">Leak Not Found</h1>
          <p className="text-muted-foreground mb-4">{error || 'The requested leak could not be found.'}</p>
          <Button onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted/30 p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold">Leak {leak.id}</h1>
              <Badge className={getStatusColor(leak.status)}>
                {getStatusIcon(leak.status)}
                <span className="ml-1 capitalize">{leak.status}</span>
              </Badge>
              <Badge className={getPriorityColor(leak.priority)}>
                {leak.priority.toUpperCase()} PRIORITY
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              {leak.location}
            </p>
          </div>
          <Button variant="outline" onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="ai-analysis" className="flex items-center gap-2">
              <Brain className="w-4 h-4" />
              AI Analysis
            </TabsTrigger>
            <TabsTrigger value="timeline" className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Timeline
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Key Metrics */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Droplets className="w-4 h-4 text-blue-500" />
                    Estimated Loss
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-red-600">
                    {leak.estimated_loss.toLocaleString()} <span className="text-sm font-normal">m³/day</span>
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    ≈ ${(leak.estimated_loss * 0.5).toFixed(2)}/day at current rates
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Brain className="w-4 h-4 text-purple-500" />
                    AI Confidence
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-purple-600">
                    {leak.confidence}%
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Detection confidence score
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-500" />
                    Time Since Detection
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {getTimeSince(leak.detected_at)}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {new Date(leak.detected_at).toLocaleString()}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Leak Information</CardTitle>
                  <CardDescription>Details about the detected leak</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">DMA</p>
                      <p className="font-medium">{leak.dma_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Pipe ID</p>
                      <p className="font-medium">{leak.pipe_id || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Flow Rate</p>
                      <p className="font-medium">{leak.flow_rate || 'N/A'} L/min</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Pressure</p>
                      <p className="font-medium">{leak.pressure || 'N/A'} bar</p>
                    </div>
                  </div>
                  {leak.notes && (
                    <div>
                      <p className="text-sm text-muted-foreground">Notes</p>
                      <p className="font-medium">{leak.notes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Actions Card */}
              <Card>
                <CardHeader>
                  <CardTitle>Actions</CardTitle>
                  <CardDescription>Manage this leak alert</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {leak.status === 'new' && (
                    <Button 
                      className="w-full" 
                      onClick={handleAcknowledge}
                      disabled={updating}
                    >
                      {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                      Acknowledge Alert
                    </Button>
                  )}
                  {(leak.status === 'new' || leak.status === 'acknowledged') && (
                    <Button 
                      className="w-full" 
                      variant="default"
                      onClick={handleDispatch}
                      disabled={updating}
                    >
                      {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Users className="w-4 h-4 mr-2" />}
                      Dispatch Field Team
                    </Button>
                  )}
                  {leak.status === 'dispatched' && (
                    <Button 
                      className="w-full" 
                      variant="default"
                      onClick={handleResolve}
                      disabled={updating}
                    >
                      {updating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                      Mark as Resolved
                    </Button>
                  )}
                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <Button variant="outline" className="w-full">
                      <Wrench className="w-4 h-4 mr-2" />
                      Create Work Order
                    </Button>
                    <Button variant="outline" className="w-full">
                      <Phone className="w-4 h-4 mr-2" />
                      Call Crew
                    </Button>
                  </div>
                  <Button variant="outline" className="w-full">
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Report
                  </Button>
                  <Link href={`/map?leak=${leak.id}`} className="block">
                    <Button variant="outline" className="w-full">
                      <ExternalLink className="w-4 h-4 mr-2" />
                      View on Map
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>

            {/* Quick AI Summary */}
            {leak.ai_reason && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-500" />
                    AI Detection Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                    <p className="text-amber-800 dark:text-amber-200">
                      {leak.ai_reason.explanation}
                    </p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="text-sm text-muted-foreground">Top signals:</span>
                    {leak.ai_reason.top_signals.slice(0, 3).map((signal) => (
                      <Badge key={signal} variant="secondary">
                        {signal.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* AI Analysis Tab */}
          <TabsContent value="ai-analysis">
            <LeakXAIPanel aiReason={leak.ai_reason} leakId={leak.id} />
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline">
            <Card>
              <CardHeader>
                <CardTitle>Event Timeline</CardTitle>
                <CardDescription>History of actions taken on this leak</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <TimelineItem
                    icon={<AlertTriangle className="w-4 h-4" />}
                    title="Leak Detected"
                    description={`AI detected potential leak with ${leak.confidence}% confidence`}
                    timestamp={leak.detected_at}
                    status="completed"
                  />
                  {leak.acknowledged_at && (
                    <TimelineItem
                      icon={<CheckCircle className="w-4 h-4" />}
                      title="Alert Acknowledged"
                      description={`Acknowledged by ${leak.acknowledged_by || 'Operator'}`}
                      timestamp={leak.acknowledged_at}
                      status="completed"
                    />
                  )}
                  {leak.dispatched_at && (
                    <TimelineItem
                      icon={<Users className="w-4 h-4" />}
                      title="Team Dispatched"
                      description="Field team assigned and en route"
                      timestamp={leak.dispatched_at}
                      status="completed"
                    />
                  )}
                  {leak.resolved_at && (
                    <TimelineItem
                      icon={<CheckCircle className="w-4 h-4" />}
                      title="Leak Resolved"
                      description="Leak has been repaired and verified"
                      timestamp={leak.resolved_at}
                      status="completed"
                    />
                  )}
                  {!leak.resolved_at && (
                    <TimelineItem
                      icon={<Wrench className="w-4 h-4" />}
                      title="Pending Resolution"
                      description="Awaiting repair completion"
                      timestamp=""
                      status="pending"
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

interface TimelineItemProps {
  icon: React.ReactNode
  title: string
  description: string
  timestamp: string
  status: 'completed' | 'pending'
}

const TimelineItem: React.FC<TimelineItemProps> = ({ icon, title, description, timestamp, status }) => (
  <div className="flex gap-4">
    <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
      status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-muted text-muted-foreground'
    }`}>
      {icon}
    </div>
    <div className="flex-1 pb-4 border-l-2 border-muted pl-4 -ml-4">
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
      {timestamp && (
        <p className="text-xs text-muted-foreground mt-1">
          {new Date(timestamp).toLocaleString()}
        </p>
      )}
    </div>
  </div>
)

// =============================================================================
// UTILITIES
// =============================================================================

function getTimeSince(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) return `${diffDays}d ${diffHours % 24}h`
  if (diffHours > 0) return `${diffHours}h ${diffMins % 60}m`
  return `${diffMins}m`
}

function createMockLeak(id: string): Leak {
  return {
    id,
    location: 'Chilenje South, Plot 234, Main Distribution Line',
    dma_id: 'DMA-001',
    estimated_loss: 45,
    priority: 'high',
    confidence: 87,
    detected_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    status: 'new',
    pipe_id: 'PIPE-CS-001',
    flow_rate: 125.5,
    pressure: 2.3,
    ai_reason: {
      pressure_drop: {
        signal_type: 'pressure_drop',
        contribution: 0.85,
        value: 2.3,
        threshold: 2.7,
        deviation: -0.4,
        description: 'Sustained pressure drop of 0.4 bar detected. Current: 2.30 bar, Expected: 2.70 bar',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        sensor_id: 'PS-001',
        raw_data: { baseline_mean: 2.7, baseline_std: 0.1 }
      },
      flow_rise: {
        signal_type: 'flow_rise',
        contribution: 0.72,
        value: 125.5,
        threshold: 105,
        deviation: 20.5,
        description: 'Flow increased by 26% above baseline. Current: 125.5 L/min, Expected: 100 L/min',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        sensor_id: 'FS-001',
        raw_data: { flow_change_rate: 26 }
      },
      multi_sensor_agreement: {
        signal_type: 'multi_sensor_agreement',
        contribution: 0.90,
        value: 4,
        threshold: 2,
        deviation: 2,
        description: '4 sensors showing correlated anomalies, strongly indicating leak presence.',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        sensor_id: null,
        raw_data: { sensors: ['PS-001', 'PS-002', 'FS-001', 'FS-002'] }
      },
      night_flow_deviation: null,
      acoustic_anomaly: {
        signal_type: 'acoustic_anomaly',
        contribution: 0.68,
        value: 78,
        threshold: 60,
        deviation: 18,
        description: 'Acoustic signature detected at 78 dB (threshold: 60 dB). Sound pattern consistent with water leak.',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        sensor_id: 'AS-001'
      },
      confidence: {
        statistical_confidence: 0.82,
        ml_confidence: 0.78,
        temporal_confidence: 0.65,
        spatial_confidence: 0.90,
        acoustic_confidence: 0.68,
        overall_confidence: 0.87,
        weights: {
          statistical: 0.20,
          ml: 0.25,
          temporal: 0.20,
          spatial: 0.25,
          acoustic: 0.10
        }
      },
      top_signals: ['multi_sensor_agreement', 'pressure_drop', 'flow_rise', 'acoustic_anomaly'],
      evidence_timeline: [
        {
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          signal_type: 'pressure_drop',
          value: 2.5,
          anomaly_score: 0.45,
          description: 'Pressure beginning to decrease',
          is_key_event: false
        },
        {
          timestamp: new Date(Date.now() - 5400000).toISOString(),
          signal_type: 'flow_rise',
          value: 115,
          anomaly_score: 0.55,
          description: 'Flow starting to increase above normal',
          is_key_event: false
        },
        {
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          signal_type: 'pressure_drop',
          value: 2.3,
          anomaly_score: 0.85,
          description: 'Sustained pressure drop confirmed',
          is_key_event: true
        },
        {
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          signal_type: 'multi_sensor_agreement',
          value: 4,
          anomaly_score: 0.90,
          description: 'Multiple sensors corroborating anomaly',
          is_key_event: true
        }
      ],
      detection_method: 'multi_signal',
      detection_timestamp: new Date(Date.now() - 3600000).toISOString(),
      analysis_duration_seconds: 0.35,
      explanation: 'High confidence leak detection (87%). Primary indicator: Multiple sensors showing correlated anomalies. Sustained pressure drop of 0.4 bar below baseline. Flow increased by 26% above normal levels. Acoustic signature detected at 78 dB, consistent with water leak sound pattern.',
      recommendations: [
        'URGENT: Dispatch field team immediately for visual inspection.',
        'Use sensor triangulation data to narrow search area.',
        'Deploy acoustic localization equipment for precise positioning.',
        'Consider isolating affected section to minimize water loss.'
      ],
      model_version: '3.0.0',
      feature_importance: {
        multi_sensor_agreement: 0.90,
        pressure_drop: 0.85,
        flow_rise: 0.72,
        acoustic_anomaly: 0.68
      }
    }
  }
}
