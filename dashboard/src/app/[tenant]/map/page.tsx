'use client'

import { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import {
  Layers, Filter, RefreshCw, MapPin, Droplets, AlertTriangle,
  Wifi, WifiOff, Gauge, Activity, Target, ZoomIn, ZoomOut,
  Maximize2, Info, X, Navigation, ChevronDown, ChevronUp,
  Circle, Square, Triangle, Hexagon, Eye, EyeOff, Settings
} from 'lucide-react'
import { clsx } from 'clsx'

// =============================================================================
// TYPES
// =============================================================================

interface GeoJSONFeature {
  type: 'Feature'
  id?: string
  geometry: {
    type: 'Point' | 'Polygon' | 'LineString'
    coordinates: number[] | number[][] | number[][][]
  }
  properties: Record<string, any>
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
  metadata?: Record<string, any>
}

interface MapData {
  tenantId: string
  layers: {
    dmas?: GeoJSONFeatureCollection
    sensors?: GeoJSONFeatureCollection
    leaks?: GeoJSONFeatureCollection
  }
  metadata: {
    total_dmas: number
    total_sensors: number
    sensors_online: number
    total_leaks: number
    active_leaks: number
    center: [number, number]
    zoom: number
  }
  generatedAt: string
}

interface LayerVisibility {
  dmas: boolean
  sensors: boolean
  leaks: boolean
  heatmap: boolean
}

interface LayerFilters {
  sensorStatus: 'all' | 'online' | 'warning' | 'offline'
  sensorType: 'all' | 'flow' | 'pressure' | 'acoustic'
  leakStatus: 'all' | 'active' | 'assigned' | 'in-progress' | 'repaired'
  leakSeverity: 'all' | 'critical' | 'high' | 'medium' | 'low'
  minNrw: number | null
}

// =============================================================================
// DYNAMIC MAP COMPONENT (SSR-safe)
// =============================================================================

const LeafletMap = dynamic<{
  mapData: MapData | null
  layers: LayerVisibility
  onFeatureClick: (feature: GeoJSONFeature) => void
  selectedFeature: GeoJSONFeature | null
}>(
  () => import('../../../components/maps/IntelligentMapView'),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full bg-slate-100 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
          <span className="text-slate-600">Loading map...</span>
        </div>
      </div>
    )
  }
)

// =============================================================================
// MAIN PAGE COMPONENT
// =============================================================================

