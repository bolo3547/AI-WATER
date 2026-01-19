'use client'

import { useState, useEffect } from 'react'
import { 
  Brain, AlertTriangle, TrendingUp, Calendar, Filter,
  MapPin, Clock, Wrench, ChevronRight, RefreshCw,
  Activity, Gauge, ThermometerSun, Droplets, Zap,
  Target, BarChart3, PieChart, AlertCircle, CheckCircle,
  ArrowUp, ArrowDown, Minus, Info, Download, Bell
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface PipePrediction {
  id: string
  pipeId: string
  location: string
  dma: string
  failureProbability: number
  predictedDate: string
  riskFactors: string[]
  pipeAge: number
  pipeMaterial: string
  lastInspection: string
  estimatedLoss: number
  repairCost: number
  priority: 'critical' | 'high' | 'medium' | 'low'
  trend: 'increasing' | 'stable' | 'decreasing'
  coordinates: { lat: number; lng: number }
}

interface RiskFactor {
  name: string
  impact: number
  description: string
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<PipePrediction[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [selectedPipe, setSelectedPipe] = useState<PipePrediction | null>(null)
  const [filterPriority, setFilterPriority] = useState('')
  const [filterDMA, setFilterDMA] = useState('')
  const [timeRange, setTimeRange] = useState('30')
  const [lastAnalysis, setLastAnalysis] = useState(new Date())

  // AI Risk Factors
  const riskFactors: RiskFactor[] = [
    { name: 'Pipe Age', impact: 35, description: 'Older pipes have higher failure rates' },
    { name: 'Material Degradation', impact: 25, description: 'Corrosion and wear patterns' },
    { name: 'Pressure Stress', impact: 20, description: 'High pressure zones increase risk' },
    { name: 'Soil Conditions', impact: 10, description: 'Corrosive or shifting soils' },
    { name: 'Historical Failures', impact: 10, description: 'Previous repairs in area' }
  ]

  // Load predictions
  useEffect(() => {
    loadPredictions()
  }, [])

  const loadPredictions = () => {
    setIsAnalyzing(true)
    
    setTimeout(() => {
      setPredictions([
        {
          id: 'PRED-001',
          pipeId: 'PIPE-KAB-2847',
          location: 'Kabulonga Rd, Near Junction',
          dma: 'Kabulonga',
          failureProbability: 94,
          predictedDate: '2026-02-15',
          riskFactors: ['Age >40 years', 'Cast Iron Corrosion', 'High Pressure Zone', 'Previous Repairs'],
          pipeAge: 45,
          pipeMaterial: 'Cast Iron',
          lastInspection: '2024-06-15',
          estimatedLoss: 450,
          repairCost: 15000,
          priority: 'critical',
          trend: 'increasing',
          coordinates: { lat: -15.4192, lng: 28.3225 }
        },
        {
          id: 'PRED-002',
          pipeId: 'PIPE-ROM-1563',
          location: 'Roma Township Main',
          dma: 'Roma',
          failureProbability: 87,
          predictedDate: '2026-02-28',
          riskFactors: ['Pressure Transients', 'Joint Weakness', 'Traffic Vibration'],
          pipeAge: 32,
          pipeMaterial: 'Asbestos Cement',
          lastInspection: '2024-08-20',
          estimatedLoss: 280,
          repairCost: 12000,
          priority: 'critical',
          trend: 'increasing',
          coordinates: { lat: -15.3958, lng: 28.3108 }
        },
        {
          id: 'PRED-003',
          pipeId: 'PIPE-CHE-0892',
          location: 'Chelstone Shopping Area',
          dma: 'Chelstone',
          failureProbability: 72,
          predictedDate: '2026-03-20',
          riskFactors: ['Age >30 years', 'Soil Movement', 'Water Hammer Events'],
          pipeAge: 35,
          pipeMaterial: 'PVC',
          lastInspection: '2025-01-10',
          estimatedLoss: 180,
          repairCost: 8000,
          priority: 'high',
          trend: 'stable',
          coordinates: { lat: -15.3605, lng: 28.3517 }
        },
        {
          id: 'PRED-004',
          pipeId: 'PIPE-MAT-2341',
          location: 'Matero Industrial Zone',
          dma: 'Matero',
          failureProbability: 65,
          predictedDate: '2026-04-05',
          riskFactors: ['Chemical Exposure', 'High Demand', 'Temperature Stress'],
          pipeAge: 28,
          pipeMaterial: 'Ductile Iron',
          lastInspection: '2025-02-18',
          estimatedLoss: 320,
          repairCost: 18000,
          priority: 'high',
          trend: 'stable',
          coordinates: { lat: -15.3747, lng: 28.2633 }
        },
        {
          id: 'PRED-005',
          pipeId: 'PIPE-WOD-4521',
          location: 'Woodlands Residential',
          dma: 'Woodlands',
          failureProbability: 48,
          predictedDate: '2026-05-10',
          riskFactors: ['Minor Corrosion', 'Age >20 years'],
          pipeAge: 22,
          pipeMaterial: 'HDPE',
          lastInspection: '2025-06-05',
          estimatedLoss: 60,
          repairCost: 4000,
          priority: 'medium',
          trend: 'stable',
          coordinates: { lat: -15.4134, lng: 28.3064 }
        },
        {
          id: 'PRED-006',
          pipeId: 'PIPE-CHI-7823',
          location: 'Chilenje South Block 5',
          dma: 'Chilenje',
          failureProbability: 35,
          predictedDate: '2026-06-20',
          riskFactors: ['Normal Wear', 'Minor Stress Points'],
          pipeAge: 15,
          pipeMaterial: 'HDPE',
          lastInspection: '2025-09-12',
          estimatedLoss: 40,
          repairCost: 3000,
          priority: 'low',
          trend: 'decreasing',
          coordinates: { lat: -15.4433, lng: 28.2925 }
        },
        {
          id: 'PRED-007',
          pipeId: 'PIPE-KAL-9012',
          location: 'Kalingalinga Main Road',
          dma: 'Kalingalinga',
          failureProbability: 78,
          predictedDate: '2026-03-01',
          riskFactors: ['Illegal Connections', 'Shallow Depth', 'Heavy Traffic'],
          pipeAge: 38,
          pipeMaterial: 'Cast Iron',
          lastInspection: '2024-11-30',
          estimatedLoss: 220,
          repairCost: 9500,
          priority: 'high',
          trend: 'increasing',
          coordinates: { lat: -15.4028, lng: 28.3350 }
        },
        {
          id: 'PRED-008',
          pipeId: 'PIPE-OLY-3456',
          location: 'Olympia Park Estate',
          dma: 'Olympia',
          failureProbability: 25,
          predictedDate: '2026-08-15',
          riskFactors: ['Normal Aging'],
          pipeAge: 12,
          pipeMaterial: 'HDPE',
          lastInspection: '2025-12-01',
          estimatedLoss: 25,
          repairCost: 2500,
          priority: 'low',
          trend: 'stable',
          coordinates: { lat: -15.4089, lng: 28.2953 }
        }
      ])
      setIsAnalyzing(false)
      setLastAnalysis(new Date())
    }, 2000)
  }

  const filteredPredictions = predictions.filter(p => {
    if (filterPriority && p.priority !== filterPriority) return false
    if (filterDMA && p.dma !== filterDMA) return false
    return true
  }).sort((a, b) => b.failureProbability - a.failureProbability)

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return <ArrowUp className="w-4 h-4 text-red-500" />
      case 'decreasing': return <ArrowDown className="w-4 h-4 text-green-500" />
      default: return <Minus className="w-4 h-4 text-gray-500" />
    }
  }

  const stats = {
    critical: predictions.filter(p => p.priority === 'critical').length,
    high: predictions.filter(p => p.priority === 'high').length,
    totalRisk: predictions.reduce((sum, p) => sum + p.estimatedLoss, 0),
    avgProbability: Math.round(predictions.reduce((sum, p) => sum + p.failureProbability, 0) / predictions.length)
  }

  const uniqueDMAs = [...new Set(predictions.map(p => p.dma))]

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Brain className="w-6 h-6 sm:w-7 sm:h-7 text-purple-600" />
            Predictive Pipe Failure AI
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Machine learning predictions for infrastructure failures
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-xs text-slate-500">
            Last analysis: {lastAnalysis.toLocaleTimeString()}
          </span>
          <Button variant="secondary" onClick={loadPredictions} disabled={isAnalyzing}>
            <RefreshCw className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isAnalyzing ? 'Analyzing...' : 'Re-analyze'}</span>
          </Button>
        </div>
      </div>

      {/* AI Model Status */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-4 sm:p-6 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center">
              <Brain className="w-8 h-8" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Pipe Failure Prediction Model</h3>
              <p className="text-purple-200 text-sm">Deep learning on 10 years of failure data</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 sm:gap-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-300">{stats.critical}</p>
              <p className="text-xs text-purple-200">Critical</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-300">{stats.high}</p>
              <p className="text-xs text-purple-200">High Risk</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{stats.avgProbability}%</p>
              <p className="text-xs text-purple-200">Avg Probability</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-300">{stats.totalRisk}</p>
              <p className="text-xs text-purple-200">m³/day at Risk</p>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Factor Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6">
        <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <PieChart className="w-5 h-5 text-blue-600" />
          AI Risk Factor Weights
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {riskFactors.map((factor, idx) => (
            <div key={idx} className="bg-slate-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-slate-600">{factor.name}</span>
                <span className="text-sm font-bold text-blue-600">{factor.impact}%</span>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                  style={{ width: `${factor.impact}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={filterPriority}
          options={[
            { value: '', label: 'All Priorities' },
            { value: 'critical', label: '🔴 Critical' },
            { value: 'high', label: '🟠 High' },
            { value: 'medium', label: '🟡 Medium' },
            { value: 'low', label: '🟢 Low' }
          ]}
          onChange={setFilterPriority}
        />
        <Select
          value={filterDMA}
          options={[
            { value: '', label: 'All DMAs' },
            ...uniqueDMAs.map(d => ({ value: d, label: d }))
          ]}
          onChange={setFilterDMA}
        />
        <Select
          value={timeRange}
          options={[
            { value: '30', label: 'Next 30 Days' },
            { value: '60', label: 'Next 60 Days' },
            { value: '90', label: 'Next 90 Days' },
            { value: '180', label: 'Next 6 Months' }
          ]}
          onChange={setTimeRange}
        />
      </div>

      {/* Predictions List */}
      <SectionCard 
        title="Failure Predictions" 
        subtitle={`${filteredPredictions.length} pipes at risk in selected period`}
        noPadding
      >
        {isAnalyzing ? (
          <div className="p-8 text-center">
            <Brain className="w-12 h-12 text-purple-500 animate-pulse mx-auto mb-4" />
            <p className="text-slate-600">AI analyzing pipe network...</p>
            <p className="text-sm text-slate-400 mt-1">Processing 15,000+ data points</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredPredictions.map((pred) => (
              <div 
                key={pred.id} 
                className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                onClick={() => setSelectedPipe(pred)}
              >
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  {/* Probability Circle */}
                  <div className="flex items-center gap-3">
                    <div className="relative w-14 h-14 flex-shrink-0">
                      <svg className="w-14 h-14 -rotate-90">
                        <circle
                          cx="28" cy="28" r="24"
                          stroke="#e2e8f0" strokeWidth="4" fill="none"
                        />
                        <circle
                          cx="28" cy="28" r="24"
                          stroke={pred.failureProbability >= 80 ? '#ef4444' : pred.failureProbability >= 60 ? '#f97316' : pred.failureProbability >= 40 ? '#eab308' : '#22c55e'}
                          strokeWidth="4"
                          fill="none"
                          strokeDasharray={`${pred.failureProbability * 1.51} 151`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold">
                        {pred.failureProbability}%
                      </span>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-slate-400">{pred.pipeId}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(pred.priority)}`}>
                        {pred.priority.toUpperCase()}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        {getTrendIcon(pred.trend)}
                        {pred.trend}
                      </span>
                    </div>
                    <p className="font-medium text-slate-900 mt-1">{pred.location}</p>
                    <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> {pred.dma}
                      </span>
                      <span>•</span>
                      <span>{pred.pipeMaterial}</span>
                      <span>•</span>
                      <span>{pred.pipeAge} years old</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {pred.riskFactors.slice(0, 3).map((factor, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
                          {factor}
                        </span>
                      ))}
                      {pred.riskFactors.length > 3 && (
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
                          +{pred.riskFactors.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex sm:flex-col items-center sm:items-end gap-4 sm:gap-1 text-right">
                    <div>
                      <p className="text-xs text-slate-500">Predicted Failure</p>
                      <p className="font-semibold text-slate-900">{new Date(pred.predictedDate).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Est. Loss</p>
                      <p className="font-semibold text-red-600">{pred.estimatedLoss} m³/day</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Repair Cost</p>
                      <p className="font-semibold text-slate-700">K{pred.repairCost.toLocaleString()}</p>
                    </div>
                  </div>

                  <ChevronRight className="w-5 h-5 text-slate-400 hidden sm:block" />
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Pipe Detail Modal */}
      {selectedPipe && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-purple-200 text-sm font-mono">{selectedPipe.pipeId}</p>
                  <h2 className="text-xl font-bold mt-1">{selectedPipe.location}</h2>
                  <p className="text-purple-200 mt-1">{selectedPipe.dma} DMA</p>
                </div>
                <button 
                  onClick={() => setSelectedPipe(null)}
                  className="p-2 hover:bg-white/20 rounded-lg"
                >
                  <AlertCircle className="w-5 h-5" />
                </button>
              </div>
              
              <div className="mt-4 flex items-center gap-6">
                <div className="text-center">
                  <p className="text-4xl font-bold">{selectedPipe.failureProbability}%</p>
                  <p className="text-purple-200 text-sm">Failure Probability</p>
                </div>
                <div className="flex-1 grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xl font-bold">{selectedPipe.pipeAge}</p>
                    <p className="text-purple-200 text-xs">Years Old</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-red-300">{selectedPipe.estimatedLoss}</p>
                    <p className="text-purple-200 text-xs">m³/day Loss</p>
                  </div>
                  <div>
                    <p className="text-xl font-bold text-yellow-300">K{(selectedPipe.repairCost/1000).toFixed(0)}K</p>
                    <p className="text-purple-200 text-xs">Repair Cost</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Risk Factors */}
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Risk Factors Detected</h3>
                <div className="space-y-2">
                  {selectedPipe.riskFactors.map((factor, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-2 bg-red-50 rounded-lg">
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                      <span className="text-sm text-slate-700">{factor}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pipe Details */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Material</p>
                  <p className="font-semibold">{selectedPipe.pipeMaterial}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Last Inspection</p>
                  <p className="font-semibold">{selectedPipe.lastInspection}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Predicted Failure Date</p>
                  <p className="font-semibold text-red-600">{selectedPipe.predictedDate}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-500">Trend</p>
                  <p className="font-semibold flex items-center gap-1">
                    {getTrendIcon(selectedPipe.trend)} {selectedPipe.trend}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary">
                  <Wrench className="w-4 h-4" />
                  Create Work Order
                </Button>
                <Button variant="secondary">
                  <Bell className="w-4 h-4" />
                  Set Alert
                </Button>
                <Button variant="secondary">
                  <Calendar className="w-4 h-4" />
                  Schedule Inspection
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
