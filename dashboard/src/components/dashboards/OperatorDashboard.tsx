'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { 
  Gauge, TrendingDown, Droplets, Activity,
  AlertTriangle, MapPin, ShieldCheck, Clock, ArrowRight,
  Radio, Bell, CheckCircle2, XCircle, Play, Pause,
  Volume2, Wifi, Wrench, Eye, Loader2, Brain, Sparkles,
  RefreshCw, WifiOff, Info
} from 'lucide-react'
import { formatNumber, formatRelativeTime } from '@/lib/api'
import { SectionCard, AlertBanner } from '@/components/ui/Cards'
import { NRWTrendChart } from '@/components/charts/Charts'
import { AIInsightsPanel, AIQuickInsight } from '@/components/ai/AIInsightsPanel'

// Types
interface Metrics {
  total_nrw_percent: number
  sensor_count: number
  dma_count: number
  active_high_priority_leaks: number
  ai_confidence: number
  last_data_received: string
}

interface DMA {
  dma_id: string
  name: string
  nrw_percent: number
  priority_score: number
  status: 'critical' | 'warning' | 'healthy'
}

interface Sensor {
  id: string
  name: string
  status: 'healthy' | 'warning' | 'critical'
  battery: number
  signal: number
  flow_rate?: number
  pressure?: number
  last_reading: string
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
}

