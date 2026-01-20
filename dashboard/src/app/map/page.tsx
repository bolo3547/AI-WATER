'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  MapPin, Droplets, AlertTriangle, CheckCircle, Clock, 
  Filter, Layers, ZoomIn, ZoomOut, Maximize2, Target,
  Info, X, Navigation, Wrench, Phone, Calendar, User, Locate, ExternalLink,
  RefreshCw, Wifi, WifiOff, Activity, Gauge, Battery, Signal
} from 'lucide-react'

// Operator location interface
interface OperatorLocation {
  lat: number
  lng: number
  accuracy: number
  timestamp: Date
  name: string
}

// DMA Zone interface for real-time updates
interface DMAZone {
  id: string
  name: string
  nrw: number
  status: 'good' | 'moderate' | 'warning' | 'critical'
  lat: number
  lng: number
  leaks: number
  flowRate: number
  pressure: number
}

// Leak interface for real-time updates
interface LeakData {
  id: number
  location: string
  dma: string
  severity: 'high' | 'medium' | 'low'
  status: 'active' | 'assigned' | 'monitoring' | 'repaired'
  flowRate: number
  detectedAt: string
  lat: number
  lng: number
}

// Sensor interface
interface SensorData {
  id: string
  name: string
  type: 'flow' | 'pressure' | 'acoustic'
  status: 'online' | 'warning' | 'offline'
  lat: number
  lng: number
  value: number
  unit: string
  battery: number
  lastReading: Date
}

// Initial DMA zones for Lusaka
const initialDmaZones: DMAZone[] = [
  { id: 'woodlands', name: 'Woodlands', nrw: 18.5, status: 'good', lat: -15.385, lng: 28.310, leaks: 2, flowRate: 850, pressure: 3.2 },
  { id: 'kabulonga', name: 'Kabulonga', nrw: 21.2, status: 'good', lat: -15.408, lng: 28.332, leaks: 3, flowRate: 720, pressure: 3.5 },
  { id: 'roma', name: 'Roma', nrw: 23.1, status: 'good', lat: -15.422, lng: 28.298, leaks: 1, flowRate: 680, pressure: 3.1 },
  { id: 'matero', name: 'Matero', nrw: 48.2, status: 'critical', lat: -15.362, lng: 28.278, leaks: 12, flowRate: 1250, pressure: 2.4 },
  { id: 'chilenje', name: 'Chilenje', nrw: 45.8, status: 'critical', lat: -15.445, lng: 28.268, leaks: 8, flowRate: 920, pressure: 2.6 },
  { id: 'garden', name: 'Garden', nrw: 42.1, status: 'warning', lat: -15.398, lng: 28.285, leaks: 6, flowRate: 780, pressure: 2.9 },
  { id: 'rhodes-park', name: 'Rhodes Park', nrw: 28.5, status: 'moderate', lat: -15.412, lng: 28.305, leaks: 4, flowRate: 650, pressure: 3.3 },
  { id: 'olympia', name: 'Olympia', nrw: 35.2, status: 'warning', lat: -15.438, lng: 28.312, leaks: 5, flowRate: 580, pressure: 3.0 },
  { id: 'kabwata', name: 'Kabwata', nrw: 39.8, status: 'warning', lat: -15.455, lng: 28.285, leaks: 7, flowRate: 890, pressure: 2.7 },
  { id: 'mtendere', name: 'Mtendere', nrw: 52.3, status: 'critical', lat: -15.448, lng: 28.342, leaks: 14, flowRate: 1100, pressure: 2.2 },
]

// Initial leak data
const initialLeakData: LeakData[] = [
  { id: 1, location: 'Great East Rd & Lumumba Rd', dma: 'matero', severity: 'high', status: 'active', flowRate: 45.2, detectedAt: '2026-01-14', lat: -15.360, lng: 28.275 },
  { id: 2, location: 'Independence Ave', dma: 'rhodes-park', severity: 'medium', status: 'assigned', flowRate: 22.8, detectedAt: '2026-01-13', lat: -15.414, lng: 28.308 },
  { id: 3, location: 'Cairo Rd South', dma: 'garden', severity: 'low', status: 'repaired', flowRate: 8.5, detectedAt: '2026-01-12', lat: -15.402, lng: 28.282 },
  { id: 4, location: 'Kafue Rd', dma: 'chilenje', severity: 'high', status: 'active', flowRate: 67.3, detectedAt: '2026-01-15', lat: -15.448, lng: 28.265 },
  { id: 5, location: 'Los Angeles Blvd', dma: 'kabulonga', severity: 'medium', status: 'assigned', flowRate: 18.4, detectedAt: '2026-01-14', lat: -15.405, lng: 28.335 },
  { id: 6, location: 'Manda Hill Area', dma: 'woodlands', severity: 'low', status: 'monitoring', flowRate: 5.2, detectedAt: '2026-01-13', lat: -15.388, lng: 28.315 },
  { id: 7, location: 'Chawama Rd Junction', dma: 'kabwata', severity: 'high', status: 'active', flowRate: 52.1, detectedAt: '2026-01-20', lat: -15.458, lng: 28.282 },
  { id: 8, location: 'Chelstone Market', dma: 'mtendere', severity: 'medium', status: 'assigned', flowRate: 31.5, detectedAt: '2026-01-19', lat: -15.450, lng: 28.345 },
]

