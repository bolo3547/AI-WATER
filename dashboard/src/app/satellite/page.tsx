'use client'

import { useState, useEffect } from 'react'
import { 
  Satellite, Plane, Camera, MapPin, Upload, 
  AlertTriangle, CheckCircle, Clock, ZoomIn, ZoomOut,
  Layers, Filter, Download, Share2, RefreshCw,
  Droplets, Thermometer, CloudRain, Sun, Moon,
  Eye, Target, Grid3X3, BarChart3, Play, Pause,
  Calendar, Battery, Signal, Navigation, FileText
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface ImageAnalysis {
  id: string
  type: 'satellite' | 'drone' | 'thermal'
  source: string
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
  areaSize: number
  resolution: string
  findings: Finding[]
}

interface Finding {
  type: 'leak' | 'wet_spot' | 'vegetation' | 'thermal' | 'infrastructure'
  severity: 'critical' | 'high' | 'medium' | 'low'
  location: { x: number; y: number }
  coordinates: { lat: number; lng: number }
  description: string
  estimatedLoss: number
  confidence: number
  address: string
}

interface DroneAsset {
  id: string
  name: string
  model: string
  status: 'available' | 'in_flight' | 'charging' | 'maintenance'
  battery: number
  lastFlight: string
  totalFlights: number
  currentMission?: string
  location: { lat: number; lng: number }
}

interface DroneSchedule {
  id: string
  route: string
  dma: string
  scheduledTime: string
  status: 'scheduled' | 'in_flight' | 'completed' | 'cancelled'
  coverage: number
  estimatedDuration: number
  droneId: string
  priority: 'routine' | 'urgent' | 'emergency'
  operator: string
}

export default function SatellitePage() {
  const [activeTab, setActiveTab] = useState('analysis')
  const [analyses, setAnalyses] = useState<ImageAnalysis[]>([])
  const [droneSchedules, setDroneSchedules] = useState<DroneSchedule[]>([])
  const [droneAssets, setDroneAssets] = useState<DroneAsset[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<ImageAnalysis | null>(null)
  const [filterType, setFilterType] = useState('')
  const [viewMode, setViewMode] = useState<'satellite' | 'thermal' | 'ndvi'>('satellite')
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    loadAnalyses()
    loadDroneSchedules()
    loadDroneAssets()
  }, [])

  const loadAnalyses = () => {
    // Real Lusaka locations with actual GPS coordinates
    setAnalyses([
      {
        id: 'SAT-2026-0120-001',
        type: 'satellite',
        source: 'Sentinel-2 MSI',
        location: 'Kabulonga Shopping Area - Los Angeles Boulevard',
        dma: 'DMA-KAB-01',
        capturedAt: '2026-01-20 06:45 CAT',
        analysisStatus: 'complete',
        leaksDetected: 4,
        wetSpots: 12,
        vegetationAnomalies: 3,
        thermalAnomalies: 6,
        coordinates: { lat: -15.4089, lng: 28.3142 },
        confidence: 94,
        areaSize: 2.8,
        resolution: '10m multispectral',
        findings: [
          { type: 'leak', severity: 'critical', location: { x: 35, y: 28 }, coordinates: { lat: -15.4092, lng: 28.3138 }, description: 'Major transmission main leak - visible surface water', estimatedLoss: 450, confidence: 97, address: 'Plot 4521, Los Angeles Boulevard' },
          { type: 'leak', severity: 'high', location: { x: 58, y: 42 }, coordinates: { lat: -15.4085, lng: 28.3155 }, description: 'Distribution pipe leak near junction', estimatedLoss: 180, confidence: 91, address: 'Kabulonga Water Works Road' },
          { type: 'wet_spot', severity: 'medium', location: { x: 72, y: 65 }, coordinates: { lat: -15.4078, lng: 28.3168 }, description: 'Persistent wet area - possible underground leak', estimatedLoss: 85, confidence: 78, address: 'Behind Kabulonga Boys Secondary' },
          { type: 'vegetation', severity: 'low', location: { x: 22, y: 80 }, coordinates: { lat: -15.4102, lng: 28.3125 }, description: 'Abnormal vegetation growth pattern indicating moisture', estimatedLoss: 35, confidence: 72, address: 'Residential area off Lukasu Road' }
        ]
      },
      {
        id: 'DRN-2026-0119-003',
        type: 'drone',
        source: 'LWSC DJI Matrice 300 RTK',
        location: 'Chilenje South - Kafue Road Junction',
        dma: 'DMA-CHI-02',
        capturedAt: '2026-01-19 14:22 CAT',
        analysisStatus: 'complete',
        leaksDetected: 3,
        wetSpots: 8,
        vegetationAnomalies: 1,
        thermalAnomalies: 5,
        coordinates: { lat: -15.4298, lng: 28.2876 },
        confidence: 97,
        areaSize: 0.8,
        resolution: '2cm RGB + Thermal',
        findings: [
          { type: 'leak', severity: 'critical', location: { x: 45, y: 35 }, coordinates: { lat: -15.4301, lng: 28.2879 }, description: 'Service connection leak at meter box', estimatedLoss: 120, confidence: 98, address: 'House No. 2341, Chilenje South' },
          { type: 'thermal', severity: 'high', location: { x: 62, y: 48 }, coordinates: { lat: -15.4295, lng: 28.2885 }, description: 'Thermal anomaly indicating underground water flow', estimatedLoss: 200, confidence: 94, address: 'Kafue Road Service Lane' },
          { type: 'infrastructure', severity: 'medium', location: { x: 28, y: 72 }, coordinates: { lat: -15.4305, lng: 28.2868 }, description: 'Deteriorated valve chamber - potential leak point', estimatedLoss: 45, confidence: 86, address: 'Corner of Chilenje Road' }
        ]
      },
      {
        id: 'THM-2026-0119-007',
        type: 'thermal',
        source: 'LWSC Night Thermal Survey',
        location: 'Matero Main - Great North Road',
        dma: 'DMA-MAT-01',
        capturedAt: '2026-01-19 02:15 CAT',
        analysisStatus: 'complete',
        leaksDetected: 7,
        wetSpots: 15,
        vegetationAnomalies: 0,
        thermalAnomalies: 11,
        coordinates: { lat: -15.3789, lng: 28.2654 },
        confidence: 92,
        areaSize: 1.5,
        resolution: 'FLIR 640x512 thermal',
        findings: [
          { type: 'thermal', severity: 'critical', location: { x: 25, y: 30 }, coordinates: { lat: -15.3792, lng: 28.2648 }, description: 'Major thermal signature - large volume leak', estimatedLoss: 580, confidence: 96, address: 'Great North Road, near Matero Market' },
          { type: 'thermal', severity: 'critical', location: { x: 55, y: 45 }, coordinates: { lat: -15.3785, lng: 28.2662 }, description: 'Underground main break - cooling signature', estimatedLoss: 420, confidence: 93, address: 'Matero Main Road' },
          { type: 'thermal', severity: 'high', location: { x: 78, y: 62 }, coordinates: { lat: -15.3778, lng: 28.2675 }, description: 'Service connection thermal anomaly', estimatedLoss: 150, confidence: 88, address: 'Plot 892, Matero East' }
        ]
      },
      {
        id: 'SAT-2026-0118-012',
        type: 'satellite',
        source: 'Planet Labs SkySat',
        location: 'Roma Township - Leopards Hill Road',
        dma: 'DMA-ROM-01',
        capturedAt: '2026-01-18 07:30 CAT',
        analysisStatus: 'complete',
        leaksDetected: 2,
        wetSpots: 6,
        vegetationAnomalies: 4,
        thermalAnomalies: 3,
        coordinates: { lat: -15.4156, lng: 28.3278 },
        confidence: 89,
        areaSize: 3.2,
        resolution: '50cm panchromatic',
        findings: [
          { type: 'leak', severity: 'high', location: { x: 42, y: 38 }, coordinates: { lat: -15.4162, lng: 28.3285 }, description: 'Visible water ponding at road intersection', estimatedLoss: 210, confidence: 92, address: 'Leopards Hill Road / Twin Palm Road Junction' },
          { type: 'vegetation', severity: 'medium', location: { x: 68, y: 55 }, coordinates: { lat: -15.4148, lng: 28.3295 }, description: 'NDVI anomaly - excess moisture zone', estimatedLoss: 65, confidence: 81, address: 'Roma Park Residential' }
        ]
      },
      {
        id: 'DRN-2026-0120-015',
        type: 'drone',
        source: 'LWSC DJI Phantom 4 RTK',
        location: 'Woodlands Extension - Off Makishi Road',
        dma: 'DMA-WDL-02',
        capturedAt: '2026-01-20 08:45 CAT',
        analysisStatus: 'processing',
        leaksDetected: 0,
        wetSpots: 0,
        vegetationAnomalies: 0,
        thermalAnomalies: 0,
        coordinates: { lat: -15.4012, lng: 28.3389 },
        confidence: 0,
        areaSize: 0.6,
        resolution: '1.5cm RGB',
        findings: []
      },
      {
        id: 'SAT-2026-0117-008',
        type: 'satellite',
        source: 'Maxar WorldView-3',
        location: 'Chelstone - Birdcage Walk Area',
        dma: 'DMA-CHL-01',
        capturedAt: '2026-01-17 09:15 CAT',
        analysisStatus: 'complete',
        leaksDetected: 5,
        wetSpots: 9,
        vegetationAnomalies: 2,
        thermalAnomalies: 4,
        coordinates: { lat: -15.3654, lng: 28.3512 },
        confidence: 91,
        areaSize: 2.1,
        resolution: '31cm multispectral',
        findings: [
          { type: 'leak', severity: 'critical', location: { x: 38, y: 25 }, coordinates: { lat: -15.3658, lng: 28.3508 }, description: 'Burst main - significant surface flow', estimatedLoss: 520, confidence: 95, address: 'Birdcage Walk, near Chelstone Mall' },
          { type: 'wet_spot', severity: 'high', location: { x: 52, y: 48 }, coordinates: { lat: -15.3648, lng: 28.3522 }, description: 'Saturated ground - multiple small leaks', estimatedLoss: 180, confidence: 87, address: 'Chelstone Primary School Area' }
        ]
      }
    ])
  }

  const loadDroneAssets = () => {
    setDroneAssets([
      { id: 'LWSC-DRN-001', name: 'Alpha-1', model: 'DJI Matrice 300 RTK', status: 'in_flight', battery: 68, lastFlight: '2026-01-20 08:30', totalFlights: 247, currentMission: 'Woodlands Extension Survey', location: { lat: -15.4012, lng: 28.3389 } },
      { id: 'LWSC-DRN-002', name: 'Bravo-2', model: 'DJI Phantom 4 RTK', status: 'available', battery: 100, lastFlight: '2026-01-19 16:45', totalFlights: 189, location: { lat: -15.4167, lng: 28.2833 } },
      { id: 'LWSC-DRN-003', name: 'Charlie-3', model: 'DJI Mavic 3 Enterprise', status: 'charging', battery: 45, lastFlight: '2026-01-20 06:15', totalFlights: 156, location: { lat: -15.4167, lng: 28.2833 } },
      { id: 'LWSC-DRN-004', name: 'Delta-4', model: 'senseFly eBee X', status: 'maintenance', battery: 0, lastFlight: '2026-01-15 09:30', totalFlights: 312, location: { lat: -15.4167, lng: 28.2833 } },
      { id: 'LWSC-DRN-005', name: 'Echo-5', model: 'DJI Matrice 30T', status: 'available', battery: 95, lastFlight: '2026-01-19 22:30', totalFlights: 98, location: { lat: -15.4167, lng: 28.2833 } }
    ])
  }

  const loadDroneSchedules = () => {
    setDroneSchedules([
      { id: 'MSN-2026-0120-001', route: 'Kalingalinga Full Coverage Survey', dma: 'DMA-KLG-01', scheduledTime: '2026-01-20 14:00 CAT', status: 'scheduled', coverage: 0, estimatedDuration: 55, droneId: 'LWSC-DRN-002', priority: 'routine', operator: 'James Mwanza' },
      { id: 'MSN-2026-0120-002', route: 'Woodlands Extension Survey', dma: 'DMA-WDL-02', scheduledTime: '2026-01-20 08:30 CAT', status: 'in_flight', coverage: 72, estimatedDuration: 40, droneId: 'LWSC-DRN-001', priority: 'urgent', operator: 'Peter Banda' },
      { id: 'MSN-2026-0120-003', route: 'Emmasdale Night Thermal Scan', dma: 'DMA-EMM-01', scheduledTime: '2026-01-20 22:00 CAT', status: 'scheduled', coverage: 0, estimatedDuration: 45, droneId: 'LWSC-DRN-005', priority: 'routine', operator: 'Grace Phiri' },
      { id: 'MSN-2026-0119-015', route: 'Chilenje South Inspection', dma: 'DMA-CHI-02', scheduledTime: '2026-01-19 14:00 CAT', status: 'completed', coverage: 100, estimatedDuration: 35, droneId: 'LWSC-DRN-001', priority: 'urgent', operator: 'Peter Banda' },
      { id: 'MSN-2026-0121-001', route: 'Kabwata Emergency Response', dma: 'DMA-KBW-01', scheduledTime: '2026-01-21 06:00 CAT', status: 'scheduled', coverage: 0, estimatedDuration: 30, droneId: 'LWSC-DRN-002', priority: 'emergency', operator: 'James Mwanza' },
      { id: 'MSN-2026-0121-002', route: 'PHI Weekly Assessment', dma: 'DMA-PHI-01', scheduledTime: '2026-01-21 09:00 CAT', status: 'scheduled', coverage: 0, estimatedDuration: 50, droneId: 'LWSC-DRN-005', priority: 'routine', operator: 'Grace Phiri' }
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
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Complete</span>
      case 'processing':
      case 'in_flight':
        return <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium animate-pulse">{status === 'in_flight' ? 'In Flight' : 'Processing'}</span>
      case 'scheduled':
        return <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">Scheduled</span>
      case 'cancelled':
        return <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-medium">Cancelled</span>
      case 'available':
        return <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Available</span>
      case 'charging':
        return <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">Charging</span>
      case 'maintenance':
        return <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-full text-xs font-medium">Maintenance</span>
      default:
        return <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-full text-xs">{status}</span>
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'emergency':
        return <span className="px-2 py-0.5 bg-red-500 text-white rounded-full text-xs font-medium">Emergency</span>
      case 'urgent':
        return <span className="px-2 py-0.5 bg-orange-500 text-white rounded-full text-xs font-medium">Urgent</span>
      default:
        return <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded-full text-xs font-medium">Routine</span>
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-slate-500'
    }
  }

  const filteredAnalyses = filterType 
    ? analyses.filter(a => a.type === filterType)
    : analyses

  const totalLeaks = analyses.reduce((sum, a) => sum + a.leaksDetected, 0)
  const totalWetSpots = analyses.reduce((sum, a) => sum + a.wetSpots, 0)
  const totalEstimatedLoss = analyses.reduce((sum, a) => sum + a.findings.reduce((s, f) => s + f.estimatedLoss, 0), 0)
  const avgConfidence = Math.round(analyses.filter(a => a.confidence > 0).reduce((sum, a) => sum + a.confidence, 0) / analyses.filter(a => a.confidence > 0).length)
  const activeDrones = droneAssets.filter(d => d.status === 'in_flight').length
  const availableDrones = droneAssets.filter(d => d.status === 'available').length

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-medium">OPERATIONAL</span>
            <span className="text-xs text-slate-500">{currentTime.toLocaleString('en-GB', { timeZone: 'Africa/Lusaka' })} CAT</span>
          </div>
          <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Satellite className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
            Satellite & Drone Analysis
          </h1>
          <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">
            LWSC Remote Sensing Operations • Lusaka Province
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary">
            <Upload className="w-4 h-4" />
            <span className="hidden sm:inline">Import</span>
          </Button>
          <Button variant="primary">
            <Plane className="w-4 h-4" />
            <span className="hidden sm:inline">Schedule Mission</span>
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3">
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{totalLeaks}</p>
              <p className="text-[10px] sm:text-xs text-slate-500">Leaks Found</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Droplets className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{totalWetSpots}</p>
              <p className="text-[10px] sm:text-xs text-slate-500">Wet Spots</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Droplets className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{(totalEstimatedLoss/1000).toFixed(1)}k</p>
              <p className="text-[10px] sm:text-xs text-slate-500">m³/day Loss</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <Target className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{avgConfidence}%</p>
              <p className="text-[10px] sm:text-xs text-slate-500">AI Accuracy</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Plane className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{activeDrones}</p>
              <p className="text-[10px] sm:text-xs text-slate-500">Flying Now</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Satellite className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-bold text-slate-900">{analyses.length}</p>
              <p className="text-[10px] sm:text-xs text-slate-500">Analyses</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'analysis', label: 'Image Analysis' },
          { id: 'fleet', label: `Drone Fleet (${droneAssets.length})` },
          { id: 'missions', label: 'Missions' },
          { id: 'live', label: 'Live Feed' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'analysis' && (
        <>
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Select
              value={filterType}
              options={[
                { value: '', label: 'All Sources' },
                { value: 'satellite', label: '🛰️ Satellite Imagery' },
                { value: 'drone', label: '🚁 Drone Surveys' },
                { value: 'thermal', label: '🌡️ Thermal Scans' }
              ]}
              onChange={setFilterType}
            />
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5 sm:p-1">
              <button
                onClick={() => setViewMode('satellite')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-md text-[10px] sm:text-xs font-medium transition-colors ${viewMode === 'satellite' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                RGB
              </button>
              <button
                onClick={() => setViewMode('thermal')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-md text-[10px] sm:text-xs font-medium transition-colors ${viewMode === 'thermal' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                Thermal
              </button>
              <button
                onClick={() => setViewMode('ndvi')}
                className={`px-2 sm:px-3 py-1 sm:py-1.5 rounded-md text-[10px] sm:text-xs font-medium transition-colors ${viewMode === 'ndvi' ? 'bg-white shadow text-slate-900' : 'text-slate-600'}`}
              >
                NDVI
              </button>
            </div>
          </div>

          {/* Analyses Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            {filteredAnalyses.map((analysis) => (
              <div 
                key={analysis.id}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-green-300 transition-all cursor-pointer"
                onClick={() => setSelectedAnalysis(analysis)}
              >
                {/* Image Preview */}
                <div className={`aspect-video relative ${
                  viewMode === 'thermal' ? 'bg-gradient-to-br from-blue-900 via-purple-800 to-red-600' :
                  viewMode === 'ndvi' ? 'bg-gradient-to-br from-red-600 via-yellow-500 to-green-600' :
                  'bg-gradient-to-br from-slate-300 via-green-200 to-slate-400'
                }`}>
                  {/* Simulated satellite/drone image pattern */}
                  <div className="absolute inset-0 opacity-30">
                    <div className="w-full h-full" style={{
                      backgroundImage: 'linear-gradient(90deg, transparent 49%, rgba(255,255,255,0.1) 50%, transparent 51%), linear-gradient(transparent 49%, rgba(255,255,255,0.1) 50%, transparent 51%)',
                      backgroundSize: '20px 20px'
                    }} />
                  </div>
                  
                  {/* Analysis overlay markers */}
                  {analysis.findings.slice(0, 4).map((finding, idx) => (
                    <div
                      key={idx}
                      className="absolute"
                      style={{ left: `${finding.location.x}%`, top: `${finding.location.y}%`, transform: 'translate(-50%, -50%)' }}
                    >
                      <div className={`w-3 h-3 sm:w-4 sm:h-4 rounded-full ${getSeverityColor(finding.severity)} ring-2 ring-white shadow-lg`} />
                      <div className={`absolute w-6 h-6 sm:w-8 sm:h-8 rounded-full ${getSeverityColor(finding.severity)} opacity-30 animate-ping`} style={{ top: '-4px', left: '-4px' }} />
                    </div>
                  ))}
                  
                  {/* Type & Source badge */}
                  <div className="absolute top-2 left-2 flex flex-col gap-1">
                    <span className="px-1.5 sm:px-2 py-0.5 sm:py-1 bg-black/70 text-white rounded-lg text-[10px] sm:text-xs flex items-center gap-1">
                      {getTypeIcon(analysis.type)}
                      <span className="hidden sm:inline">{analysis.type}</span>
                    </span>
                  </div>
                  
                  {/* Status badge */}
                  <div className="absolute top-2 right-2">
                    {getStatusBadge(analysis.analysisStatus)}
                  </div>

                  {/* Resolution badge */}
                  <div className="absolute bottom-2 left-2">
                    <span className="px-1.5 sm:px-2 py-0.5 bg-black/70 text-white rounded text-[8px] sm:text-[10px]">
                      {analysis.resolution}
                    </span>
                  </div>

                  {/* Processing overlay */}
                  {analysis.analysisStatus === 'processing' && (
                    <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                      <div className="text-center text-white">
                        <RefreshCw className="w-6 h-6 sm:w-8 sm:h-8 animate-spin mx-auto mb-2" />
                        <p className="text-[10px] sm:text-sm">AI Processing...</p>
                        <p className="text-[8px] sm:text-xs text-slate-300">Detecting anomalies</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Details */}
                <div className="p-3 sm:p-4">
                  <div className="flex items-center justify-between mb-1 sm:mb-2">
                    <span className="font-mono text-[10px] sm:text-xs text-slate-400">{analysis.id}</span>
                    <span className="text-[10px] sm:text-xs text-slate-500">{analysis.areaSize} km²</span>
                  </div>
                  <h3 className="font-semibold text-slate-900 text-xs sm:text-sm line-clamp-1">{analysis.location}</h3>
                  <p className="text-[10px] sm:text-xs text-slate-500 flex items-center gap-1 mt-0.5 sm:mt-1">
                    <MapPin className="w-3 h-3" /> {analysis.dma} • {analysis.capturedAt.split(' ')[0]}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{analysis.source}</p>

                  {analysis.analysisStatus === 'complete' && (
                    <div className="mt-2 sm:mt-3 grid grid-cols-2 sm:grid-cols-4 gap-1 sm:gap-2">
                      <div className="text-center p-1.5 sm:p-2 bg-red-50 rounded-lg">
                        <p className="text-sm sm:text-lg font-bold text-red-600">{analysis.leaksDetected}</p>
                        <p className="text-[8px] sm:text-[10px] text-red-500">Leaks</p>
                      </div>
                      <div className="text-center p-1.5 sm:p-2 bg-blue-50 rounded-lg">
                        <p className="text-sm sm:text-lg font-bold text-blue-600">{analysis.wetSpots}</p>
                        <p className="text-[8px] sm:text-[10px] text-blue-500">Wet</p>
                      </div>
                      <div className="text-center p-1.5 sm:p-2 bg-green-50 rounded-lg">
                        <p className="text-sm sm:text-lg font-bold text-green-600">{analysis.vegetationAnomalies}</p>
                        <p className="text-[8px] sm:text-[10px] text-green-500">Veg</p>
                      </div>
                      <div className="text-center p-1.5 sm:p-2 bg-orange-50 rounded-lg">
                        <p className="text-sm sm:text-lg font-bold text-orange-600">{analysis.thermalAnomalies}</p>
                        <p className="text-[8px] sm:text-[10px] text-orange-500">Heat</p>
                      </div>
                    </div>
                  )}

                  <div className="mt-2 sm:mt-3 flex items-center justify-between pt-2 border-t border-slate-100">
                    <span className="text-[10px] sm:text-xs text-slate-500">AI Confidence</span>
                    <div className="flex items-center gap-2">
                      <div className="w-16 sm:w-20 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${analysis.confidence >= 90 ? 'bg-green-500' : analysis.confidence >= 75 ? 'bg-amber-500' : 'bg-red-500'}`}
                          style={{ width: `${analysis.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs sm:text-sm font-semibold text-slate-900">{analysis.confidence}%</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'fleet' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
          {droneAssets.map((drone) => (
            <div key={drone.id} className={`bg-white rounded-xl border-2 ${
              drone.status === 'in_flight' ? 'border-green-300 bg-green-50/30' : 'border-slate-200'
            } p-4`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                    drone.status === 'in_flight' ? 'bg-green-100' :
                    drone.status === 'available' ? 'bg-blue-100' :
                    drone.status === 'charging' ? 'bg-yellow-100' : 'bg-slate-100'
                  }`}>
                    <Plane className={`w-6 h-6 ${
                      drone.status === 'in_flight' ? 'text-green-600 animate-pulse' :
                      drone.status === 'available' ? 'text-blue-600' :
                      drone.status === 'charging' ? 'text-yellow-600' : 'text-slate-500'
                    }`} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{drone.name}</h3>
                    <p className="text-xs text-slate-500">{drone.model}</p>
                  </div>
                </div>
                {getStatusBadge(drone.status)}
              </div>

              {drone.currentMission && (
                <div className="mb-3 p-2 bg-green-100 rounded-lg">
                  <p className="text-[10px] text-green-600 font-medium">Current Mission</p>
                  <p className="text-xs text-green-800">{drone.currentMission}</p>
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <Battery className="w-3 h-3" /> Battery
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          drone.battery >= 80 ? 'bg-green-500' : 
                          drone.battery >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${drone.battery}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold">{drone.battery}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Total Flights</span>
                  <span className="font-medium">{drone.totalFlights}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Last Flight</span>
                  <span className="font-medium">{drone.lastFlight}</span>
                </div>
              </div>

              {drone.status === 'available' && (
                <button className="w-full mt-3 py-2 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-1">
                  <Play className="w-3 h-3" /> Launch Mission
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'missions' && (
        <SectionCard title="Mission Schedule" subtitle="Planned and active drone missions across Lusaka">
          <div className="space-y-3">
            {droneSchedules.map((mission) => (
              <div key={mission.id} className={`rounded-xl p-4 ${
                mission.status === 'in_flight' ? 'bg-green-50 border-2 border-green-200' :
                mission.priority === 'emergency' ? 'bg-red-50 border border-red-200' :
                mission.status === 'completed' ? 'bg-slate-50' : 'bg-white border border-slate-200'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-lg flex items-center justify-center ${
                      mission.status === 'in_flight' ? 'bg-green-100' : 
                      mission.status === 'completed' ? 'bg-slate-200' : 
                      mission.priority === 'emergency' ? 'bg-red-100' : 'bg-blue-100'
                    }`}>
                      <Plane className={`w-5 h-5 sm:w-6 sm:h-6 ${
                        mission.status === 'in_flight' ? 'text-green-600 animate-pulse' : 
                        mission.status === 'completed' ? 'text-slate-500' : 
                        mission.priority === 'emergency' ? 'text-red-600' : 'text-blue-600'
                      }`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-semibold text-slate-900 text-sm">{mission.route}</p>
                        {getPriorityBadge(mission.priority)}
                      </div>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span className="text-xs text-slate-500">{mission.dma}</span>
                        {getStatusBadge(mission.status)}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">Operator: {mission.operator}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs sm:text-sm font-semibold text-slate-900">{mission.scheduledTime}</p>
                      <p className="text-[10px] sm:text-xs text-slate-500">{mission.estimatedDuration} min flight</p>
                    </div>
                    {mission.status === 'in_flight' && (
                      <div className="w-20 sm:w-24">
                        <div className="flex items-center justify-between text-[10px] sm:text-xs mb-1">
                          <span className="text-slate-500">Progress</span>
                          <span className="font-semibold text-green-600">{mission.coverage}%</span>
                        </div>
                        <div className="h-2 bg-green-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full transition-all"
                            style={{ width: `${mission.coverage}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {mission.status === 'scheduled' && (
                      <Button variant="primary" size="sm">
                        <Play className="w-4 h-4" />
                      </Button>
                    )}
                    {mission.status === 'completed' && (
                      <Button variant="secondary" size="sm">
                        <FileText className="w-4 h-4" />
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
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-white font-semibold text-sm sm:text-base">Live Drone Feed - Alpha-1</span>
              <span className="text-slate-400 text-xs">Woodlands Extension</span>
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
          
          <div className="aspect-video bg-gradient-to-br from-green-900/50 to-slate-900/50 rounded-lg relative overflow-hidden">
            {/* Simulated live feed with grid pattern */}
            <div className="absolute inset-0" style={{
              backgroundImage: 'linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px)',
              backgroundSize: '50px 50px'
            }} />
            
            {/* Flight path overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Navigation className="w-12 h-12 sm:w-16 sm:h-16 text-green-400 mx-auto mb-3 animate-pulse" />
                <p className="text-white font-medium text-sm sm:text-base">Drone Alpha-1 Live Feed</p>
                <p className="text-green-400 text-xs sm:text-sm">Woodlands Extension Survey</p>
                <p className="text-slate-400 text-[10px] sm:text-xs mt-2">-15.4012°S, 28.3389°E • Alt: 120m AGL</p>
              </div>
            </div>

            {/* Crosshair */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-green-500/30" />
              <div className="absolute top-1/2 left-0 right-0 h-px bg-green-500/30" />
            </div>

            {/* HUD overlay */}
            <div className="absolute top-3 left-3 text-green-400 text-[10px] sm:text-xs font-mono space-y-1">
              <p>SPD: 8.2 m/s</p>
              <p>ALT: 120m AGL</p>
              <p>HDG: 045°</p>
            </div>
            <div className="absolute top-3 right-3 text-green-400 text-[10px] sm:text-xs font-mono text-right space-y-1">
              <p>REC ●</p>
              <p>4K 30fps</p>
              <p>{currentTime.toLocaleTimeString()}</p>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold text-sm sm:text-base">72%</p>
              <p className="text-slate-400 text-[10px] sm:text-xs">Coverage</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold text-sm sm:text-base">18:42</p>
              <p className="text-slate-400 text-[10px] sm:text-xs">Flight Time</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-green-400 font-semibold text-sm sm:text-base">68%</p>
              <p className="text-slate-400 text-[10px] sm:text-xs">Battery</p>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <p className="text-white font-semibold text-sm sm:text-base">12.4 km</p>
              <p className="text-slate-400 text-[10px] sm:text-xs">Distance</p>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Detail Modal */}
      {selectedAnalysis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-xl sm:rounded-2xl shadow-2xl w-full max-w-4xl max-h-[95vh] overflow-y-auto">
            <div className="p-4 sm:p-6 border-b border-slate-200 sticky top-0 bg-white z-10">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {getTypeIcon(selectedAnalysis.type)}
                    <span className="font-mono text-[10px] sm:text-xs text-slate-400">{selectedAnalysis.id}</span>
                    {getStatusBadge(selectedAnalysis.analysisStatus)}
                  </div>
                  <h2 className="text-base sm:text-xl font-bold text-slate-900 mt-1">{selectedAnalysis.location}</h2>
                  <p className="text-xs sm:text-sm text-slate-500">{selectedAnalysis.dma} • {selectedAnalysis.capturedAt}</p>
                  <p className="text-[10px] sm:text-xs text-slate-400 mt-0.5">Source: {selectedAnalysis.source} • {selectedAnalysis.areaSize} km² • {selectedAnalysis.resolution}</p>
                </div>
                <button 
                  onClick={() => setSelectedAnalysis(null)}
                  className="p-2 hover:bg-slate-100 rounded-lg text-slate-500"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-4 sm:p-6">
              {/* Image with markers */}
              <div className={`aspect-video rounded-xl relative mb-4 sm:mb-6 overflow-hidden ${
                viewMode === 'thermal' ? 'bg-gradient-to-br from-blue-900 via-purple-800 to-red-600' :
                viewMode === 'ndvi' ? 'bg-gradient-to-br from-red-600 via-yellow-500 to-green-600' :
                'bg-gradient-to-br from-slate-300 via-green-200 to-slate-400'
              }`}>
                <div className="absolute inset-0 opacity-30">
                  <div className="w-full h-full" style={{
                    backgroundImage: 'linear-gradient(90deg, transparent 49%, rgba(255,255,255,0.1) 50%, transparent 51%), linear-gradient(transparent 49%, rgba(255,255,255,0.1) 50%, transparent 51%)',
                    backgroundSize: '30px 30px'
                  }} />
                </div>
                {selectedAnalysis.findings.map((finding, idx) => (
                  <div
                    key={idx}
                    className="absolute group cursor-pointer"
                    style={{ left: `${finding.location.x}%`, top: `${finding.location.y}%`, transform: 'translate(-50%, -50%)' }}
                  >
                    <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full ${getSeverityColor(finding.severity)} flex items-center justify-center text-white text-xs sm:text-sm font-bold ring-2 ring-white shadow-lg`}>
                      {idx + 1}
                    </div>
                    <div className="absolute left-10 top-0 bg-black/90 text-white px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg text-[10px] sm:text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-20 max-w-[200px]">
                      <p className="font-medium">{finding.description}</p>
                      <p className="text-slate-300 mt-0.5">{finding.address}</p>
                      <p className="text-amber-300 mt-0.5">~{finding.estimatedLoss} m³/day loss</p>
                    </div>
                  </div>
                ))}
                
                {/* Coordinates overlay */}
                <div className="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-[10px] sm:text-xs font-mono">
                  {selectedAnalysis.coordinates.lat.toFixed(4)}°S, {selectedAnalysis.coordinates.lng.toFixed(4)}°E
                </div>
              </div>

              {/* Findings */}
              <h3 className="font-semibold text-slate-900 mb-3 text-sm sm:text-base">AI Findings ({selectedAnalysis.findings.length})</h3>
              <div className="space-y-2 mb-4 sm:mb-6">
                {selectedAnalysis.findings.map((finding, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full ${getSeverityColor(finding.severity)} flex items-center justify-center text-white text-xs sm:text-sm font-bold flex-shrink-0`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 text-xs sm:text-sm">{finding.description}</p>
                      <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">
                        📍 {finding.address}
                      </p>
                      <p className="text-[10px] sm:text-xs text-slate-500">
                        {finding.type.replace('_', ' ')} • {finding.confidence}% confidence • ~{finding.estimatedLoss} m³/day
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-[10px] sm:text-xs font-medium flex-shrink-0 ${
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

              {/* Summary */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 sm:p-4 mb-4 sm:mb-6">
                <p className="text-amber-800 font-medium text-xs sm:text-sm">
                  💧 Total Estimated Water Loss: {selectedAnalysis.findings.reduce((s, f) => s + f.estimatedLoss, 0).toLocaleString()} m³/day
                </p>
                <p className="text-amber-700 text-[10px] sm:text-xs mt-1">
                  Revenue Impact: K{(selectedAnalysis.findings.reduce((s, f) => s + f.estimatedLoss, 0) * 8.5).toLocaleString()}/day (at K8.50/m³)
                </p>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary">
                  Create Work Orders
                </Button>
                <Button variant="secondary">
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Report</span>
                </Button>
                <Button variant="secondary">
                  <Share2 className="w-4 h-4" />
                  <span className="hidden sm:inline">Share</span>
                </Button>
                <Button variant="secondary">
                  <MapPin className="w-4 h-4" />
                  <span className="hidden sm:inline">View on Map</span>
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
