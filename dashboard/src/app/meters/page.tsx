'use client'

import { useState, useEffect } from 'react'
import { 
  Gauge, Activity, AlertTriangle, CheckCircle, Clock,
  Signal, Battery, Wifi, WifiOff, RefreshCw, Download,
  TrendingUp, TrendingDown, BarChart3, Zap, Settings,
  MapPin, Filter, Search, ChevronRight, Bell, Eye
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface SmartMeter {
  id: string
  accountNumber: string
  customerName: string
  location: string
  dma: string
  meterType: 'ultrasonic' | 'electromagnetic' | 'mechanical' | 'amr'
  status: 'online' | 'offline' | 'warning' | 'tampered'
  lastReading: number
  previousReading: number
  consumption: number
  avgConsumption: number
  battery: number
  signalStrength: number
  lastContact: string
  alerts: string[]
  anomalyScore: number
  coordinates: { lat: number; lng: number }
}

interface ConsumptionAnomaly {
  meterId: string
  accountNumber: string
  customerName: string
  anomalyType: 'sudden_increase' | 'sudden_decrease' | 'zero_consumption' | 'reverse_flow' | 'tampering'
  severity: 'critical' | 'high' | 'medium' | 'low'
  detectedAt: string
  currentConsumption: number
  expectedConsumption: number
  deviation: number
  status: 'new' | 'investigating' | 'resolved'
}

export default function SmartMeterPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [meters, setMeters] = useState<SmartMeter[]>([])
  const [anomalies, setAnomalies] = useState<ConsumptionAnomaly[]>([])
  const [selectedMeter, setSelectedMeter] = useState<SmartMeter | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterDMA, setFilterDMA] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadData()
    // Simulate real-time updates
    const interval = setInterval(updateMeterReadings, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadData = () => {
    setIsLoading(true)
    setTimeout(() => {
      setMeters([
        {
          id: 'MTR-001',
          accountNumber: 'ACC-KAB-12345',
          customerName: 'Mwamba Enterprises',
          location: 'Plot 5, Kabulonga Rd',
          dma: 'Kabulonga',
          meterType: 'ultrasonic',
          status: 'online',
          lastReading: 15234.5,
          previousReading: 15180.2,
          consumption: 54.3,
          avgConsumption: 48.5,
          battery: 92,
          signalStrength: 4,
          lastContact: '2 min ago',
          alerts: [],
          anomalyScore: 12,
          coordinates: { lat: -15.4192, lng: 28.3225 }
        },
        {
          id: 'MTR-002',
          accountNumber: 'ACC-ROM-23456',
          customerName: 'Roma Shopping Complex',
          location: 'Roma Main Road',
          dma: 'Roma',
          meterType: 'electromagnetic',
          status: 'warning',
          lastReading: 89456.8,
          previousReading: 88890.2,
          consumption: 566.6,
          avgConsumption: 420.0,
          battery: 78,
          signalStrength: 3,
          lastContact: '15 min ago',
          alerts: ['High consumption detected'],
          anomalyScore: 68,
          coordinates: { lat: -15.3958, lng: 28.3108 }
        },
        {
          id: 'MTR-003',
          accountNumber: 'ACC-CHE-34567',
          customerName: 'Chelstone Primary School',
          location: 'Off Chelstone Main',
          dma: 'Chelstone',
          meterType: 'amr',
          status: 'online',
          lastReading: 45678.2,
          previousReading: 45650.8,
          consumption: 27.4,
          avgConsumption: 32.0,
          battery: 85,
          signalStrength: 5,
          lastContact: '5 min ago',
          alerts: [],
          anomalyScore: 8,
          coordinates: { lat: -15.3605, lng: 28.3517 }
        },
        {
          id: 'MTR-004',
          accountNumber: 'ACC-MAT-45678',
          customerName: 'Matero Industrial Ltd',
          location: 'Industrial Zone Block A',
          dma: 'Matero',
          meterType: 'electromagnetic',
          status: 'tampered',
          lastReading: 234567.0,
          previousReading: 234800.5,
          consumption: -233.5,
          avgConsumption: 850.0,
          battery: 45,
          signalStrength: 2,
          lastContact: '2 hours ago',
          alerts: ['Reverse flow detected', 'Possible tampering'],
          anomalyScore: 95,
          coordinates: { lat: -15.3747, lng: 28.2633 }
        },
        {
          id: 'MTR-005',
          accountNumber: 'ACC-WDL-56789',
          customerName: 'Woodlands Residence 42',
          location: '42 Woodlands Close',
          dma: 'Woodlands',
          meterType: 'mechanical',
          status: 'offline',
          lastReading: 1234.6,
          previousReading: 1234.6,
          consumption: 0,
          avgConsumption: 12.5,
          battery: 5,
          signalStrength: 0,
          lastContact: '3 days ago',
          alerts: ['No communication', 'Battery critical'],
          anomalyScore: 78,
          coordinates: { lat: -15.4134, lng: 28.3064 }
        },
        {
          id: 'MTR-006',
          accountNumber: 'ACC-CHI-67890',
          customerName: 'Chilenje Health Center',
          location: 'Chilenje South',
          dma: 'Chilenje',
          meterType: 'ultrasonic',
          status: 'online',
          lastReading: 78901.3,
          previousReading: 78845.7,
          consumption: 55.6,
          avgConsumption: 52.0,
          battery: 88,
          signalStrength: 4,
          lastContact: '1 min ago',
          alerts: [],
          anomalyScore: 5,
          coordinates: { lat: -15.4433, lng: 28.2925 }
        }
      ])

      setAnomalies([
        {
          meterId: 'MTR-004',
          accountNumber: 'ACC-MAT-45678',
          customerName: 'Matero Industrial Ltd',
          anomalyType: 'reverse_flow',
          severity: 'critical',
          detectedAt: '2026-01-29 08:15',
          currentConsumption: -233.5,
          expectedConsumption: 850.0,
          deviation: -127,
          status: 'new'
        },
        {
          meterId: 'MTR-002',
          accountNumber: 'ACC-ROM-23456',
          customerName: 'Roma Shopping Complex',
          anomalyType: 'sudden_increase',
          severity: 'high',
          detectedAt: '2026-01-29 06:30',
          currentConsumption: 566.6,
          expectedConsumption: 420.0,
          deviation: 35,
          status: 'investigating'
        },
        {
          meterId: 'MTR-005',
          accountNumber: 'ACC-WDL-56789',
          customerName: 'Woodlands Residence 42',
          anomalyType: 'zero_consumption',
          severity: 'medium',
          detectedAt: '2026-01-26 14:00',
          currentConsumption: 0,
          expectedConsumption: 12.5,
          deviation: -100,
          status: 'new'
        }
      ])

      setIsLoading(false)
    }, 1500)
  }

  const updateMeterReadings = () => {
    setMeters(prev => prev.map(meter => ({
      ...meter,
      lastContact: meter.status === 'online' ? 'Just now' : meter.lastContact
    })))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-500'
      case 'offline': return 'bg-gray-400'
      case 'warning': return 'bg-yellow-500'
      case 'tampered': return 'bg-red-500 animate-pulse'
      default: return 'bg-gray-500'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-700'
      case 'offline': return 'bg-gray-100 text-gray-700'
      case 'warning': return 'bg-yellow-100 text-yellow-700'
      case 'tampered': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const filteredMeters = meters.filter(m => {
    if (searchQuery && !m.customerName.toLowerCase().includes(searchQuery.toLowerCase()) && 
        !m.accountNumber.toLowerCase().includes(searchQuery.toLowerCase())) return false
    if (filterStatus && m.status !== filterStatus) return false
    if (filterDMA && m.dma !== filterDMA) return false
    return true
  })

  const stats = {
    total: meters.length,
    online: meters.filter(m => m.status === 'online').length,
    offline: meters.filter(m => m.status === 'offline').length,
    warning: meters.filter(m => m.status === 'warning').length,
    tampered: meters.filter(m => m.status === 'tampered').length,
    totalConsumption: meters.reduce((sum, m) => sum + (m.consumption > 0 ? m.consumption : 0), 0),
    anomalies: anomalies.filter(a => a.status === 'new').length
  }

  const uniqueDMAs = [...new Set(meters.map(m => m.dma))]

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Gauge className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />
            Smart Meter Integration
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AMR/AMI meter monitoring and consumption analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={loadData} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Sync</span>
          </Button>
          <Button variant="primary">
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 sm:gap-3">
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <Gauge className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-lg font-bold text-slate-900">{stats.total}</p>
              <p className="text-[10px] text-slate-500">Total Meters</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <Wifi className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-lg font-bold text-green-600">{stats.online}</p>
              <p className="text-[10px] text-slate-500">Online</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <WifiOff className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-lg font-bold text-gray-600">{stats.offline}</p>
              <p className="text-[10px] text-slate-500">Offline</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <div>
              <p className="text-lg font-bold text-yellow-600">{stats.warning}</p>
              <p className="text-[10px] text-slate-500">Warning</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <div>
              <p className="text-lg font-bold text-red-600">{stats.tampered}</p>
              <p className="text-[10px] text-slate-500">Tampered</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" />
            <div>
              <p className="text-lg font-bold text-purple-600">{stats.totalConsumption.toFixed(0)}</p>
              <p className="text-[10px] text-slate-500">m³ Today</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'overview', label: 'Meter List' },
          { id: 'anomalies', label: `Anomalies (${stats.anomalies})` },
          { id: 'analytics', label: 'Analytics' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'overview' && (
        <>
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by name or account..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <Select
              value={filterStatus}
              options={[
                { value: '', label: 'All Status' },
                { value: 'online', label: '🟢 Online' },
                { value: 'offline', label: '⚫ Offline' },
                { value: 'warning', label: '🟡 Warning' },
                { value: 'tampered', label: '🔴 Tampered' }
              ]}
              onChange={setFilterStatus}
            />
            <Select
              value={filterDMA}
              options={[
                { value: '', label: 'All DMAs' },
                ...uniqueDMAs.map(d => ({ value: d, label: d }))
              ]}
              onChange={setFilterDMA}
            />
          </div>

          {/* Meters Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {isLoading ? (
              Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-1/2 mb-2" />
                  <div className="h-6 bg-slate-200 rounded w-3/4 mb-4" />
                  <div className="h-20 bg-slate-100 rounded" />
                </div>
              ))
            ) : (
              filteredMeters.map((meter) => (
                <div 
                  key={meter.id}
                  className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-lg transition-all cursor-pointer"
                  onClick={() => setSelectedMeter(meter)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-mono text-xs text-slate-400">{meter.accountNumber}</p>
                      <p className="font-semibold text-slate-900 mt-0.5">{meter.customerName}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${getStatusBadge(meter.status)}`}>
                      {meter.status}
                    </span>
                  </div>

                  <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg p-3 mb-3">
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-xs text-slate-500">Current Reading</p>
                        <p className="text-2xl font-bold text-slate-900">{meter.lastReading.toFixed(1)}</p>
                        <p className="text-xs text-slate-400">m³</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-lg font-bold flex items-center justify-end gap-1 ${
                          meter.consumption > meter.avgConsumption * 1.2 ? 'text-red-600' :
                          meter.consumption < 0 ? 'text-red-600' :
                          meter.consumption < meter.avgConsumption * 0.8 ? 'text-yellow-600' : 'text-green-600'
                        }`}>
                          {meter.consumption > 0 ? '+' : ''}{meter.consumption.toFixed(1)}
                          {meter.consumption > meter.avgConsumption * 1.2 && <TrendingUp className="w-4 h-4" />}
                          {meter.consumption < meter.avgConsumption * 0.8 && <TrendingDown className="w-4 h-4" />}
                        </p>
                        <p className="text-xs text-slate-500">m³/day</p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs mb-3">
                    <div className="bg-slate-50 rounded p-2">
                      <div className="flex items-center justify-center gap-1">
                        <Battery className={`w-3 h-3 ${meter.battery > 50 ? 'text-green-500' : meter.battery > 20 ? 'text-yellow-500' : 'text-red-500'}`} />
                        <span className="font-semibold">{meter.battery}%</span>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded p-2">
                      <div className="flex items-center justify-center gap-1">
                        <Signal className={`w-3 h-3 ${meter.signalStrength >= 4 ? 'text-green-500' : meter.signalStrength >= 2 ? 'text-yellow-500' : 'text-red-500'}`} />
                        <span className="font-semibold">{meter.signalStrength}/5</span>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded p-2">
                      <div className="flex items-center justify-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span className="font-semibold">{meter.lastContact}</span>
                      </div>
                    </div>
                  </div>

                  {meter.alerts.length > 0 && (
                    <div className="space-y-1">
                      {meter.alerts.map((alert, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                          <AlertTriangle className="w-3 h-3" />
                          {alert}
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {meter.dma}
                    </span>
                    <span className="capitalize">{meter.meterType}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}

      {activeTab === 'anomalies' && (
        <SectionCard title="Consumption Anomalies" subtitle="AI-detected unusual consumption patterns" noPadding>
          <div className="divide-y divide-slate-100">
            {anomalies.map((anomaly, idx) => (
              <div key={idx} className="p-4 hover:bg-slate-50">
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    anomaly.anomalyType === 'reverse_flow' ? 'bg-red-100' :
                    anomaly.anomalyType === 'tampering' ? 'bg-red-100' :
                    anomaly.anomalyType === 'sudden_increase' ? 'bg-orange-100' :
                    anomaly.anomalyType === 'sudden_decrease' ? 'bg-yellow-100' : 'bg-blue-100'
                  }`}>
                    <AlertTriangle className={`w-6 h-6 ${
                      anomaly.anomalyType === 'reverse_flow' ? 'text-red-600' :
                      anomaly.anomalyType === 'tampering' ? 'text-red-600' :
                      anomaly.anomalyType === 'sudden_increase' ? 'text-orange-600' :
                      anomaly.anomalyType === 'sudden_decrease' ? 'text-yellow-600' : 'text-blue-600'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-slate-400">{anomaly.accountNumber}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs border ${getSeverityColor(anomaly.severity)}`}>
                        {anomaly.severity}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        anomaly.status === 'new' ? 'bg-red-100 text-red-700' :
                        anomaly.status === 'investigating' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {anomaly.status}
                      </span>
                    </div>
                    <p className="font-semibold text-slate-900 mt-1">{anomaly.customerName}</p>
                    <p className="text-sm text-slate-600 mt-1 capitalize">{anomaly.anomalyType.replace('_', ' ')}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{anomaly.currentConsumption.toFixed(1)}</p>
                      <p className="text-xs text-slate-500">Actual</p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{anomaly.expectedConsumption.toFixed(1)}</p>
                      <p className="text-xs text-slate-500">Expected</p>
                    </div>
                    <div>
                      <p className={`text-sm font-semibold ${anomaly.deviation > 0 ? 'text-red-600' : 'text-yellow-600'}`}>
                        {anomaly.deviation > 0 ? '+' : ''}{anomaly.deviation}%
                      </p>
                      <p className="text-xs text-slate-500">Deviation</p>
                    </div>
                  </div>
                  <Button variant="secondary" size="sm">
                    <Eye className="w-4 h-4" />
                    Investigate
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {activeTab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SectionCard title="Consumption by DMA" subtitle="Daily consumption distribution">
            <div className="space-y-3">
              {uniqueDMAs.map((dma, idx) => {
                const dmaMeters = meters.filter(m => m.dma === dma)
                const totalConsumption = dmaMeters.reduce((sum, m) => sum + Math.max(0, m.consumption), 0)
                const maxConsumption = 800
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-slate-700">{dma}</span>
                      <span className="text-sm font-semibold text-slate-900">{totalConsumption.toFixed(1)} m³</span>
                    </div>
                    <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                        style={{ width: `${(totalConsumption / maxConsumption) * 100}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </SectionCard>

          <SectionCard title="Meter Health" subtitle="Battery and signal status overview">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-green-600">
                  {meters.filter(m => m.battery > 50).length}
                </p>
                <p className="text-sm text-green-700">Good Battery</p>
              </div>
              <div className="bg-yellow-50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-yellow-600">
                  {meters.filter(m => m.battery > 20 && m.battery <= 50).length}
                </p>
                <p className="text-sm text-yellow-700">Low Battery</p>
              </div>
              <div className="bg-red-50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-red-600">
                  {meters.filter(m => m.battery <= 20).length}
                </p>
                <p className="text-sm text-red-700">Critical Battery</p>
              </div>
              <div className="bg-blue-50 rounded-xl p-4 text-center">
                <p className="text-3xl font-bold text-blue-600">
                  {meters.filter(m => m.signalStrength >= 4).length}
                </p>
                <p className="text-sm text-blue-700">Strong Signal</p>
              </div>
            </div>
          </SectionCard>
        </div>
      )}

      {/* Meter Detail Modal */}
      {selectedMeter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className={`p-6 text-white ${
              selectedMeter.status === 'online' ? 'bg-green-600' :
              selectedMeter.status === 'offline' ? 'bg-gray-600' :
              selectedMeter.status === 'warning' ? 'bg-yellow-600' : 'bg-red-600'
            }`}>
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-white/70 text-sm font-mono">{selectedMeter.accountNumber}</p>
                  <h2 className="text-xl font-bold mt-1">{selectedMeter.customerName}</h2>
                  <p className="text-white/70">{selectedMeter.location}</p>
                </div>
                <button onClick={() => setSelectedMeter(null)} className="p-2 hover:bg-white/20 rounded-lg">✕</button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-slate-50 rounded-xl p-4 text-center">
                <p className="text-4xl font-bold text-slate-900">{selectedMeter.lastReading.toFixed(1)}</p>
                <p className="text-slate-500">Current Reading (m³)</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Daily Consumption</p>
                  <p className={`text-xl font-bold ${selectedMeter.consumption > selectedMeter.avgConsumption * 1.2 ? 'text-red-600' : 'text-green-600'}`}>
                    {selectedMeter.consumption.toFixed(1)} m³
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Average</p>
                  <p className="text-xl font-bold text-slate-900">{selectedMeter.avgConsumption.toFixed(1)} m³</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <Battery className={`w-5 h-5 mx-auto ${selectedMeter.battery > 50 ? 'text-green-500' : 'text-red-500'}`} />
                  <p className="text-sm font-semibold mt-1">{selectedMeter.battery}%</p>
                  <p className="text-[10px] text-slate-500">Battery</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <Signal className={`w-5 h-5 mx-auto ${selectedMeter.signalStrength >= 3 ? 'text-green-500' : 'text-red-500'}`} />
                  <p className="text-sm font-semibold mt-1">{selectedMeter.signalStrength}/5</p>
                  <p className="text-[10px] text-slate-500">Signal</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <Gauge className="w-5 h-5 mx-auto text-blue-500" />
                  <p className="text-sm font-semibold mt-1 capitalize">{selectedMeter.meterType}</p>
                  <p className="text-[10px] text-slate-500">Type</p>
                </div>
              </div>

              {selectedMeter.alerts.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-semibold text-slate-900">Active Alerts</p>
                  {selectedMeter.alerts.map((alert, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 bg-red-50 text-red-700 rounded-lg text-sm">
                      <AlertTriangle className="w-4 h-4" />
                      {alert}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button variant="primary" className="flex-1">
                  <Bell className="w-4 h-4" />
                  Set Alert
                </Button>
                <Button variant="secondary" className="flex-1">
                  <Settings className="w-4 h-4" />
                  Configure
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