// Initial sensor data
const initialSensorData: SensorData[] = [
  { id: 'ESP32-001', name: 'Woodlands Flow A', type: 'flow', status: 'online', lat: -15.383, lng: 28.308, value: 856, unit: 'L/hr', battery: 92, lastReading: new Date() },
  { id: 'ESP32-002', name: 'Kabulonga Pressure', type: 'pressure', status: 'online', lat: -15.406, lng: 28.330, value: 3.4, unit: 'bar', battery: 85, lastReading: new Date() },
  { id: 'ESP32-003', name: 'Matero Acoustic', type: 'acoustic', status: 'warning', lat: -15.364, lng: 28.280, value: 72, unit: 'dB', battery: 23, lastReading: new Date() },
  { id: 'ESP32-004', name: 'Garden Flow', type: 'flow', status: 'online', lat: -15.400, lng: 28.287, value: 782, unit: 'L/hr', battery: 78, lastReading: new Date() },
  { id: 'ESP32-005', name: 'Chilenje Pressure', type: 'pressure', status: 'online', lat: -15.447, lng: 28.270, value: 2.8, unit: 'bar', battery: 65, lastReading: new Date() },
  { id: 'ESP32-006', name: 'Roma Flow', type: 'flow', status: 'online', lat: -15.424, lng: 28.300, value: 695, unit: 'L/hr', battery: 88, lastReading: new Date() },
  { id: 'ESP32-007', name: 'Rhodes Park Acoustic', type: 'acoustic', status: 'online', lat: -15.410, lng: 28.303, value: 28, unit: 'dB', battery: 71, lastReading: new Date() },
  { id: 'ESP32-008', name: 'Olympia Flow', type: 'flow', status: 'offline', lat: -15.440, lng: 28.314, value: 0, unit: 'L/hr', battery: 5, lastReading: new Date(Date.now() - 3600000) },
  { id: 'ESP32-009', name: 'Kabwata Pressure', type: 'pressure', status: 'online', lat: -15.457, lng: 28.287, value: 2.9, unit: 'bar', battery: 82, lastReading: new Date() },
  { id: 'ESP32-010', name: 'Mtendere Acoustic', type: 'acoustic', status: 'warning', lat: -15.446, lng: 28.340, value: 85, unit: 'dB', battery: 45, lastReading: new Date() },
  { id: 'ESP32-011', name: 'Woodlands Flow B', type: 'flow', status: 'online', lat: -15.387, lng: 28.312, value: 912, unit: 'L/hr', battery: 90, lastReading: new Date() },
  { id: 'ESP32-012', name: 'Matero Flow', type: 'flow', status: 'online', lat: -15.358, lng: 28.276, value: 1285, unit: 'L/hr', battery: 67, lastReading: new Date() },
]