export default function TenantMapPage() {
  const params = useParams()
  const tenantId = params.tenant as string
  
  // State
  const [mapData, setMapData] = useState<MapData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [isLive, setIsLive] = useState(true)
  
  // Layer visibility
  const [layers, setLayers] = useState<LayerVisibility>({
    dmas: true,
    sensors: true,
    leaks: true,
    heatmap: true
  })
  
  // Filters
  const [filters, setFilters] = useState<LayerFilters>({
    sensorStatus: 'all',
    sensorType: 'all',
    leakStatus: 'all',
    leakSeverity: 'all',
    minNrw: null
  })
  
  // UI state
  const [showControls, setShowControls] = useState(true)
  const [showLegend, setShowLegend] = useState(true)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedFeature, setSelectedFeature] = useState<GeoJSONFeature | null>(null)
  
  // Fetch map data
  const fetchMapData = useCallback(async () => {
    try {
      setLoading(true)
      
      // Build query params
      const params = new URLSearchParams({
        include_layers: 'dmas,sensors,leaks'
      })
      
      if (filters.sensorStatus !== 'all') {
        params.set('sensor_status', filters.sensorStatus)
      }
      if (filters.leakStatus !== 'all') {
        params.set('leak_status', filters.leakStatus)
      }
      if (filters.leakSeverity !== 'all') {
        params.set('leak_severity', filters.leakSeverity)
      }
      if (filters.minNrw !== null) {
        params.set('min_nrw', filters.minNrw.toString())
      }
      
      const response = await fetch(`/api/map/geojson?tenant=${tenantId}&${params.toString()}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch map data')
      }
      
      const data = await response.json()
      setMapData(data)
      setLastRefresh(new Date())
      setError(null)
    } catch (err) {
      console.error('Map data fetch error:', err)
      setError('Failed to load map data')
    } finally {
      setLoading(false)
    }
  }, [tenantId, filters])
  
  // Initial fetch
  useEffect(() => {
    fetchMapData()
  }, [fetchMapData])
  
  // Auto-refresh when live mode is enabled
  useEffect(() => {
    if (!isLive) return
    
    const interval = setInterval(() => {
      fetchMapData()
    }, 30000) // Refresh every 30 seconds
    
    return () => clearInterval(interval)
  }, [isLive, fetchMapData])
  
  // Toggle layer
  const toggleLayer = (layer: keyof LayerVisibility) => {
    setLayers(prev => ({ ...prev, [layer]: !prev[layer] }))
  }
  
  // Handle feature click
  const handleFeatureClick = (feature: GeoJSONFeature) => {
    setSelectedFeature(feature)
  }
  
  // Calculate statistics
  const stats = useMemo(() => {
    if (!mapData) return null
    
    const { metadata } = mapData
    return {
      dmas: metadata.total_dmas,
      sensors: metadata.total_sensors,
      sensorsOnline: metadata.sensors_online,
      leaks: metadata.total_leaks,
      activeLeaks: metadata.active_leaks,
      sensorHealth: Math.round((metadata.sensors_online / metadata.total_sensors) * 100) || 0
    }
  }, [mapData])
  
  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between z-20">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">Network Intelligence Map</h1>
            <p className="text-xs text-slate-500">
              {tenantId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} • Real-time GIS View
            </p>
          </div>
          
          {/* Live indicator */}
          <button
            onClick={() => setIsLive(!isLive)}
            className={clsx(
              'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors',
              isLive ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
            )}
          >
            {isLive ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                LIVE
              </>
            ) : (
              <>
                <Circle className="w-2 h-2 fill-current" />
                PAUSED
              </>
            )}
          </button>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Quick stats */}
          {stats && (
            <div className="hidden md:flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <Hexagon className="w-4 h-4 text-blue-500" />
                <span className="text-slate-600">{stats.dmas} DMAs</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Wifi className="w-4 h-4 text-emerald-500" />
                <span className="text-slate-600">{stats.sensorsOnline}/{stats.sensors} Sensors</span>
              </div>
              <div className="flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span className="text-slate-600">{stats.activeLeaks} Active Leaks</span>
              </div>
            </div>
          )}
          
          {/* Refresh */}
          <button
            onClick={fetchMapData}
            disabled={loading}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            title="Refresh map data"
          >
            <RefreshCw className={clsx('w-5 h-5 text-slate-600', loading && 'animate-spin')} />
          </button>
          
          {/* Settings */}
          <button
            onClick={() => setShowControls(!showControls)}
            className={clsx(
              'p-2 rounded-lg transition-colors',
              showControls ? 'bg-blue-100 text-blue-600' : 'hover:bg-slate-100 text-slate-600'
            )}
            title="Toggle controls"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>
      
      {/* Main content */}
      <div className="flex-1 relative overflow-hidden">
        {/* Map */}
        <div className="absolute inset-0">
          {error ? (
            <div className="w-full h-full flex items-center justify-center bg-slate-50">
              <div className="text-center">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
                <p className="text-slate-600 font-medium">{error}</p>
                <button
                  onClick={fetchMapData}
                  className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : (
            <LeafletMap
              mapData={mapData}
              layers={layers}
              onFeatureClick={handleFeatureClick}
              selectedFeature={selectedFeature}
            />
          )}
        </div>
        
        {/* Controls Panel */}
        {showControls && (
          <div className="absolute top-4 left-4 z-10 w-72 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
            {/* Layers */}
            <div className="p-3 border-b border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4" />
                  Layers
                </h3>
              </div>
              
              <div className="space-y-2">
                <LayerToggle
                  label="DMA Zones"
                  description="NRW heatmap overlay"
                  icon={<Hexagon className="w-4 h-4" />}
                  enabled={layers.dmas}
                  onChange={() => toggleLayer('dmas')}
                  color="blue"
                />
                <LayerToggle
                  label="Sensors"
                  description={stats ? `${stats.sensorsOnline}/${stats.sensors} online` : 'Loading...'}
                  icon={<Wifi className="w-4 h-4" />}
                  enabled={layers.sensors}
                  onChange={() => toggleLayer('sensors')}
                  color="emerald"
                />
                <LayerToggle
                  label="Leaks"
                  description={stats ? `${stats.activeLeaks} active` : 'Loading...'}
                  icon={<Droplets className="w-4 h-4" />}
                  enabled={layers.leaks}
                  onChange={() => toggleLayer('leaks')}
                  color="red"
                />
                <LayerToggle
                  label="NRW Heatmap"
                  description="Intensity shading"
                  icon={<Activity className="w-4 h-4" />}
                  enabled={layers.heatmap}
                  onChange={() => toggleLayer('heatmap')}
                  color="amber"
                />
              </div>
            </div>
            
            {/* Filters */}
            <div className="p-3 border-b border-slate-100">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="w-full flex items-center justify-between text-sm font-semibold text-slate-900"
              >
                <span className="flex items-center gap-2">
                  <Filter className="w-4 h-4" />
                  Filters
                </span>
                {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              
              {showFilters && (
                <div className="mt-3 space-y-3">
                  <FilterSelect
                    label="Sensor Status"
                    value={filters.sensorStatus}
                    onChange={(v) => setFilters(f => ({ ...f, sensorStatus: v as any }))}
                    options={[
                      { value: 'all', label: 'All Sensors' },
                      { value: 'online', label: 'Online Only' },
                      { value: 'warning', label: 'Warnings' },
                      { value: 'offline', label: 'Offline' }
                    ]}
                  />
                  <FilterSelect
                    label="Sensor Type"
                    value={filters.sensorType}
                    onChange={(v) => setFilters(f => ({ ...f, sensorType: v as any }))}
                    options={[
                      { value: 'all', label: 'All Types' },
                      { value: 'flow', label: 'Flow Meters' },
                      { value: 'pressure', label: 'Pressure' },
                      { value: 'acoustic', label: 'Acoustic' }
                    ]}
                  />
                  <FilterSelect
                    label="Leak Severity"
                    value={filters.leakSeverity}
                    onChange={(v) => setFilters(f => ({ ...f, leakSeverity: v as any }))}
                    options={[
                      { value: 'all', label: 'All Severities' },
                      { value: 'critical', label: 'Critical' },
                      { value: 'high', label: 'High' },
                      { value: 'medium', label: 'Medium' },
                      { value: 'low', label: 'Low' }
                    ]}
                  />
                  <FilterSelect
                    label="Leak Status"
                    value={filters.leakStatus}
                    onChange={(v) => setFilters(f => ({ ...f, leakStatus: v as any }))}
                    options={[
                      { value: 'all', label: 'All Statuses' },
                      { value: 'active', label: 'Active' },
                      { value: 'assigned', label: 'Assigned' },
                      { value: 'in-progress', label: 'In Progress' },
                      { value: 'repaired', label: 'Repaired' }
                    ]}
                  />
                </div>
              )}
            </div>
            
            {/* Last update */}
            <div className="px-3 py-2 bg-slate-50 text-xs text-slate-500">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>
        )}
        
        {/* Legend */}
        {showLegend && (
          <div className="absolute bottom-4 left-4 z-10 bg-white rounded-xl shadow-lg border border-slate-200 p-3 min-w-[200px]">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-xs font-semibold text-slate-700">Legend</h4>
              <button onClick={() => setShowLegend(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div className="space-y-2 text-xs">
              {/* NRW Legend */}
              <div>
                <p className="text-slate-500 mb-1">NRW Level</p>
                <div className="flex gap-1">
                  {[
                    { color: '#10b981', label: '<20%' },
                    { color: '#22c55e', label: '20-25%' },
                    { color: '#eab308', label: '25-35%' },
                    { color: '#f97316', label: '35-45%' },
                    { color: '#ef4444', label: '>45%' },
                  ].map(({ color, label }) => (
                    <div key={label} className="flex-1 text-center">
                      <div className="h-2 rounded" style={{ backgroundColor: color }} />
                      <span className="text-[10px] text-slate-400">{label}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Sensor status */}
              <div className="flex items-center gap-3 pt-1">
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span className="text-slate-600">Online</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span className="text-slate-600">Warning</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <span className="text-slate-600">Offline</span>
                </div>
              </div>
              
              {/* Leak severity */}
              <div className="flex items-center gap-3 pt-1">
                <div className="flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-red-600" />
                  <span className="text-slate-600">Critical</span>
                </div>
                <div className="flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-amber-500" />
                  <span className="text-slate-600">Medium</span>
                </div>
                <div className="flex items-center gap-1">
                  <Droplets className="w-3 h-3 text-blue-500" />
                  <span className="text-slate-600">Low</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {!showLegend && (
          <button
            onClick={() => setShowLegend(true)}
            className="absolute bottom-4 left-4 z-10 p-2 bg-white rounded-lg shadow-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
            title="Show legend"
          >
            <Info className="w-5 h-5" />
          </button>
        )}
        
        {/* Feature Detail Panel */}
        {selectedFeature && (
          <FeatureDetailPanel
            feature={selectedFeature}
            onClose={() => setSelectedFeature(null)}
          />
        )}
      </div>
    </div>
  )
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

interface LayerToggleProps {
  label: string
  description: string
  icon: React.ReactNode
  enabled: boolean
  onChange: () => void
  color: 'blue' | 'emerald' | 'red' | 'amber'
}

function LayerToggle({ label, description, icon, enabled, onChange, color }: LayerToggleProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    red: 'bg-red-100 text-red-600',
    amber: 'bg-amber-100 text-amber-600'
  }
  
  return (
    <button
      onClick={onChange}
      className={clsx(
        'w-full flex items-center gap-3 p-2 rounded-lg transition-colors text-left',
        enabled ? 'bg-slate-50' : 'hover:bg-slate-50 opacity-60'
      )}
    >
      <div className={clsx('p-1.5 rounded-lg', enabled ? colorClasses[color] : 'bg-slate-100 text-slate-400')}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900">{label}</p>
        <p className="text-xs text-slate-500 truncate">{description}</p>
      </div>
      {enabled ? (
        <Eye className="w-4 h-4 text-slate-400" />
      ) : (
        <EyeOff className="w-4 h-4 text-slate-300" />
      )}
    </button>
  )
}

interface FilterSelectProps {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}

function FilterSelect({ label, value, onChange, options }: FilterSelectProps) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-2 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  )
}

interface FeatureDetailPanelProps {
  feature: GeoJSONFeature
  onClose: () => void
}

function FeatureDetailPanel({ feature, onClose }: FeatureDetailPanelProps) {
  const props = feature.properties
  const type = props.type as 'dma' | 'sensor' | 'leak'
  
  return (
    <div className="absolute top-4 right-4 z-10 w-80 bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className={clsx(
        'px-4 py-3 flex items-center justify-between',
        type === 'dma' ? 'bg-blue-50' : type === 'sensor' ? 'bg-emerald-50' : 'bg-red-50'
      )}>
        <div className="flex items-center gap-2">
          {type === 'dma' && <Hexagon className="w-5 h-5 text-blue-600" />}
          {type === 'sensor' && <Wifi className="w-5 h-5 text-emerald-600" />}
          {type === 'leak' && <Droplets className="w-5 h-5 text-red-600" />}
          <div>
            <h3 className="font-semibold text-slate-900">{props.name || props.id}</h3>
            <p className="text-xs text-slate-500 capitalize">{type}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-white/50 rounded">
          <X className="w-4 h-4 text-slate-500" />
        </button>
      </div>
      
      {/* Content */}
      <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
        {type === 'dma' && (
          <>
            <DetailRow label="NRW %" value={`${props.nrw_percent}%`} highlight={props.nrw_percent > 35} />
            <DetailRow label="Status" value={props.status} />
            <DetailRow label="Active Leaks" value={props.active_leaks} />
            <DetailRow label="Flow Rate" value={`${props.flow_rate_m3h} m³/h`} />
            <DetailRow label="Pressure" value={`${props.pressure_bar} bar`} />
            <DetailRow label="Connections" value={props.connections?.toLocaleString()} />
            <DetailRow label="Population" value={props.population?.toLocaleString()} />
            <DetailRow label="Sensors" value={`${props.sensors_online}/${props.sensors_total}`} />
          </>
        )}
        
        {type === 'sensor' && (
          <>
            <DetailRow label="Type" value={props.sensor_type} />
            <DetailRow label="Status" value={props.status} />
            <DetailRow label="Value" value={`${props.value} ${props.unit}`} />
            <DetailRow label="Battery" value={`${props.battery_percent}%`} highlight={props.battery_percent < 20} />
            <DetailRow label="Signal" value={`${props.signal_strength}%`} />
            <DetailRow label="DMA" value={props.dma_name} />
            <DetailRow label="Last Reading" value={new Date(props.last_reading).toLocaleString()} />
            {props.has_alert && (
              <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-xs text-amber-700 font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {props.alert_type?.replace('_', ' ')}
                </p>
              </div>
            )}
          </>
        )}
        
        {type === 'leak' && (
          <>
            <DetailRow label="Severity" value={props.severity} highlight={props.severity === 'critical'} />
            <DetailRow label="Status" value={props.status} />
            <DetailRow label="Location" value={props.location} />
            <DetailRow label="Flow Rate" value={`${props.flow_rate_lph} L/hr`} />
            <DetailRow label="Est. Loss" value={`${props.estimated_loss_m3_day} m³/day`} />
            <DetailRow label="Detection" value={props.detection_method?.replace('_', ' ')} />
            <DetailRow label="AI Confidence" value={`${props.confidence_percent}%`} />
            <DetailRow label="DMA" value={props.dma_name} />
            <DetailRow label="Detected" value={new Date(props.detected_at).toLocaleDateString()} />
            {props.assigned_to && (
              <DetailRow label="Assigned To" value={props.assigned_to} />
            )}
            {props.work_order_id && (
              <DetailRow label="Work Order" value={props.work_order_id} />
            )}
          </>
        )}
      </div>
      
      {/* Actions */}
      <div className="p-3 bg-slate-50 border-t border-slate-100 flex gap-2">
        {type === 'leak' && props.status === 'active' && (
          <button className="flex-1 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">
            Create Work Order
          </button>
        )}
        {type === 'sensor' && props.status === 'offline' && (
          <button className="flex-1 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700">
            Schedule Maintenance
          </button>
        )}
        <button className="py-2 px-3 border border-slate-200 text-slate-700 text-sm font-medium rounded-lg hover:bg-white">
          <Navigation className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

function DetailRow({ label, value, highlight }: { label: string; value: any; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className={clsx(
        'font-medium',
        highlight ? 'text-red-600' : 'text-slate-900'
      )}>
        {value}
      </span>
    </div>
  )
}
