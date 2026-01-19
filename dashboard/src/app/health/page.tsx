'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  Server, 
  Database, 
  Cpu, 
  Wifi, 
  Radio,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Activity,
  RefreshCw,
  Loader2
} from 'lucide-react'
import { SectionCard, AlertBanner } from '@/components/ui/Cards'
import { Button } from '@/components/ui/Controls'
import { StatusBadge, ConfidenceIndicator } from '@/components/metrics/StatusIndicators'
import { formatRelativeTime } from '@/lib/api'

// Types for real-time data
interface InfrastructureComponent {
  status: 'healthy' | 'warning' | 'critical'
  latency?: number
  uptime?: number
  connections?: number
  storage?: number
  model_version?: string
  inference_time?: number
  accuracy?: number
  connected_devices?: number
  messages_per_min?: number
  queue_size?: number
  processing_rate?: number
  last_check: string
}

interface Sensor {
  id: string
  name: string
  status: 'healthy' | 'warning' | 'critical'
  battery: number
  signal: number
  last_reading: string
  flow_rate?: number
  pressure?: number
  temperature?: number
}

interface SystemAlert {
  id: number
  type: 'critical' | 'warning' | 'info' | 'success'
  message: string
  time: string
}

interface AIEngineData {
  model_version: string
  accuracy: number
  inference_time: number
  training_samples: number
  last_retrained: string
  deployed_at: string
  methods_active: string[]
}