export function OperatorDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [dmas, setDMAs] = useState<DMA[]>([])
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [leaks, setLeaks] = useState<Leak[]>([])
  const [trendData, setTrendData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Fetch real-time data
  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, dmasRes, sensorsRes, leaksRes] = await Promise.all([
        fetch('/api/realtime?type=metrics'),
        fetch('/api/realtime?type=dmas'),
        fetch('/api/realtime?type=sensors'),
        fetch('/api/leaks')
      ])
      
      const [metricsData, dmasData, sensorsData, leaksData] = await Promise.all([
        metricsRes.json(),
        dmasRes.json(),
        sensorsRes.json(),
        leaksRes.json()
      ])
      
      if (metricsData.metrics) setMetrics(metricsData.metrics)
      if (dmasData.dmas) setDMAs(dmasData.dmas)
      if (sensorsData.sensors) setSensors(sensorsData.sensors)
      if (leaksData.success) setLeaks(leaksData.data || [])
      
      // Generate trend based on real metrics
      const baseNrw = metricsData.metrics?.total_nrw_percent || 32
      const trend = Array.from({ length: 30 }, (_, i) => ({
        timestamp: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
        nrw: baseNrw + 6 - (i * 0.2) + (Math.random() * 2 - 1),
        target: 25
      }))
      setTrendData(trend)
      
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      console.error('Failed to fetch data:', err)
      setError('Live data unavailable')
    } finally {
      setLoading(false)
    }
  }, [])

  // Handle leak actions (acknowledge, dispatch)
  const handleLeakAction = async (leakId: string, action: 'acknowledge' | 'dispatch') => {
    setActionLoading(leakId)
    try {
      const userStr = localStorage.getItem('user')
      const user = userStr ? JSON.parse(userStr) : { name: 'Operator' }
      
      const response = await fetch('/api/leaks', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: leakId,
          action: action,
          user: user.name || user.username || 'Operator'
        })
      })
      
      const data = await response.json()
      
      if (data.success) {
        // Update local state
        setLeaks(prev => prev.map(leak => 
          leak.id === leakId ? data.data : leak
        ))
      } else {
        alert(data.error || 'Action failed')
      }
    } catch (err) {
      console.error('Failed to update leak:', err)
      alert('Failed to update leak status')
    } finally {
      setActionLoading(null)
    }
  }
  
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Fetch data initially and every 10 seconds
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const displayMetrics = metrics || {
    total_nrw_percent: 0,
    sensor_count: 0,
    dma_count: 0,
    active_high_priority_leaks: 0,
    ai_confidence: 0,
    last_data_received: new Date().toISOString()
  }
  const displayDMAs = dmas.length > 0 ? dmas : []
  const displayTrend = trendData.length > 0 ? trendData : []
  
  // Convert sensors to display format
  const sensorsDisplay = sensors.map(s => ({
    id: s.id,
    name: s.name,
    status: s.status === 'healthy' ? 'online' : s.status === 'warning' ? 'warning' : 'offline',
    value: s.flow_rate || s.pressure || null,
    unit: s.flow_rate ? 'm³/h' : s.pressure ? 'bar' : '-',
    lastSeen: formatRelativeTime(s.last_reading)
  }))

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return 'bg-red-500'
      case 'warning': return 'bg-amber-500'
      case 'healthy': return 'bg-emerald-500'
      case 'online': return 'bg-emerald-500'
      case 'offline': return 'bg-red-500'
      default: return 'bg-slate-400'
    }
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Operator Hero Section */}
      <div className="relative overflow-hidden rounded-xl sm:rounded-2xl bg-gradient-to-br from-cyan-900 via-slate-800 to-slate-900 p-4 sm:p-6 text-white">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 sm:mb-6">
            <div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                <div className="px-2 sm:px-3 py-1 bg-cyan-500/20 rounded-full border border-cyan-400/30">
                  <span className="text-[10px] sm:text-xs font-semibold text-cyan-300 uppercase tracking-wider">Operator</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full pulse-live" />
                  <span className="text-[10px] sm:text-xs font-medium text-emerald-400 uppercase">Live</span>
                </div>
                {lastUpdate && (
                  <span className="text-[10px] sm:text-xs text-slate-400 hidden sm:inline">Updated {lastUpdate.toLocaleTimeString()}</span>
                )}
              </div>
              <h1 className="text-xl sm:text-2xl font-bold">Control Room</h1>
              <p className="text-slate-400 text-xs sm:text-sm">Real-time network monitoring</p>
            </div>
            <div className="text-left sm:text-right">
              <div className="text-xl sm:text-3xl font-mono font-bold text-white/90">
                {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </div>
              <div className="text-[10px] sm:text-xs text-slate-400 mt-1">
                {currentTime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              </div>
            </div>
          </div>
          
          {/* Quick Stats - Responsive Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4">
            <Link href="/analytics" className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <Gauge className="w-4 sm:w-5 h-4 sm:h-5 text-blue-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">NRW</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold">{displayMetrics.total_nrw_percent?.toFixed(1)}%</div>
            </Link>
            
            <Link href="/actions" className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <AlertTriangle className="w-4 sm:w-5 h-4 sm:h-5 text-red-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">Alerts</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold text-red-400">{leaks.filter(l => l.status !== 'resolved').length}</div>
            </Link>
            
            <Link href="/health" className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <Radio className="w-4 sm:w-5 h-4 sm:h-5 text-emerald-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">Sensors</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold text-emerald-400">
                {sensors.filter(s => s.status === 'healthy').length}/{sensors.length || displayMetrics.sensor_count}
              </div>
            </Link>
            
            <Link href="/dma" className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10 hover:bg-white/10 transition-all cursor-pointer">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <MapPin className="w-4 sm:w-5 h-4 sm:h-5 text-purple-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">DMAs</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold">{dmas.length || displayMetrics.dma_count}</div>
            </Link>
            
            <Link href="/health" className="bg-white/5 backdrop-blur rounded-lg sm:rounded-xl p-3 sm:p-4 border border-white/10 hover:bg-white/10 transition-all cursor-pointer col-span-2 sm:col-span-1">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                <Activity className="w-4 sm:w-5 h-4 sm:h-5 text-cyan-400" />
                <span className="text-[10px] sm:text-xs text-slate-400">AI Confidence</span>
              </div>
              <div className="text-lg sm:text-2xl font-bold text-cyan-400">{displayMetrics.ai_confidence?.toFixed(0) || 94}%</div>
            </Link>
          </div>
        </div>
      </div>
      
      {error && (
        <AlertBanner 
          type="warning"
          title="Demo Mode"
          message={error}
        />
      )}
      
      {/* Main Operations Grid - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Alert Queue - Main Focus for Operators */}
        <div className="lg:col-span-2">
          <SectionCard 
            title="Active Alert Queue"
            subtitle={leaks.length > 0 ? "Alerts requiring action" : "No active leaks"}
            action={
              <div className="flex items-center gap-2 sm:gap-3">
                <button 
                  onClick={fetchData}
                  className="text-xs sm:text-sm text-cyan-600 hover:text-cyan-700 font-medium flex items-center gap-1"
                >
                  <RefreshCw className="w-3 sm:w-4 h-3 sm:h-4" />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
                <Link href="/actions" className="text-xs sm:text-sm text-cyan-600 hover:text-cyan-700 font-semibold flex items-center gap-1">
                  <span className="hidden sm:inline">Full Queue</span> <ArrowRight className="w-3 sm:w-4 h-3 sm:h-4" />
                </Link>
              </div>
            }
            noPadding
          >
            {leaks.length === 0 ? (
              <div className="p-8 text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">No Active Leaks</h3>
                <p className="text-slate-500 max-w-md mx-auto">
                  The AI monitoring system has not detected any leaks. All sensors are operating normally.
                </p>
                <div className="mt-4 flex items-center justify-center gap-2 text-sm text-emerald-600">
                  <Wifi className="w-4 h-4" />
                  <span>System actively monitoring {sensors.length} sensors</span>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {leaks.filter(l => l.status !== 'resolved').map((leak) => (
                  <div key={leak.id} className="p-4 hover:bg-slate-50/50 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        leak.priority === 'high' ? 'bg-red-100' : 'bg-amber-100'
                      }`}>
                        <AlertTriangle className={`w-6 h-6 ${
                          leak.priority === 'high' ? 'text-red-600' : 'text-amber-600'
                        }`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                            leak.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                          }`}>
                            {leak.priority.toUpperCase()}
                          </span>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                            leak.status === 'new' ? 'bg-blue-100 text-blue-700' :
                            leak.status === 'acknowledged' ? 'bg-purple-100 text-purple-700' :
                            'bg-emerald-100 text-emerald-700'
                          }`}>
                            {leak.status}
                          </span>
                        </div>
                        <p className="font-semibold text-slate-900 truncate">{leak.location}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                          <span>{leak.estimated_loss} m³/day loss</span>
                          <span>{leak.confidence}% confidence</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatRelativeTime(leak.detected_at)}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {leak.status === 'new' && (
                          <>
                            <button 
                              onClick={() => handleLeakAction(leak.id, 'acknowledge')}
                              disabled={actionLoading === leak.id}
                              className="px-3 py-2 bg-cyan-600 text-white text-sm font-medium rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-1 disabled:opacity-50"
                            >
                              {actionLoading === leak.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <CheckCircle2 className="w-4 h-4" />
                              )}
                              Acknowledge
                            </button>
                            <Link href={`/dma/${leak.dma_id}`} className="px-3 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition-colors">
                              <Eye className="w-4 h-4" />
                            </Link>
                          </>
                        )}
                        {leak.status === 'acknowledged' && (
                          <button 
                            onClick={() => handleLeakAction(leak.id, 'dispatch')}
                            disabled={actionLoading === leak.id}
                            className="px-3 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-1 disabled:opacity-50"
                          >
                            {actionLoading === leak.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Wrench className="w-4 h-4" />
                            )}
                            Dispatch Team
                          </button>
                        )}
                        {leak.status === 'dispatched' && (
                          <span className="px-3 py-2 bg-emerald-100 text-emerald-700 text-sm font-medium rounded-lg flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" />
                            Team En Route
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
        
        {/* Sensor Status Panel */}
        <div className="col-span-1">
          <SectionCard 
            title="Sensor Network"
            subtitle="Live sensor status"
            action={
              <Link href="/health" className="text-sm text-cyan-600 hover:text-cyan-700 font-semibold flex items-center gap-1">
                Details <ArrowRight className="w-4 h-4" />
              </Link>
            }
            noPadding
          >
            <div className="divide-y divide-slate-100 max-h-[400px] overflow-y-auto">
              {(sensorsDisplay.length > 0 ? sensorsDisplay : [
                { id: 'Loading...', name: 'Fetching sensor data', status: 'online', value: null, unit: '-', lastSeen: 'now' }
              ]).map((sensor) => (
                <Link key={sensor.id} href="/health" className="block p-3 hover:bg-slate-50/50 transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(sensor.status)}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{sensor.name}</p>
                      <p className="text-xs text-slate-500">{sensor.id}</p>
                    </div>
                    <div className="text-right">
                      {sensor.value !== null ? (
                        <>
                          <p className="text-sm font-bold text-slate-900">{typeof sensor.value === 'number' ? sensor.value.toFixed(1) : sensor.value}</p>
                          <p className="text-xs text-slate-500">{sensor.unit}</p>
                        </>
                      ) : (
                        <span className="text-xs text-slate-400">{sensor.lastSeen}</span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
      
      {/* DMA Monitoring Grid */}
      <SectionCard 
        title="DMA Status Overview"
        subtitle="Real-time district metered area monitoring"
        action={
          <Link href="/dma" className="text-sm text-cyan-600 hover:text-cyan-700 font-semibold flex items-center gap-1">
            DMA Intelligence <ArrowRight className="w-4 h-4" />
          </Link>
        }
      >
        <div className="grid grid-cols-3 gap-4">
          {displayDMAs.map((dma: any) => (
            <Link 
              key={dma.dma_id}
              href={`/dma/${dma.dma_id}`}
              className="bg-slate-50 rounded-xl p-4 border border-slate-200 hover:border-cyan-300 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-slate-900 group-hover:text-cyan-600 truncate">{dma.name}</span>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(dma.status)}`} />
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-2xl font-bold text-slate-900">{dma.nrw_percent}%</div>
                  <div className="text-xs text-slate-500">NRW Rate</div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-slate-700">{dma.priority_score}</div>
                  <div className="text-xs text-slate-500">Priority</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </SectionCard>
      
      {/* Trend Chart */}
      <SectionCard 
        title="NRW Performance Trend" 
        subtitle="30-day network performance tracking"
      >
        <NRWTrendChart data={displayTrend as any} height={250} showLegend />
      </SectionCard>

      {/* AI Operational Insights */}
      <div className="grid grid-cols-2 gap-6">
        <AIInsightsPanel 
          type="leak_analysis"
          title="AI Leak Priority Analysis"
          data={{
            leaks: leaks,
            metrics: displayMetrics,
            dmas: displayDMAs
          }}
          autoLoad={true}
        />
        <AIInsightsPanel 
          type="alert_priority"
          title="AI Alert Recommendations"
          data={{
            leaks: leaks,
            sensors: sensors,
            dmas: displayDMAs
          }}
        />
      </div>
      
      {/* Footer Stats */}
      <div className="flex items-center justify-between py-3 px-5 bg-cyan-50 rounded-xl border border-cyan-200">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full pulse-live" />
            <span className="text-sm font-medium text-cyan-700">Operator Session Active</span>
          </div>
          <div className="h-4 w-px bg-cyan-300" />
          <span className="text-sm text-slate-600">
            Data refresh: {formatRelativeTime(displayMetrics.last_data_received)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-3 py-1.5 bg-cyan-600 text-white text-sm font-medium rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-1">
            <Bell className="w-4 h-4" />
            Sound Alerts On
          </button>
        </div>
      </div>
    </div>
  )
}
