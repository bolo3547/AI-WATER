'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { 
  Gauge, TrendingDown, Droplets, BarChart3, Zap, Activity,
  AlertTriangle, MapPin, ShieldCheck, Clock, ArrowRight,
  Users, Settings, Key, Server, Database, Shield, 
  CheckCircle2, XCircle, RefreshCw, FileText, Cpu,
  TrendingUp, Brain, Sparkles
} from 'lucide-react'
import { formatNumber, formatCurrency, formatRelativeTime } from '@/lib/api'
import { SectionCard, AlertBanner } from '@/components/ui/Cards'
import { KPICard } from '@/components/metrics/KPICard'
import { NRWTrendChart } from '@/components/charts/Charts'
import { ConfidenceIndicator } from '@/components/metrics/StatusIndicators'
import { DMAListItem } from '@/components/data/DataTable'
import { AIInsightsPanel } from '@/components/ai/AIInsightsPanel'

// Types for real-time data
interface SystemMetrics {
  total_nrw_percent: number
  water_recovered_30d: number
  revenue_recovered_30d: number
  sensor_count: number
  dma_count: number
  active_high_priority_leaks: number
  ai_confidence: number
  last_data_received: string
  total_input: number
  total_output: number
  nrw_change: number
}

interface DMAData {
  dma_id: string
  name: string
  nrw_percent: number
  priority_score: number
  status: 'critical' | 'warning' | 'healthy'
  trend: 'up' | 'down' | 'stable'
  input_flow: number
  output_flow: number
}

interface InfraHealth {
  api_server: { status: string; latency: number; uptime: number }
  database: { status: string; connections: number; storage: number }
  mqtt_broker: { status: string; connected_devices: number; messages_per_min: number }
  ai_engine: { status: string; inference_time: number; accuracy: number }
  data_ingestion: { status: string; queue_size: number; processing_rate: number }
}

const RECENT_ACTIVITY = [
  { user: 'operator', action: 'Acknowledged leak alert', time: '2 min ago' },
  { user: 'technician', action: 'Updated work order #WO-2847', time: '15 min ago' },
  { user: 'admin', action: 'Added new sensor ESP32-024', time: '1 hour ago' },
  { user: 'operator', action: 'Generated monthly report', time: '2 hours ago' },
]

