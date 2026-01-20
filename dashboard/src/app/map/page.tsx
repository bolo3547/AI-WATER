'use client'

import { useState, useEffect } from 'react'
import { 
  MapPin, Droplets, AlertTriangle, CheckCircle, Clock, 
  Filter, Layers, ZoomIn, ZoomOut, Maximize2, Target,
  Info, X, Navigation, Wrench, Phone, Calendar
} from 'lucide-react'

// DMA zones for Lusaka
const dmaZones = [
  { id: 'woodlands', name: 'Woodlands', nrw: 18.5, status: 'good', lat: -15.385, lng: 28.310, leaks: 2 },
  { id: 'kabulonga', name: 'Kabulonga', nrw: 21.2, status: 'good', lat: -15.408, lng: 28.332, leaks: 3 },
  { id: 'roma', name: 'Roma', nrw: 23.1, status: 'good', lat: -15.422, lng: 28.298, leaks: 1 },
  { id: 'matero', name: 'Matero', nrw: 48.2, status: 'critical', lat: -15.362, lng: 28.278, leaks: 12 },
  { id: 'chilenje', name: 'Chilenje', nrw: 45.8, status: 'critical', lat: -15.445, lng: 28.268, leaks: 8 },
  { id: 'garden', name: 'Garden', nrw: 42.1, status: 'warning', lat: -15.398, lng: 28.285, leaks: 6 },
  { id: 'rhodes-park', name: 'Rhodes Park', nrw: 28.5, status: 'moderate', lat: -15.412, lng: 28.305, leaks: 4 },
  { id: 'olympia', name: 'Olympia', nrw: 35.2, status: 'warning', lat: -15.438, lng: 28.312, leaks: 5 },
  { id: 'kabwata', name: 'Kabwata', nrw: 39.8, status: 'warning', lat: -15.455, lng: 28.285, leaks: 7 },
  { id: 'mtendere', name: 'Mtendere', nrw: 52.3, status: 'critical', lat: -15.448, lng: 28.342, leaks: 14 },
]

// Sample leak data
const leakData = [
  { id: 1, location: 'Great East Rd & Lumumba Rd', dma: 'matero', severity: 'high', status: 'active', flowRate: 45.2, detectedAt: '2025-01-14', lat: -15.360, lng: 28.275 },
  { id: 2, location: 'Independence Ave', dma: 'rhodes-park', severity: 'medium', status: 'assigned', flowRate: 22.8, detectedAt: '2025-01-13', lat: -15.414, lng: 28.308 },
  { id: 3, location: 'Cairo Rd South', dma: 'garden', severity: 'low', status: 'repaired', flowRate: 8.5, detectedAt: '2025-01-12', lat: -15.402, lng: 28.282 },
  { id: 4, location: 'Kafue Rd', dma: 'chilenje', severity: 'high', status: 'active', flowRate: 67.3, detectedAt: '2025-01-15', lat: -15.448, lng: 28.265 },
  { id: 5, location: 'Los Angeles Blvd', dma: 'kabulonga', severity: 'medium', status: 'assigned', flowRate: 18.4, detectedAt: '2025-01-14', lat: -15.405, lng: 28.335 },
  { id: 6, location: 'Manda Hill Area', dma: 'woodlands', severity: 'low', status: 'monitoring', flowRate: 5.2, detectedAt: '2025-01-13', lat: -15.388, lng: 28.315 },
]

export default function MapPage() {
  const [selectedDMA, setSelectedDMA] = useState<string | null>(null)
  const [selectedLeak, setSelectedLeak] = useState<typeof leakData[0] | null>(null)
  const [filter, setFilter] = useState<'all' | 'active' | 'assigned' | 'repaired'>('all')
  const [layer, setLayer] = useState<'nrw' | 'leaks' | 'sensors'>('nrw')
  const [zoom, setZoom] = useState(1)

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
          <div>
            <h1 className="text-base sm:text-lg md:text-xl lg:text-3xl font-bold text-slate-900">Network Map</h1>
            <p className="text-[10px] sm:text-xs md:text-sm text-slate-500 mt-0.5">Lusaka water distribution network</p>
          </div>
          
          {/* Controls */}
          <div className="flex items-center gap-2 sm:gap-3">
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
                      ? 'bg-green-600 text-white' 
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <l.icon className="w-3 h-3 sm:w-4 sm:h-4" />
                  <span className="hidden sm:inline">{l.label}</span>
                </button>
              ))}
            </div>
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

                {/* Sensor Markers */}
                {layer === 'sensors' && Array.from({ length: 15 }).map((_, i) => {
                  const x = 10 + (i % 5) * 20 + Math.random() * 10
                  const y = 15 + Math.floor(i / 5) * 30 + Math.random() * 10
                  
                  return (
                    <div
                      key={i}
                      className="absolute cursor-pointer transition-all hover:scale-110 z-10"
                      style={{ 
                        left: `${x}%`, 
                        top: `${y}%`,
                        transform: 'translate(-50%, -50%)'
                      }}
                    >
                      <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-cyan-500 ring-2 ring-cyan-300 flex items-center justify-center shadow-lg">
                        <Target className="w-3 h-3 sm:w-4 sm:h-4 text-white" />
                      </div>
                    </div>
                  )
                })}
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
                <button className="w-8 h-8 sm:w-10 sm:h-10 bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-slate-50 transition-colors">
                  <Navigation className="w-4 h-4 sm:w-5 sm:h-5 text-slate-600" />
                </button>
              </div>

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
              <div className="flex items-center justify-between p-2 bg-emerald-50 rounded-lg">
                <span className="text-xs text-emerald-600">Repaired Today</span>
                <span className="text-sm font-bold text-emerald-600">
                  {leakData.filter(l => l.status === 'repaired').length}
                </span>
              </div>
            </div>
          </div>

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
