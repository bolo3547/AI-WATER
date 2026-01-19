'use client'

import { useState, useEffect } from 'react'
import { 
  Satellite, Plane, Camera, MapPin, Upload, 
  AlertTriangle, CheckCircle, Clock, ZoomIn, ZoomOut,
  Layers, Filter, Download, Share2, RefreshCw,
  Droplets, Thermometer, CloudRain, Sun, Moon,
  Eye, Target, Grid3X3, BarChart3, Play, Pause
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface ImageAnalysis {
  id: string
  type: 'satellite' | 'drone' | 'thermal'
  location: string
  dma: string
  capturedAt: string
  analysisStatus: 'pending' | 'processing' | 'complete'
  leaksDetected: number
  wetSpots: number
  vegetationAnomalies: number
  thermalAnomalies: number
  coordinates: { lat: number; lng: number }
  confidence: number
  imageUrl: string
  findings: Finding[]
}

interface Finding {
  type: 'leak' | 'wet_spot' | 'vegetation' | 'thermal'
  severity: 'critical' | 'high' | 'medium' | 'low'
  location: { x: number; y: number }
  description: string
  confidence: number
}

interface DroneSchedule {
  id: string
  route: string
  dma: string
  scheduledTime: string
  status: 'scheduled' | 'in_flight' | 'completed' | 'cancelled'
  coverage: number
  estimatedDuration: number
}

export default function SatellitePage() {
  const [activeTab, setActiveTab] = useState('analysis')
  const [analyses, setAnalyses] = useState<ImageAnalysis[]>([])
  const [droneSchedules, setDroneSchedules] = useState<DroneSchedule[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<ImageAnalysis | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [viewMode, setViewMode] = useState<'satellite' | 'thermal' | 'ndvi'>('satellite')

  // Load data
  useEffect(() => {
    loadAnalyses()
    loadDroneSchedules()
  }, [])

  const loadAnalyses = () => {
    setAnalyses([
      {
        id: 'SAT-001',
        type: 'satellite',
        location: 'Kabulonga District',
        dma: 'Kabulonga',
        capturedAt: '2026-01-28 09:30',
        analysisStatus: 'complete',
        leaksDetected: 3,
        wetSpots: 7,
        vegetationAnomalies: 2,
        thermalAnomalies: 4,
        coordinates: { lat: -15.4192, lng: 28.3225 },
        confidence: 94,
        imageUrl: '/satellite/kabulonga.jpg',
        findings: [
          { type: 'leak', severity: 'critical', location: { x: 45, y: 30 }, description: 'Active surface leak', confidence: 96 },
          { type: 'wet_spot', severity: 'high', location: { x: 60, y: 55 }, description: 'Persistent wet area', confidence: 88 },
          { type: 'vegetation', severity: 'medium', location: { x: 25, y: 70 }, description: 'Abnormal vegetation growth', confidence: 82 }
        ]
      },
      {
        id: 'DRN-002',
        type: 'drone',
        location: 'Roma Township Main Road',
        dma: 'Roma',
        capturedAt: '2026-01-27 14:15',
        analysisStatus: 'complete',
        leaksDetected: 2,
        wetSpots: 4,
        vegetationAnomalies: 1,
        thermalAnomalies: 3,
        coordinates: { lat: -15.3958, lng: 28.3108 },
        confidence: 97,
        imageUrl: '/drone/roma.jpg',
        findings: [
          { type: 'leak', severity: 'high', location: { x: 35, y: 40 }, description: 'Underground leak indication', confidence: 92 },
          { type: 'thermal', severity: 'critical', location: { x: 70, y: 45 }, description: 'Temperature anomaly detected', confidence: 95 }
        ]
      },
      {
        id: 'THM-003',
        type: 'thermal',
        location: 'Chelstone Industrial',
        dma: 'Chelstone',
        capturedAt: '2026-01-27 02:30',
        analysisStatus: 'complete',
        leaksDetected: 5,
        wetSpots: 8,
        vegetationAnomalies: 0,
        thermalAnomalies: 6,
        coordinates: { lat: -15.3605, lng: 28.3517 },
        confidence: 91,
        imageUrl: '/thermal/chelstone.jpg',
        findings: [
          { type: 'thermal', severity: 'critical', location: { x: 20, y: 25 }, description: 'Major thermal signature', confidence: 98 },
          { type: 'thermal', severity: 'high', location: { x: 55, y: 60 }, description: 'Water flow detected', confidence: 89 }
        ]
      },
      {
        id: 'SAT-004',
        type: 'satellite',
        location: 'Matero District',
        dma: 'Matero',
        capturedAt: '2026-01-26 10:00',
        analysisStatus: 'processing',
        leaksDetected: 0,
        wetSpots: 0,
        vegetationAnomalies: 0,
        thermalAnomalies: 0,
        coordinates: { lat: -15.3747, lng: 28.2633 },
        confidence: 0,
        imageUrl: '/satellite/matero.jpg',
        findings: []
      }
    ])
  }

  const loadDroneSchedules = () => {
    setDroneSchedules([
      {
        id: 'FLT-001',
        route: 'Kabulonga Full Survey',
        dma: 'Kabulonga',
        scheduledTime: '2026-01-30 06:00',
        status: 'scheduled',
        coverage: 100,
        estimatedDuration: 45
      },
      {
        id: 'FLT-002',
        route: 'Roma-Chelstone Corridor',
        dma: 'Roma/Chelstone',
        scheduledTime: '2026-01-30 08:00',
        status: 'scheduled',
        coverage: 85,
        estimatedDuration: 60
      },
      {
        id: 'FLT-003',
        route: 'Woodlands Night Thermal',
        dma: 'Woodlands',
        scheduledTime: '2026-01-29 22:00',
        status: 'in_flight',
        coverage: 65,
        estimatedDuration: 35
      },
      {
        id: 'FLT-004',
        route: 'Chilenje Inspection',
        dma: 'Chilenje',
        scheduledTime: '2026-01-29 07:00',
        status: 'completed',
        coverage: 100,
        estimatedDuration: 40
      }
    ])
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'satellite': return <Satellite className="w-5 h-5 text-blue-600" />
      case 'drone': return <Plane className="w-5 h-5 text-green-600" />
      case 'thermal': return <Thermometer className="w-5 h-5 text-red-600" />
      default: return <Camera className="w-5 h-5" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
      case 'completed':
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs">Complete</span>
      case 'processing':
      case 'in_flight':
        return <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs animate-pulse">{status === 'in_flight' ? 'In Flight' : 'Processing'}</span>
      case 'scheduled':
        return <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs">Scheduled</span>
      case 'cancelled':
        return <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">Cancelled</span>
      default:
        return <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-xs">{status}</span>
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const filteredAnalyses = filterType 
    ? analyses.filter(a => a.type === filterType)
    : analyses

  const totalLeaks = analyses.reduce((sum, a) => sum + a.leaksDetected, 0)
  const totalWetSpots = analyses.reduce((sum, a) => sum + a.wetSpots, 0)
  const avgConfidence = Math.round(analyses.filter(a => a.confidence > 0).reduce((sum, a) => sum + a.confidence, 0) / analyses.filter(a => a.confidence > 0).length)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Satellite className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />
            Satellite & Drone Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AI-powered image analysis for leak detection
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary">
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Upload Image</span>
          </Button>
          <Button variant="primary">
            <Plane className="w-4 h-4" />
            Schedule Drone
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{totalLeaks}</p>
              <p className="text-xs text-slate-500">Leaks Detected</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Droplets className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{totalWetSpots}</p>
              <p className="text-xs text-slate-500">Wet Spots</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <Target className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{avgConfidence}%</p>
              <p className="text-xs text-slate-500">Avg Confidence</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Plane className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{droneSchedules.filter(d => d.status === 'in_flight').length}</p>
              <p className="text-xs text-slate-500">Drones Active</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'analysis', label: 'Image Analysis' },
          { id: 'drones', label: 'Drone Fleet' },
          { id: 'live', label: 'Live View' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'analysis' && (
        <>
          {/* Filters */}
          <div className="flex items-center gap-3">
            <Select
              value={filterType}
              options={[
                { value: '', label: 'All Types' },
                { value: 'satellite', label: '🛰️ Satellite' },
                { value: 'drone', label: '🚁 Drone' },
                { value: 'thermal', label: '🌡️ Thermal' }
              ]}
              onChange={setFilterType}
            />
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('satellite')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'satellite' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                RGB
              </button>
              <button
                onClick={() => setViewMode('thermal')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'thermal' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                Thermal
              </button>
              <button
                onClick={() => setViewMode('ndvi')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === 'ndvi' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                NDVI
              </button>
            </div>
          </div>

          {/* Analyses Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAnalyses.map((analysis) => (
              <div 
                key={analysis.id}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-lg transition-all cursor-pointer"
                onClick={() => setSelectedAnalysis(analysis)}
              >
                {/* Image Preview */}
                <div className="aspect-video bg-gradient-to-br from-slate-200 to-slate-300 relative">
                  {/* Simulated satellite/drone image */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Grid3X3 className="w-16 h-16 text-slate-400" />
                  </div>
                  
                  {/* Analysis overlay markers */}
                  {analysis.findings.map((finding, idx) => (
                    <div
                      key={idx}
                      className={`absolute w-4 h-4 rounded-full ${getSeverityColor(finding.severity)} animate-ping`}
                      style={{ left: `${finding.location.x}%`, top: `${finding.location.y}%` }}
                    />
                  ))}
                  
                  {/* Type badge */}
                  <div className="absolute top-2 left-2">
                    <span className="px-2 py-1 bg-black/60 text-white rounded-lg text-xs flex items-center gap-1">
                      {getTypeIcon(analysis.type)}
                      {analysis.type}
                    </span>
                  </div>
                  
                  {/* Status badge */}
                  <div className="absolute top-2 right-2">
                    {getStatusBadge(analysis.analysisStatus)}
                  </div>

                  {/* Processing overlay */}
                  {analysis.analysisStatus === 'processing' && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <div className="text-center text-white">
                        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                        <p className="text-sm">AI Processing...</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs text-slate-400">{analysis.id}</span>
                    <span className="text-xs text-slate-500">{analysis.capturedAt}</span>
                  </div>
                  <h3 className="font-semibold text-slate-900">{analysis.location}</h3>
                  <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                    <MapPin className="w-3 h-3" /> {analysis.dma} DMA
                  </p>

                  {analysis.analysisStatus === 'complete' && (
                    <div className="mt-3 grid grid-cols-4 gap-2">
                      <div className="text-center p-2 bg-red-50 rounded-lg">
                        <p className="text-lg font-bold text-red-600">{analysis.leaksDetected}</p>
                        <p className="text-[10px] text-red-500">Leaks</p>
                      </div>
                      <div className="text-center p-2 bg-blue-50 rounded-lg">
                        <p className="text-lg font-bold text-blue-600">{analysis.wetSpots}</p>
                        <p className="text-[10px] text-blue-500">Wet</p>
                      </div>
                      <div className="text-center p-2 bg-green-50 rounded-lg">
                        <p className="text-lg font-bold text-green-600">{analysis.vegetationAnomalies}</p>
                        <p className="text-[10px] text-green-500">Veg</p>
                      </div>
                      <div className="text-center p-2 bg-orange-50 rounded-lg">
                        <p className="text-lg font-bold text-orange-600">{analysis.thermalAnomalies}</p>
                        <p className="text-[10px] text-orange-500">Thermal</p>
                      </div>
                    </div>
                  )}

                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-xs text-slate-500">Confidence</span>
                    <span className="text-sm font-semibold text-slate-900">{analysis.confidence}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'drones' && (
        <SectionCard title="Drone Fleet Status" subtitle="Scheduled and active drone flights">
          <div className="space-y-3">
            {droneSchedules.map((drone) => (
              <div key={drone.id} className="bg-slate-50 rounded-xl p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      drone.status === 'in_flight' ? 'bg-green-100' : 
                      drone.status === 'completed' ? 'bg-blue-100' : 'bg-yellow-100'
                    }`}>
                      <Plane className={`w-6 h-6 ${
                        drone.status === 'in_flight' ? 'text-green-600 animate-pulse' : 
                        drone.status === 'completed' ? 'text-blue-600' : 'text-yellow-600'
                      }`} />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{drone.route}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-500">{drone.dma}</span>
                        {getStatusBadge(drone.status)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-900">{drone.scheduledTime}</p>
                      <p className="text-xs text-slate-500">{drone.estimatedDuration} min</p>
                    </div>
                    {drone.status === 'in_flight' && (
                      <div className="w-24">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate-500">Progress</span>
                          <span className="font-semibold">{drone.coverage}%</span>
                        </div>
                        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full transition-all"
                            style={{ width: `${drone.coverage}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {drone.status === 'scheduled' && (
                      <Button variant="secondary" size="sm">
                        <Play className="w-4 h-4" />
                        Launch
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {activeTab === 'live' && (
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 sm:p-6 min-h-[400px]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-white font-semibold">Live Drone Feed</span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm">
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button variant="secondary" size="sm">
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button variant="secondary" size="sm">
                <Layers className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <div className="aspect-video bg-black/50 rounded-lg flex items-center justify-center">
            <div className="text-center text-slate-400">
              <Camera className="w-16 h-16 mx-auto mb-3" />
              <p>Drone live feed will appear here</p>
              <p className="text-sm mt-1">Connect to active drone to view</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold">65%</p>
              <p className="text-slate-400 text-xs">Coverage</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold">12:45</p>
              <p className="text-slate-400 text-xs">Flight Time</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold">78%</p>
              <p className="text-slate-400 text-xs">Battery</p>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Detail Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    {getTypeIcon(selectedAnalysis.type)}
                    <span className="font-mono text-sm text-slate-400">{selectedAnalysis.id}</span>
                    {getStatusBadge(selectedAnalysis.analysisStatus)}
                  </div>
                  <h2 className="text-xl font-bold text-slate-900 mt-1">{selectedAnalysis.location}</h2>
                  <p className="text-slate-500">{selectedAnalysis.dma} DMA • {selectedAnalysis.capturedAt}</p>
                </div>
                <button 
                  onClick={() => setSelectedAnalysis(null)}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6">
              {/* Image with markers */}
              <div className="aspect-video bg-gradient-to-br from-slate-200 to-slate-300 rounded-xl relative mb-6 overflow-hidden">
                <div className="absolute inset-0 flex items-center justify-center">
                  <Grid3X3 className="w-24 h-24 text-slate-400" />
                </div>
                {selectedAnalysis.findings.map((finding, idx) => (
                  <div
                    key={idx}
                    className="absolute group cursor-pointer"
                    style={{ left: `${finding.location.x}%`, top: `${finding.location.y}%` }}
                  >
                    <div className={`w-6 h-6 rounded-full ${getSeverityColor(finding.severity)} flex items-center justify-center text-white text-xs font-bold`}>
                      {idx + 1}
                    </div>
                    <div className="absolute left-8 top-0 bg-black/80 text-white px-2 py-1 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                      {finding.description}
                    </div>
                  </div>
                ))}
              </div>

              {/* Findings */}
              <h3 className="font-semibold text-slate-900 mb-3">AI Findings ({selectedAnalysis.findings.length})</h3>
              <div className="space-y-2 mb-6">
                {selectedAnalysis.findings.map((finding, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className={`w-8 h-8 rounded-full ${getSeverityColor(finding.severity)} flex items-center justify-center text-white font-bold`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-slate-900">{finding.description}</p>
                      <p className="text-sm text-slate-500">
                        {finding.type.replace('_', ' ')} • {finding.confidence}% confidence
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      finding.severity === 'critical' ? 'bg-red-100 text-red-700' :
                      finding.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                      finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {finding.severity}
                    </span>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary">
                  Create Work Orders
                </Button>
                <Button variant="secondary">
                  <Download className="w-4 h-4" />
                  Download Report
                </Button>
                <Button variant="secondary">
                  <Share2 className="w-4 h-4" />
                  Share
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