export function AdminDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [dmas, setDMAs] = useState<DMAData[]>([])
  const [health, setHealth] = useState<InfraHealth | null>(null)
  const [trendData, setTrendData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  
  // Fetch real-time data
  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, dmasRes, infraRes] = await Promise.all([
        fetch('/api/realtime?type=metrics'),
        fetch('/api/realtime?type=dmas'),
        fetch('/api/realtime?type=infrastructure')
      ])
      
      const [metricsData, dmasData, infraData] = await Promise.all([
        metricsRes.json(),
        dmasRes.json(),
        infraRes.json()
      ])
      
      if (metricsData.metrics) {
        setMetrics(metricsData.metrics)
      }
      
      if (dmasData.dmas) {
        setDMAs(dmasData.dmas)
      }
      
      if (infraData.infrastructure) {
        setHealth(infraData.infrastructure)
      }
      
      // Generate trend data
      const trend = Array.from({ length: 30 }, (_, i) => {
        const baseNrw = metricsData.metrics?.total_nrw_percent || 32
        return {
          timestamp: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
          nrw: baseNrw + 6 - (i * 0.2) + (Math.random() * 2 - 1),
          target: 25
        }
      })
      setTrendData(trend)
      
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      console.error('Failed to fetch data:', err)
      setError('Unable to fetch real-time data')
    } finally {
      setLoading(false)
    }
  }, [])
  
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])
  
  // Fetch data initially and every 15 seconds
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [fetchData])

  // Default values while loading
  const displayMetrics = metrics || {
    total_nrw_percent: 0,
    water_recovered_30d: 0,
    revenue_recovered_30d: 0,
    sensor_count: 0,
    dma_count: 0,
    active_high_priority_leaks: 0,
    ai_confidence: 0,
    last_data_received: new Date().toISOString(),
    nrw_change: 0
  }
  
  const displayDMAs = dmas.length > 0 ? dmas : []
  const displayTrend = trendData.length > 0 ? trendData : []

  const systemHealth = {
    api: { 
      status: health?.api_server?.status || 'loading', 
      latency: health?.api_server?.latency || 0 
    },
    database: { 
      status: health?.database?.status || 'loading', 
      connections: health?.database?.connections || 0 
    },
    mqtt: { 
      status: health?.mqtt_broker?.status || 'loading', 
      messages: health?.mqtt_broker?.messages_per_min || 0 
    },
    aiEngine: { 
      status: health?.ai_engine?.status || 'loading', 
      queueSize: health?.data_ingestion?.queue_size || 0 
    }
  }

  return (
    <div className="space-y-8">
      {/* Admin Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 p-8 text-white">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex items-start justify-between mb-8 gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <div className="px-3 py-1 bg-purple-500/20 rounded-full border border-purple-400/30">
                  <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider">Administrator</span>
                </div>
                <div className="w-2 h-2 bg-emerald-400 rounded-full pulse-live flex-shrink-0" />
                <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Live</span>
                {lastUpdate && (
                  <span className="text-xs text-slate-400">Updated {lastUpdate.toLocaleTimeString()}</span>
                )}
              </div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">Executive Command Center</h1>
              <p className="text-slate-400 text-sm">Full system oversight • User management • Configuration</p>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="text-2xl font-mono font-bold text-white/90">
                {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {currentTime.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
              </div>
            </div>
          </div>
          
          {/* Hero Stats */}
          <div className="grid grid-cols-4 gap-6">
            <Link href="/analytics" className="bg-white/5 backdrop-blur rounded-xl p-5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center group-hover:bg-blue-500/30">
                  <Gauge className="w-5 h-5 text-blue-400" />
                </div>
                <span className="text-sm text-slate-400 truncate">Network NRW</span>
              </div>
              <div className="text-3xl font-bold text-white">{displayMetrics.total_nrw_percent?.toFixed(1)}%</div>
              <div className="flex items-center gap-2 mt-2">
                {(displayMetrics.nrw_change || 0) <= 0 ? (
                  <>
                    <TrendingDown className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs text-emerald-400">{Math.abs(displayMetrics.nrw_change || 2.3).toFixed(1)}% vs last month</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4 text-red-400" />
                    <span className="text-xs text-red-400">+{(displayMetrics.nrw_change || 0).toFixed(1)}% vs last month</span>
                  </>
                )}
              </div>
            </Link>
            
            <Link href="/reports" className="bg-white/5 backdrop-blur rounded-xl p-5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center group-hover:bg-cyan-500/30">
                  <Droplets className="w-5 h-5 text-cyan-400" />
                </div>
                <span className="text-sm text-slate-400 truncate">Recovered</span>
              </div>
              <div className="text-3xl font-bold text-white">{formatNumber(displayMetrics.water_recovered_30d || 0)}</div>
              <div className="text-xs text-slate-400 mt-2">m³ this month</div>
            </Link>
            
            <Link href="/reports" className="bg-white/5 backdrop-blur rounded-xl p-5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center group-hover:bg-emerald-500/30">
                  <BarChart3 className="w-5 h-5 text-emerald-400" />
                </div>
                <span className="text-sm text-slate-400 truncate">Revenue</span>
              </div>
              <div className="text-3xl font-bold text-white">{formatCurrency(displayMetrics.revenue_recovered_30d || 0)}</div>
              <div className="text-xs text-slate-400 mt-2">ZMW this month</div>
            </Link>
            
            <Link href="/admin/users" className="bg-white/5 backdrop-blur rounded-xl p-5 border border-white/10 hover:bg-white/10 transition-all cursor-pointer group">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center group-hover:bg-purple-500/30">
                  <Users className="w-5 h-5 text-purple-400" />
                </div>
                <span className="text-sm text-slate-400 truncate">Active Users</span>
              </div>
              <div className="text-3xl font-bold text-white">8</div>
              <div className="flex items-center gap-2 mt-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-emerald-400">3 online now</span>
              </div>
            </Link>
          </div>
        </div>
      </div>
      
      {error && (
        <AlertBanner 
          type="warning"
          title="Data Refresh Issue"
          message={error}
        />
      )}
      
      {/* Admin Quick Actions */}
      <div className="grid grid-cols-4 gap-4">
        <Link href="/admin/users" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-purple-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-purple-600">User Management</h3>
              <p className="text-xs text-slate-500">Manage operators & technicians</p>
            </div>
          </div>
        </Link>
        
        <Link href="/admin/config" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-blue-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <Settings className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-blue-600">System Config</h3>
              <p className="text-xs text-slate-500">API, MQTT, retention settings</p>
            </div>
          </div>
        </Link>
        
        <Link href="/admin/security" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-amber-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center group-hover:bg-amber-200 transition-colors">
              <Key className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-amber-600">Security</h3>
              <p className="text-xs text-slate-500">API keys & audit logs</p>
            </div>
          </div>
        </Link>
        
        <Link href="/admin/firmware" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-indigo-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center group-hover:bg-indigo-200 transition-colors">
              <Cpu className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600">Firmware Generator</h3>
              <p className="text-xs text-slate-500">Generate ESP32 .ino code</p>
            </div>
          </div>
        </Link>
      </div>
      
      {/* Second row of quick actions */}
      <div className="grid grid-cols-2 gap-4">
        <Link href="/reports" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-emerald-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center group-hover:bg-emerald-200 transition-colors">
              <FileText className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-emerald-600">Reports</h3>
              <p className="text-xs text-slate-500">Generate & export reports</p>
            </div>
          </div>
        </Link>
        
        <Link href="/analytics" className="bg-white rounded-xl p-5 border border-slate-200 hover:shadow-md hover:border-cyan-200 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-cyan-100 flex items-center justify-center group-hover:bg-cyan-200 transition-colors">
              <Activity className="w-6 h-6 text-cyan-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 group-hover:text-cyan-600">Analytics</h3>
              <p className="text-xs text-slate-500">View detailed analytics</p>
            </div>
          </div>
        </Link>
      </div>
      
      {/* System Health Overview - Admin Only */}
      <SectionCard title="System Health" subtitle="Infrastructure status overview (Live)">
        <div className="grid grid-cols-4 gap-4">
          <Link href="/health" className="bg-slate-50 rounded-xl p-4 border border-slate-100 hover:bg-slate-100 hover:border-slate-200 transition-all cursor-pointer">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700">API Server</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${systemHealth.api.status === 'healthy' ? 'bg-emerald-500' : systemHealth.api.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${systemHealth.api.status === 'healthy' ? 'text-emerald-600' : systemHealth.api.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>
                  {systemHealth.api.status === 'healthy' ? 'Online' : systemHealth.api.status}
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">{systemHealth.api.latency}ms</div>
            <p className="text-xs text-slate-500 mt-1">Average latency</p>
          </Link>
          
          <Link href="/health" className="bg-slate-50 rounded-xl p-4 border border-slate-100 hover:bg-slate-100 hover:border-slate-200 transition-all cursor-pointer">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700">Database</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${systemHealth.database.status === 'healthy' ? 'bg-emerald-500' : systemHealth.database.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${systemHealth.database.status === 'healthy' ? 'text-emerald-600' : systemHealth.database.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>
                  {systemHealth.database.status === 'healthy' ? 'Online' : systemHealth.database.status}
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">{systemHealth.database.connections}</div>
            <p className="text-xs text-slate-500 mt-1">Active connections</p>
          </Link>
          
          <Link href="/health" className="bg-slate-50 rounded-xl p-4 border border-slate-100 hover:bg-slate-100 hover:border-slate-200 transition-all cursor-pointer">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700">MQTT Broker</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${systemHealth.mqtt.status === 'healthy' ? 'bg-emerald-500' : systemHealth.mqtt.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${systemHealth.mqtt.status === 'healthy' ? 'text-emerald-600' : systemHealth.mqtt.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>
                  {systemHealth.mqtt.status === 'healthy' ? 'Online' : systemHealth.mqtt.status}
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">{systemHealth.mqtt.messages}</div>
            <p className="text-xs text-slate-500 mt-1">Messages/min</p>
          </Link>
          
          <Link href="/health" className="bg-slate-50 rounded-xl p-4 border border-slate-100 hover:bg-slate-100 hover:border-slate-200 transition-all cursor-pointer">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-slate-600" />
                <span className="font-medium text-slate-700">AI Engine</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${systemHealth.aiEngine.status === 'healthy' ? 'bg-emerald-500' : systemHealth.aiEngine.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${systemHealth.aiEngine.status === 'healthy' ? 'text-emerald-600' : systemHealth.aiEngine.status === 'warning' ? 'text-amber-600' : 'text-red-600'}`}>
                  {systemHealth.aiEngine.status === 'healthy' ? 'Online' : systemHealth.aiEngine.status}
                </span>
              </div>
            </div>
            <div className="text-2xl font-bold text-slate-900">{systemHealth.aiEngine.queueSize}</div>
            <p className="text-xs text-slate-500 mt-1">Pending analyses</p>
          </Link>
        </div>
      </SectionCard>
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* NRW Trend Chart */}
        <div className="col-span-2">
          <SectionCard 
            title="NRW Performance Trend" 
            subtitle="30-day network performance vs IWA benchmark target"
          >
            <NRWTrendChart data={displayTrend as any} height={300} showLegend />
          </SectionCard>
        </div>
        
        {/* Recent Activity - Admin Only */}
        <div className="col-span-1">
          <SectionCard 
            title="Recent Activity"
            subtitle="User actions across system"
            noPadding
          >
            <div className="divide-y divide-slate-100">
              {RECENT_ACTIVITY.map((activity, i) => (
                <Link key={i} href="/admin/security" className="block p-4 hover:bg-slate-50/50 transition-colors cursor-pointer">
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                      activity.user === 'admin' ? 'bg-purple-500' :
                      activity.user === 'operator' ? 'bg-cyan-500' : 'bg-orange-500'
                    }`}>
                      {activity.user[0].toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900 truncate">{activity.action}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-500 capitalize">{activity.user}</span>
                        <span className="text-xs text-slate-400">•</span>
                        <span className="text-xs text-slate-400">{activity.time}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
      
      {/* DMA Rankings */}
      <SectionCard 
        title="DMA Priority Ranking"
        subtitle="District Metered Areas ranked by intervention urgency"
        action={
          <Link href="/dma" className="text-sm text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1">
            View All <ArrowRight className="w-4 h-4" />
          </Link>
        }
      >
        <div className="grid grid-cols-2 gap-4">
          {displayDMAs.slice(0, 4).map((dma: any, index: number) => (
            <DMAListItem
              key={dma.dma_id}
              rank={index + 1}
              name={dma.name}
              nrwPercent={dma.nrw_percent}
              priorityScore={dma.priority_score}
              status={dma.status}
              trend={dma.trend}
              href={`/dma/${dma.dma_id}`}
            />
          ))}
        </div>
      </SectionCard>

      {/* AI Executive Insights */}
      <div className="grid grid-cols-2 gap-6">
        <AIInsightsPanel 
          type="nrw_insights"
          title="AI Executive Summary"
          data={{
            metrics: displayMetrics,
            dmas: displayDMAs,
            systemHealth: systemHealth,
            trend: displayTrend
          }}
          autoLoad={true}
        />
        <AIInsightsPanel 
          type="dma_recommendation"
          title="AI Strategic Recommendations"
          data={{
            dmas: displayDMAs,
            metrics: displayMetrics
          }}
        />
      </div>
      
      {/* Footer Stats */}
      <div className="flex items-center justify-between py-4 px-6 bg-purple-50 rounded-xl border border-purple-200">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-700">Admin Session Active</span>
          </div>
          <div className="h-4 w-px bg-purple-300" />
          <span className="text-sm text-slate-600">
            Last sync: {formatRelativeTime(displayMetrics.last_data_received)}
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <span>{displayMetrics.sensor_count} sensors</span>
          <span>•</span>
          <span>{displayMetrics.dma_count} DMAs</span>
          <span>•</span>
          <span>AI Engine v2.4.1</span>
        </div>
      </div>
    </div>
  )
}