export default function MapPage() {
  const [selectedDMA, setSelectedDMA] = useState<string | null>(null)
  const [selectedLeak, setSelectedLeak] = useState<LeakData | null>(null)
  const [selectedSensor, setSelectedSensor] = useState<SensorData | null>(null)
  const [filter, setFilter] = useState<'all' | 'active' | 'assigned' | 'repaired'>('all')
  const [layer, setLayer] = useState<'nrw' | 'leaks' | 'sensors'>('nrw')
  const [zoom, setZoom] = useState(1)
  const [operatorLocation, setOperatorLocation] = useState<OperatorLocation | null>(null)
  const [locationError, setLocationError] = useState<string | null>(null)
  
  // Real-time state
  const [dmaZones, setDmaZones] = useState<DMAZone[]>(initialDmaZones)
  const [leakData, setLeakData] = useState<LeakData[]>(initialLeakData)
  const [sensorData, setSensorData] = useState<SensorData[]>(initialSensorData)
  const [isLive, setIsLive] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  
  // Real-time data update function
  const updateRealTimeData = useCallback(() => {
    // Update DMA zones with slight variations
    setDmaZones(prev => prev.map(dma => {
      const nrwChange = (Math.random() - 0.5) * 2
      const newNrw = Math.max(10, Math.min(60, dma.nrw + nrwChange))
      const flowChange = (Math.random() - 0.5) * 50
      const pressureChange = (Math.random() - 0.5) * 0.2
      
      let newStatus: DMAZone['status'] = 'good'
      if (newNrw > 45) newStatus = 'critical'
      else if (newNrw > 35) newStatus = 'warning'
      else if (newNrw > 25) newStatus = 'moderate'
      
      return {
        ...dma,
        nrw: Math.round(newNrw * 10) / 10,
        status: newStatus,
        flowRate: Math.max(100, dma.flowRate + flowChange),
        pressure: Math.max(1.5, Math.min(4.5, dma.pressure + pressureChange))
      }
    }))
    
    // Update leak data flow rates
    setLeakData(prev => prev.map(leak => ({
      ...leak,
      flowRate: leak.status === 'repaired' ? 0 : Math.max(1, leak.flowRate + (Math.random() - 0.4) * 5)
    })))
    
    // Update sensor data
    setSensorData(prev => prev.map(sensor => {
      if (sensor.status === 'offline') return sensor
      
      let newValue = sensor.value
      if (sensor.type === 'flow') {
        newValue = Math.max(0, sensor.value + (Math.random() - 0.5) * 100)
      } else if (sensor.type === 'pressure') {
        newValue = Math.max(1, Math.min(5, sensor.value + (Math.random() - 0.5) * 0.3))
      } else if (sensor.type === 'acoustic') {
        newValue = Math.max(10, Math.min(100, sensor.value + (Math.random() - 0.5) * 10))
      }
      
      return {
        ...sensor,
        value: Math.round(newValue * 10) / 10,
        lastReading: new Date(),
        battery: Math.max(0, sensor.battery - (Math.random() > 0.95 ? 1 : 0))
      }
    }))
    
    setLastUpdate(new Date())
  }, [])
  
  // Real-time update interval
  useEffect(() => {
    if (!isLive) return
    const interval = setInterval(updateRealTimeData, 3000)
    return () => clearInterval(interval)
  }, [isLive, updateRealTimeData])
  const [isLocating, setIsLocating] = useState(false)

  // Get operator's location on mount
  useEffect(() => {
    getOperatorLocation()
  }, [])

  const getOperatorLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported')
      return
    }

    setIsLocating(true)
    setLocationError(null)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setOperatorLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: new Date(),
          name: 'You (Operator)'
        })
        setIsLocating(false)
      },
      (error) => {
        console.error('Location error:', error)
        setLocationError(error.message)
        setIsLocating(false)
        // Fallback to Lusaka center if location fails
        setOperatorLocation({
          lat: -15.4167,
          lng: 28.2833,
          accuracy: 1000,
          timestamp: new Date(),
          name: 'You (Location unavailable)'
        })
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    )
  }

  // Watch position for real-time updates
  useEffect(() => {
    if (!navigator.geolocation) return

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setOperatorLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: new Date(),
          name: 'You (Operator)'
        })
      },
      (error) => {
        console.error('Watch position error:', error)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000
      }
    )

    return () => navigator.geolocation.clearWatch(watchId)
  }, [])

  const filteredLeaks = leakData.filter(leak => 
    filter === 'all' || leak.status === filter
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return { bg: 'bg-emerald-500', text: 'text-emerald-600', light: 'bg-emerald-100' }
      case 'moderate': return { bg: 'bg-blue-500', text: 'text-blue-600', light: 'bg-blue-100' }
      case 'warning': return { bg: 'bg-amber-500', text: 'text-amber-600', light: 'bg-amber-100' }
      case 'critical': return { bg: 'bg-red-500', text: 'text-red-600', light: 'bg-red-100' }
      default: return { bg: 'bg-slate-500', text: 'text-slate-600', light: 'bg-slate-100' }
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-500 ring-red-300'
      case 'medium': return 'bg-amber-500 ring-amber-300'
      case 'low': return 'bg-blue-500 ring-blue-300'
      default: return 'bg-slate-500 ring-slate-300'
    }
  }

  const getLeakStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-red-100 text-red-700'
      case 'assigned': return 'bg-amber-100 text-amber-700'
      case 'monitoring': return 'bg-blue-100 text-blue-700'
      case 'repaired': return 'bg-emerald-100 text-emerald-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-2 sm:p-3 md:p-4 lg:p-6">
      {/* Header */}
      <div className="mb-2 sm:mb-3 md:mb-4 lg:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-base sm:text-lg md:text-xl lg:text-3xl font-bold text-slate-900">Network Map</h1>
              <p className="text-[10px] sm:text-xs md:text-sm text-slate-500 mt-0.5">Lusaka water distribution network</p>
            </div>
            {/* Real-time Status */}
            <div className={`flex items-center gap-2 px-2 sm:px-3 py-1 rounded-full ${isLive ? 'bg-green-100' : 'bg-slate-100'}`}>
              {isLive ? (
                <>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  <span className="text-[10px] sm:text-xs font-medium text-green-700">LIVE</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-slate-500" />
                  <span className="text-[10px] sm:text-xs font-medium text-slate-600">Paused</span>
                </>
              )}
            </div>
          </div>
          
          {/* Controls */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Live Toggle */}
            <button
              onClick={() => setIsLive(!isLive)}
              className={`p-1.5 sm:p-2 rounded-lg transition-colors ${isLive ? 'bg-red-100 text-red-600 hover:bg-red-200' : 'bg-green-100 text-green-600 hover:bg-green-200'}`}
              title={isLive ? 'Pause updates' : 'Resume updates'}
            >
              {isLive ? <WifiOff className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
            </button>
            
            {/* Refresh Button */}
            <button
              onClick={updateRealTimeData}
              className="p-1.5 sm:p-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
              title="Refresh now"
            >
              <RefreshCw className="w-4 h-4 text-slate-600" />
            </button>
            
            {/* Last Update */}
            <div className="hidden md:flex items-center gap-1.5 text-[10px] sm:text-xs text-slate-500">
              <Clock className="w-3 h-3" />
              {lastUpdate.toLocaleTimeString()}
            </div>
            
            {/* Layer Toggle */}
            <div className="flex bg-white rounded-lg border border-slate-200 p-0.5 sm:p-1">
              {[
                { id: 'nrw', label: 'NRW Zones', icon: Droplets },
                { id: 'leaks', label: 'Leaks', icon: AlertTriangle },
                { id: 'sensors', label: 'Sensors', icon: Target },
              ].map((l) => (
                <button
                  key={l.id}
                  onClick={() => setLayer(l.id as typeof layer)}
                  className={`flex items-center gap-1 px-2 sm:px-3 py-1 sm:py-1.5 text-[10px] sm:text-xs font-medium rounded-md transition-colors ${
                    layer === l.id 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <l.icon className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">{l.label}</span>
                </button>
              ))}
            </div>
            
            {/* Public View Button */}
            <a
              href="/report-leak"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-[10px] sm:text-xs font-medium rounded-lg transition-colors shadow-sm"
            >
              <ExternalLink className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden xs:inline">Public View</span>
            </a>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
        {/* Map Area */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            {/* Map Container */}
            <div className="relative h-[280px] xs:h-[320px] sm:h-[400px] md:h-[500px] lg:h-[600px] bg-slate-100">
              {/* Simulated Map Background */}
              <div 
                className="absolute inset-0 bg-gradient-to-br from-blue-50 to-cyan-50"
                style={{ 
                  backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2394a3b8' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
                }}
              >
                {/* Roads SVG Overlay */}
                <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {/* Major Roads */}
                  <line x1="20" y1="0" x2="20" y2="100" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="2,2" />
                  <line x1="50" y1="0" x2="50" y2="100" stroke="#94a3b8" strokeWidth="0.8" />
                  <line x1="80" y1="0" x2="80" y2="100" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="2,2" />
                  <line x1="0" y1="30" x2="100" y2="30" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="2,2" />
                  <line x1="0" y1="50" x2="100" y2="50" stroke="#94a3b8" strokeWidth="0.8" />
                  <line x1="0" y1="70" x2="100" y2="70" stroke="#94a3b8" strokeWidth="0.5" strokeDasharray="2,2" />
                  {/* Diagonal Roads */}
                  <line x1="0" y1="0" x2="60" y2="60" stroke="#94a3b8" strokeWidth="0.3" />
                  <line x1="40" y1="0" x2="100" y2="60" stroke="#94a3b8" strokeWidth="0.3" />
                </svg>

                {/* DMA Zones */}
                {layer === 'nrw' && dmaZones.map((dma) => {
                  const x = ((dma.lng - 28.26) / 0.1) * 100
                  const y = ((dma.lat + 15.35) / 0.12) * 100
                  const colors = getStatusColor(dma.status)
                  const isSelected = selectedDMA === dma.id
                  
                  return (
                    <div
                      key={dma.id}
                      onClick={() => setSelectedDMA(isSelected ? null : dma.id)}
                      className={`absolute cursor-pointer transition-all duration-300 ${isSelected ? 'z-20' : 'z-10'}`}
                      style={{ 
                        left: `${Math.min(Math.max(x, 5), 90)}%`, 
                        top: `${Math.min(Math.max(y, 5), 90)}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    >
                      {/* Zone Circle */}
                      <div className={`relative ${isSelected ? 'scale-110' : 'hover:scale-105'} transition-transform`}>
                        <div className={`w-12 h-12 sm:w-16 sm:h-16 rounded-full ${colors.light} ${colors.bg}/30 border-2 ${colors.bg.replace('bg-', 'border-')} flex items-center justify-center`}>
                          <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full ${colors.bg} flex items-center justify-center text-white font-bold text-xs sm:text-sm`}>
                            {dma.nrw.toFixed(0)}%
                          </div>
                        </div>
                        {/* Label */}
                        <div className={`absolute -bottom-5 sm:-bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap px-2 py-0.5 rounded text-[8px] sm:text-[10px] font-medium ${isSelected ? colors.bg + ' text-white' : 'bg-white shadow-sm text-slate-700'}`}>
                          {dma.name}
                        </div>
                        {/* Pulse for critical */}
                        {dma.status === 'critical' && (
                          <div className={`absolute inset-0 w-12 h-12 sm:w-16 sm:h-16 rounded-full ${colors.bg} animate-ping opacity-30`} />
                        )}
                      </div>
                    </div>
                  )
                })}

                {/* Leak Markers */}
                {layer === 'leaks' && filteredLeaks.map((leak) => {
                  const x = ((leak.lng - 28.26) / 0.1) * 100
                  const y = ((leak.lat + 15.35) / 0.12) * 100
                  const isSelected = selectedLeak?.id === leak.id
                  
                  return (
                    <div
                      key={leak.id}
                      onClick={() => setSelectedLeak(isSelected ? null : leak)}
                      className={`absolute cursor-pointer transition-all duration-300 ${isSelected ? 'z-20' : 'z-10'}`}
                      style={{ 
                        left: `${Math.min(Math.max(x, 5), 90)}%`, 
                        top: `${Math.min(Math.max(y, 5), 90)}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    >
                      <div className={`relative ${isSelected ? 'scale-125' : 'hover:scale-110'} transition-transform`}>
                        <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full ${getSeverityColor(leak.severity)} ring-4 flex items-center justify-center shadow-lg`}>
                          <AlertTriangle className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                        </div>
                        {leak.status === 'active' && (
                          <div className={`absolute inset-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-red-500 animate-ping opacity-50`} />
                        )}
                      </div>
                    </div>
                  )
                })}

                {/* Sensor Markers - Real-time data */}
                {layer === 'sensors' && sensorData.map((sensor) => {
                  const x = ((sensor.lng - 28.26) / 0.1) * 100
                  const y = ((sensor.lat + 15.35) / 0.12) * 100
                  const isSelected = selectedSensor?.id === sensor.id
                  
                  const getSensorColor = () => {
                    if (sensor.status === 'offline') return 'bg-slate-500 ring-slate-300'
                    if (sensor.status === 'warning') return 'bg-amber-500 ring-amber-300'
                    return sensor.type === 'flow' ? 'bg-cyan-500 ring-cyan-300' :
                           sensor.type === 'pressure' ? 'bg-purple-500 ring-purple-300' :
                           'bg-orange-500 ring-orange-300'
                  }
                  
                  const getSensorIcon = () => {
                    if (sensor.type === 'flow') return <Activity className="w-3 h-3 text-white" />
                    if (sensor.type === 'pressure') return <Gauge className="w-3 h-3 text-white" />
                    return <Target className="w-3 h-3 text-white" />
                  }
                  
                  return (
                    <div
                      key={sensor.id}
                      onClick={() => setSelectedSensor(isSelected ? null : sensor)}
                      className={`absolute cursor-pointer transition-all duration-300 ${isSelected ? 'z-20' : 'z-10'}`}
                      style={{ 
                        left: `${Math.min(Math.max(x, 5), 90)}%`, 
                        top: `${Math.min(Math.max(y, 5), 90)}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    >
                      <div className={`relative ${isSelected ? 'scale-125' : 'hover:scale-110'} transition-transform`}>
                        <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full ${getSensorColor()} ring-2 flex items-center justify-center shadow-lg`}>
                          {getSensorIcon()}
                        </div>
                        {sensor.status === 'online' && isLive && (
                          <div className={`absolute -top-1 -right-1 w-2 h-2 rounded-full bg-green-500 animate-pulse`} />
                        )}
                        {sensor.status === 'offline' && (
                          <div className={`absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500`} />
                        )}
                        {/* Value label on hover/select */}
                        {isSelected && (
                          <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap px-2 py-1 rounded bg-slate-900 text-white text-[9px] font-mono shadow-lg">
                            {sensor.value} {sensor.unit}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}

                {/* Operator Location Marker */}
                {operatorLocation && (() => {
                  const x = ((operatorLocation.lng - 28.26) / 0.1) * 100
                  const y = ((operatorLocation.lat + 15.35) / 0.12) * 100
                  
                  return (
                    <div
                      className="absolute z-30 cursor-pointer"
                      style={{ 
                        left: `${Math.min(Math.max(x, 5), 95)}%`, 
                        top: `${Math.min(Math.max(y, 5), 95)}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    >
                      {/* Accuracy circle */}
                      <div 
                        className="absolute rounded-full bg-green-500/20 border-2 border-green-500/40 animate-pulse"
                        style={{
                          width: `${Math.min(operatorLocation.accuracy / 10, 80)}px`,
                          height: `${Math.min(operatorLocation.accuracy / 10, 80)}px`,
                          left: '50%',
                          top: '50%',
                          transform: 'translate(-50%, -50%)'
                        }}
                      />
                      {/* Operator marker */}
                      <div className="relative">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-green-600 ring-4 ring-green-300 ring-opacity-60 flex items-center justify-center shadow-lg border-2 border-white">
                          <User className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                        </div>
                        {/* Pulse animation */}
                        <div className="absolute inset-0 w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-green-500 animate-ping opacity-30" />
                        {/* Label */}
                        <div className="absolute -bottom-7 left-1/2 -translate-x-1/2 whitespace-nowrap px-2 py-1 rounded-full bg-green-600 text-white text-[9px] sm:text-[10px] font-semibold shadow-lg">
                          📍 Your Location
                        </div>
                      </div>
                    </div>
                  )
                })()}
              </div>

              {/* Map Controls */}
              <div className="absolute top-3 right-3 flex flex-col gap-2">
                <button className="w-8 h-8 sm:w-10 sm:h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-slate-50 transition-colors">
                  <ZoomIn className="w-4 h-4 sm:w-5 sm:h-5 text-slate-600" />
                </button>
                <button className="w-8 h-8 sm:w-10 sm:h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-slate-50 transition-colors">
                  <ZoomOut className="w-4 h-4 sm:w-5 sm:h-5 text-slate-600" />
                </button>
                <button className="w-8 h-8 sm:w-10 sm:h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-slate-50 transition-colors">
                  <Maximize2 className="w-4 h-4 sm:w-5 sm:h-5 text-slate-600" />
                </button>
                <button 
                  onClick={getOperatorLocation}
                  className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg shadow-md flex items-center justify-center transition-colors ${
                    isLocating ? 'bg-green-100' : operatorLocation ? 'bg-green-50 hover:bg-green-100' : 'bg-white hover:bg-slate-50'
                  }`}
                  title="Center on your location"
                >
                  <Locate className={`w-4 h-4 sm:w-5 sm:h-5 ${isLocating ? 'text-green-600 animate-pulse' : operatorLocation ? 'text-green-600' : 'text-slate-600'}`} />
                </button>
              </div>

              {/* Operator Location Info Banner */}
              {operatorLocation && (
                <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-md p-2 sm:p-3 max-w-[200px] sm:max-w-[250px]">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-green-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] sm:text-xs font-semibold text-slate-900 truncate">Operator Online</p>
                      <p className="text-[8px] sm:text-[10px] text-slate-500">
                        {operatorLocation.lat.toFixed(4)}°S, {operatorLocation.lng.toFixed(4)}°E
                      </p>
                    </div>
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  </div>
                  <p className="text-[8px] sm:text-[10px] text-slate-400 mt-1">
                    Accuracy: ±{operatorLocation.accuracy.toFixed(0)}m • Updated: {operatorLocation.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              )}

              {/* Legend */}
              <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-md p-2 sm:p-3">
                <p className="text-[10px] sm:text-xs font-semibold text-slate-700 mb-2">
                  {layer === 'nrw' ? 'NRW Rate' : layer === 'leaks' ? 'Leak Severity' : 'Sensor Status'}
                </p>
                {layer === 'nrw' ? (
                  <div className="space-y-1">
                    {[
                      { label: 'Good (<25%)', color: 'bg-emerald-500' },
                      { label: 'Moderate (25-35%)', color: 'bg-blue-500' },
                      { label: 'Warning (35-45%)', color: 'bg-amber-500' },
                      { label: 'Critical (>45%)', color: 'bg-red-500' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${item.color}`} />
                        <span className="text-[9px] sm:text-[11px] text-slate-600">{item.label}</span>
                      </div>
                    ))}
                  </div>
                ) : layer === 'leaks' ? (
                  <div className="space-y-1">
                    {[
                      { label: 'High Priority', color: 'bg-red-500' },
                      { label: 'Medium Priority', color: 'bg-amber-500' },
                      { label: 'Low Priority', color: 'bg-blue-500' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${item.color}`} />
                        <span className="text-[9px] sm:text-[11px] text-slate-600">{item.label}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1">
                    {[
                      { label: 'Online', color: 'bg-cyan-500' },
                      { label: 'Offline', color: 'bg-slate-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${item.color}`} />
                        <span className="text-[9px] sm:text-[11px] text-slate-600">{item.label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Location Label */}
              <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-1.5 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-600" />
                <span className="text-xs sm:text-sm font-medium text-slate-700">Lusaka, Zambia</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* DMA Details */}
          {selectedDMA && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm sm:text-base font-semibold text-slate-900">DMA Details</h3>
                <button onClick={() => setSelectedDMA(null)} className="p-1 hover:bg-slate-100 rounded">
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              {(() => {
                const dma = dmaZones.find(d => d.id === selectedDMA)
                if (!dma) return null
                const colors = getStatusColor(dma.status)
                return (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg ${colors.light} flex items-center justify-center`}>
                        <Droplets className={`w-5 h-5 ${colors.text}`} />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{dma.name}</p>
                        <p className={`text-xs ${colors.text} capitalize`}>{dma.status}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-slate-50 rounded-lg">
                        <p className="text-[10px] text-slate-500">NRW Rate</p>
                        <p className="text-lg font-bold text-slate-900">{dma.nrw}%</p>
                      </div>
                      <div className="p-2 bg-slate-50 rounded-lg">
                        <p className="text-[10px] text-slate-500">Active Leaks</p>
                        <p className="text-lg font-bold text-slate-900">{dma.leaks}</p>
                      </div>
                    </div>
                    <button className="w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors">
                      View Full Report
                    </button>
                  </div>
                )
              })()}
            </div>
          )}

          {/* Leak Details */}
          {selectedLeak && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm sm:text-base font-semibold text-slate-900">Leak Details</h3>
                <button onClick={() => setSelectedLeak(null)} className="p-1 hover:bg-slate-100 rounded">
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getLeakStatusColor(selectedLeak.status)}`}>
                    {selectedLeak.status.charAt(0).toUpperCase() + selectedLeak.status.slice(1)}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    selectedLeak.severity === 'high' ? 'bg-red-100 text-red-700' :
                    selectedLeak.severity === 'medium' ? 'bg-amber-100 text-amber-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>
                    {selectedLeak.severity.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-slate-500 flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> Location
                  </p>
                  <p className="text-sm font-medium text-slate-900">{selectedLeak.location}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-slate-50 rounded-lg">
                    <p className="text-[10px] text-slate-500">Flow Rate</p>
                    <p className="text-sm font-bold text-slate-900">{selectedLeak.flowRate} L/min</p>
                  </div>
                  <div className="p-2 bg-slate-50 rounded-lg">
                    <p className="text-[10px] text-slate-500">Detected</p>
                    <p className="text-sm font-bold text-slate-900">{selectedLeak.detectedAt}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-1">
                    <Wrench className="w-3 h-3" /> Assign Crew
                  </button>
                  <button className="py-2 px-3 border border-slate-200 rounded-lg text-xs font-medium hover:bg-slate-50 transition-colors">
                    <Phone className="w-4 h-4 text-slate-600" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Sensor Details */}
          {selectedSensor && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm sm:text-base font-semibold text-slate-900">Sensor Details</h3>
                <button onClick={() => setSelectedSensor(null)} className="p-1 hover:bg-slate-100 rounded">
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    selectedSensor.status === 'online' ? 'bg-green-100 text-green-700' :
                    selectedSensor.status === 'warning' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {selectedSensor.status.toUpperCase()}
                  </span>
                  <span className="px-2 py-1 rounded text-xs font-medium bg-slate-100 text-slate-700 capitalize">
                    {selectedSensor.type}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-slate-500">{selectedSensor.id}</p>
                  <p className="text-sm font-medium text-slate-900">{selectedSensor.name}</p>
                </div>
                <div className="p-3 bg-gradient-to-r from-cyan-50 to-blue-50 rounded-lg border border-cyan-200">
                  <p className="text-[10px] text-cyan-600 mb-1">Current Reading</p>
                  <p className="text-2xl font-bold text-cyan-700">
                    {selectedSensor.value} <span className="text-sm font-normal">{selectedSensor.unit}</span>
                  </p>
                  {isLive && selectedSensor.status === 'online' && (
                    <div className="flex items-center gap-1 mt-1">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                      </span>
                      <span className="text-[10px] text-green-600">Live</span>
                    </div>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 bg-slate-50 rounded-lg">
                    <p className="text-[10px] text-slate-500 flex items-center gap-1">
                      <Battery className="w-3 h-3" /> Battery
                    </p>
                    <p className={`text-sm font-bold ${
                      selectedSensor.battery > 50 ? 'text-green-600' :
                      selectedSensor.battery > 20 ? 'text-amber-600' :
                      'text-red-600'
                    }`}>{selectedSensor.battery}%</p>
                  </div>
                  <div className="p-2 bg-slate-50 rounded-lg">
                    <p className="text-[10px] text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" /> Last Update
                    </p>
                    <p className="text-sm font-bold text-slate-900">
                      {selectedSensor.lastReading.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <button className="w-full py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors">
                  View Sensor History
                </button>
              </div>
            </div>
          )}

          {/* Quick Stats */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-3">Network Overview</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                <span className="text-xs text-slate-600">Total DMAs</span>
                <span className="text-sm font-bold text-slate-900">{dmaZones.length}</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                <span className="text-xs text-red-600">Critical Zones</span>
                <span className="text-sm font-bold text-red-600">
                  {dmaZones.filter(d => d.status === 'critical').length}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-amber-50 rounded-lg">
                <span className="text-xs text-amber-600">Active Leaks</span>
                <span className="text-sm font-bold text-amber-600">
                  {leakData.filter(l => l.status === 'active').length}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-cyan-50 rounded-lg">
                <span className="text-xs text-cyan-600">Sensors Online</span>
                <span className="text-sm font-bold text-cyan-600">
                  {sensorData.filter(s => s.status === 'online').length}/{sensorData.length}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-emerald-50 rounded-lg">
                <span className="text-xs text-emerald-600">Repaired Today</span>
                <span className="text-sm font-bold text-emerald-600">
                  {leakData.filter(l => l.status === 'repaired').length}
                </span>
              </div>
            </div>
          </div>

          {/* Sensor List when layer is sensors */}
          {layer === 'sensors' && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Sensor Status</h3>
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {sensorData.map(sensor => (
                  <div
                    key={sensor.id}
                    onClick={() => setSelectedSensor(sensor)}
                    className={`p-2 rounded-lg cursor-pointer transition-colors ${
                      selectedSensor?.id === sensor.id ? 'bg-blue-50 border border-blue-200' : 'bg-slate-50 hover:bg-slate-100'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-900">{sensor.name}</span>
                      <div className={`w-2 h-2 rounded-full ${
                        sensor.status === 'online' ? 'bg-green-500' :
                        sensor.status === 'warning' ? 'bg-amber-500' :
                        'bg-red-500'
                      }`} />
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-[10px] text-slate-500">{sensor.type}</span>
                      <span className="text-xs font-mono text-slate-700">{sensor.value} {sensor.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Leak Filter */}
          {layer === 'leaks' && (
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Filter Leaks</h3>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'all', label: 'All' },
                  { id: 'active', label: 'Active' },
                  { id: 'assigned', label: 'Assigned' },
                  { id: 'repaired', label: 'Repaired' },
                ].map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setFilter(f.id as typeof filter)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                      filter === f.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