export default function SystemHealthPage() {
  const [components, setComponents] = useState<Record<string, InfrastructureComponent>>({})
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [alerts, setAlerts] = useState<SystemAlert[]>([])
  const [aiEngine, setAIEngine] = useState<AIEngineData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  // Fetch real-time data
  const fetchData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true)
    
    try {
      const [infraRes, sensorsRes] = await Promise.all([
        fetch('/api/realtime?type=infrastructure'),
        fetch('/api/realtime?type=sensors')
      ])
      
      const infraData = await infraRes.json()
      const sensorsData = await sensorsRes.json()
      
      if (infraData.infrastructure) {
        setComponents(infraData.infrastructure)
        
        // Extract AI engine data
        if (infraData.infrastructure.ai_engine) {
          const ai = infraData.infrastructure.ai_engine
          setAIEngine({
            model_version: ai.model_version || 'v2.4.1',
            accuracy: ai.accuracy || 94.2,
            inference_time: ai.inference_time || 120,
            training_samples: 2400000,
            last_retrained: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            deployed_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
            methods_active: ['Flow Analysis', 'Night Flow Detection', 'Acoustic Analysis', 'Pressure Transients']
          })
        }
      }
      
      if (sensorsData.sensors) {
        setSensors(sensorsData.sensors)
        
        // Generate alerts based on sensor data
        const newAlerts: SystemAlert[] = []
        let alertId = 1
        
        sensorsData.sensors.forEach((sensor: Sensor) => {
          if (sensor.battery < 20) {
            newAlerts.push({
              id: alertId++,
              type: sensor.battery < 10 ? 'critical' : 'warning',
              message: `Sensor ${sensor.id} battery low (${sensor.battery}%) - schedule replacement`,
              time: new Date().toISOString()
            })
          }
          if (sensor.status === 'critical') {
            newAlerts.push({
              id: alertId++,
              type: 'critical',
              message: `Sensor ${sensor.id} offline - no recent data received`,
              time: sensor.last_reading
            })
          }
          if (sensor.signal < 50) {
            newAlerts.push({
              id: alertId++,
              type: 'warning',
              message: `Sensor ${sensor.id} weak signal (${sensor.signal}%) - check connectivity`,
              time: new Date().toISOString()
            })
          }
        })
        
        // Add infrastructure alerts
        Object.entries(infraData.infrastructure || {}).forEach(([name, comp]: [string, any]) => {
          if (comp.status === 'warning') {
            newAlerts.push({
              id: alertId++,
              type: 'warning',
              message: `${name.replace(/_/g, ' ')} - performance degraded`,
              time: comp.last_check
            })
          }
        })
        
        // Add success message if system is healthy
        if (newAlerts.filter(a => a.type === 'critical').length === 0) {
          newAlerts.push({
            id: alertId++,
            type: 'success',
            message: 'All critical systems operational',
            time: new Date().toISOString()
          })
        }
        
        setAlerts(newAlerts)
      }
      
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Failed to fetch real-time data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // Initial fetch and auto-refresh every 10 seconds
  useEffect(() => {
    fetchData()
    const interval = setInterval(() => fetchData(), 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  const refreshStatus = () => fetchData(true)
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-status-green" />
      case 'warning': return <AlertTriangle className="w-5 h-5 text-status-amber" />
      case 'critical': return <XCircle className="w-5 h-5 text-status-red" />
      default: return <Clock className="w-5 h-5 text-text-tertiary" />
    }
  }
  
  const getComponentIcon = (name: string) => {
    switch (name) {
      case 'api_server': return Server
      case 'database': return Database
      case 'ai_engine': return Cpu
      case 'mqtt_broker': return Wifi
      case 'data_ingestion': return Activity
      default: return Server
    }
  }
  
  const healthyComponents = Object.values(components).filter(c => c.status === 'healthy').length
  const totalComponents = Object.keys(components).length
  const healthySensors = sensors.filter(s => s.status === 'healthy').length
  const totalSensors = sensors.length
  
  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary-500 mx-auto" />
          <p className="text-text-secondary mt-4">Loading system health data...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display font-bold text-text-primary">System Health</h1>
          <p className="text-body text-text-secondary mt-1">
            Infrastructure status, sensor network, and AI engine monitoring
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-caption text-text-tertiary">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-status-green animate-pulse" />
            <span className="text-caption text-status-green">Live</span>
          </div>
          <Button variant="secondary" onClick={refreshStatus} disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh Status'}
          </Button>
        </div>
      </div>
      
      {/* Overall Health Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-label text-text-tertiary uppercase">System Status</p>
              <p className="text-heading font-bold text-status-green mt-1">Operational</p>
            </div>
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-status-green" />
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-label text-text-tertiary uppercase">Components</p>
              <p className="text-heading font-bold text-text-primary mt-1">{healthyComponents}/{totalComponents} Healthy</p>
            </div>
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Server className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-label text-text-tertiary uppercase">Sensors Online</p>
              <p className="text-heading font-bold text-text-primary mt-1">{healthySensors}/{totalSensors}</p>
            </div>
            <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
              <Radio className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-label text-text-tertiary uppercase">AI Engine</p>
              <p className="text-heading font-bold text-status-green mt-1">Active</p>
            </div>
            <ConfidenceIndicator value={94} showLabel />
          </div>
        </div>
      </div>
      
      {/* Active Alerts */}
      {alerts.filter(a => a.type === 'critical' || a.type === 'warning').length > 0 && (
        <div className="space-y-3">
          {alerts.filter(a => a.type === 'critical').map(alert => (
            <AlertBanner
              key={alert.id}
              type="error"
              title={alert.message}
              message={formatRelativeTime(alert.time)}
              action={<Button variant="secondary" size="sm">Acknowledge</Button>}
            />
          ))}
          {alerts.filter(a => a.type === 'warning').map(alert => (
            <AlertBanner
              key={alert.id}
              type="warning"
              title={alert.message}
              message={formatRelativeTime(alert.time)}
              action={<Button variant="ghost" size="sm">Dismiss</Button>}
            />
          ))}
        </div>
      )}
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Infrastructure Components */}
        <SectionCard title="Infrastructure Components" subtitle="Core system services status">
          <div className="space-y-4">
            {Object.entries(components).map(([name, component]) => {
              const Icon = getComponentIcon(name)
              const displayName = name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
              
              return (
                <div key={name} className="flex items-center gap-4 p-3 rounded-lg bg-surface-secondary">
                  <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center border border-surface-border">
                    <Icon className="w-5 h-5 text-text-secondary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-body font-medium text-text-primary">{displayName}</h4>
                      {getStatusIcon(component.status)}
                    </div>
                    <p className="text-caption text-text-tertiary">
                      {name === 'api_server' && component.latency !== undefined && `Latency: ${component.latency}ms • Uptime: ${component.uptime?.toFixed(2)}%`}
                      {name === 'database' && component.connections !== undefined && `Connections: ${component.connections} • Storage: ${component.storage?.toFixed(1)}%`}
                      {name === 'ai_engine' && component.model_version && `Version: ${component.model_version} • Inference: ${component.inference_time}ms`}
                      {name === 'mqtt_broker' && component.connected_devices !== undefined && `Devices: ${component.connected_devices} • ${component.messages_per_min} msg/min`}
                      {name === 'data_ingestion' && component.queue_size !== undefined && `Queue: ${component.queue_size} • Rate: ${component.processing_rate}/min`}
                    </p>
                  </div>
                  <p className="text-label text-text-tertiary">
                    {formatRelativeTime(component.last_check)}
                  </p>
                </div>
              )
            })}
          </div>
        </SectionCard>
        
        {/* Sensor Network */}
        <SectionCard title="Sensor Network" subtitle="IoT device status and connectivity" noPadding>
          <div className="max-h-[400px] overflow-y-auto">
            <table className="w-full">
              <thead className="bg-surface-secondary sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-label font-semibold text-text-secondary uppercase">Sensor</th>
                  <th className="px-4 py-3 text-left text-label font-semibold text-text-secondary uppercase">Status</th>
                  <th className="px-4 py-3 text-center text-label font-semibold text-text-secondary uppercase">Battery</th>
                  <th className="px-4 py-3 text-center text-label font-semibold text-text-secondary uppercase">Signal</th>
                  <th className="px-4 py-3 text-right text-label font-semibold text-text-secondary uppercase">Last Reading</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {sensors.map(sensor => (
                  <tr key={sensor.id} className="hover:bg-surface-secondary">
                    <td className="px-4 py-3">
                      <p className="text-body font-medium text-text-primary">{sensor.id}</p>
                      <p className="text-caption text-text-tertiary">{sensor.name}</p>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sensor.status as any} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-body font-medium ${
                        sensor.battery < 20 ? 'text-status-red' : 
                        sensor.battery < 50 ? 'text-status-amber' : 
                        'text-text-primary'
                      }`}>
                        {sensor.battery}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-body font-medium ${
                        sensor.signal < 50 ? 'text-status-red' : 
                        sensor.signal < 70 ? 'text-status-amber' : 
                        'text-text-primary'
                      }`}>
                        {sensor.signal}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-caption text-text-tertiary">
                        {formatRelativeTime(sensor.last_reading)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>
      
      {/* AI Engine Details */}
      <SectionCard title="AI Engine Status" subtitle="Machine learning model performance and metrics">
        <div className="grid grid-cols-4 gap-6">
          <div>
            <p className="text-label text-text-tertiary uppercase mb-1">Model Version</p>
            <p className="text-body font-semibold text-text-primary">{aiEngine?.model_version || 'v2.4.1'}</p>
            <p className="text-caption text-text-tertiary">Deployed {aiEngine ? formatRelativeTime(aiEngine.deployed_at) : '3 days ago'}</p>
          </div>
          <div>
            <p className="text-label text-text-tertiary uppercase mb-1">Detection Accuracy</p>
            <p className="text-body font-semibold text-status-green">{aiEngine?.accuracy?.toFixed(1) || '94.2'}%</p>
            <p className="text-caption text-text-tertiary">Based on validated detections</p>
          </div>
          <div>
            <p className="text-label text-text-tertiary uppercase mb-1">Avg Inference Time</p>
            <p className="text-body font-semibold text-text-primary">{aiEngine?.inference_time || 120}ms</p>
            <p className="text-caption text-text-tertiary">Per detection cycle</p>
          </div>
          <div>
            <p className="text-label text-text-tertiary uppercase mb-1">Training Data</p>
            <p className="text-body font-semibold text-text-primary">{((aiEngine?.training_samples || 2400000) / 1000000).toFixed(1)}M samples</p>
            <p className="text-caption text-text-tertiary">Last retrained: {aiEngine ? formatRelativeTime(aiEngine.last_retrained) : '7 days ago'}</p>
          </div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-surface-border">
          <h4 className="text-body font-semibold text-text-primary mb-3">Detection Methods Active</h4>
          <div className="grid grid-cols-4 gap-4">
            {(aiEngine?.methods_active || ['Flow Analysis', 'Night Flow Detection', 'Acoustic Analysis', 'Pressure Transients']).map(method => (
              <div key={method} className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-status-green" />
                <span className="text-caption text-text-secondary">{method}</span>
              </div>
            ))}
          </div>
        </div>
      </SectionCard>
      
      {/* Recent Activity Log */}
      <SectionCard title="System Activity Log" subtitle="Recent events and notifications">
        <div className="space-y-3">
          {alerts.map(alert => (
            <div key={alert.id} className="flex items-start gap-3 py-2">
              <div className={`w-2 h-2 rounded-full mt-1.5 ${
                alert.type === 'critical' ? 'bg-status-red' :
                alert.type === 'warning' ? 'bg-status-amber' :
                alert.type === 'success' ? 'bg-status-green' :
                'bg-primary-500'
              }`} />
              <div className="flex-1">
                <p className="text-body text-text-primary">{alert.message}</p>
                <p className="text-caption text-text-tertiary">{formatRelativeTime(alert.time)}</p>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  )
}
