'use client'

import { useState, useEffect } from 'react'
import { 
  Brain, Sparkles, TrendingUp, AlertTriangle, Lightbulb, 
  Zap, DollarSign, Activity, BarChart3, 
  ChevronRight, RefreshCw, Download, X, CheckCircle2,
  Loader2, MapPin, Droplets, Clock, FileText, Route
} from 'lucide-react'
import { AIInsightsPanel } from '@/components/ai/AIInsightsPanel'

interface AIMetric {
  label: string
  value: string
  change: number
  icon: React.ElementType
  color: string
}

interface LeakPrediction {
  id: string
  location: string
  dma: string
  probability: number
  estimatedLoss: number
  riskLevel: 'high' | 'medium' | 'low'
  coordinates: { lat: number; lng: number }
}

interface Anomaly {
  id: string
  type: string
  sensor: string
  location: string
  severity: 'critical' | 'warning' | 'info'
  description: string
  detectedAt: string
}

interface RouteOptimization {
  id: string
  tasks: string[]
  distance: number
  estimatedTime: string
  savings: string
  route: string[]
}

interface NRWReport {
  period: string
  totalNrw: number
  physicalLosses: number
  commercialLosses: number
  recoveredRevenue: number
  recommendations: string[]
}

export default function AIInsightsPage() {
  const [lastAnalysis, setLastAnalysis] = useState(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)
  
  // AI Action States
  const [showLeakPrediction, setShowLeakPrediction] = useState(false)
  const [showAnomalyScan, setShowAnomalyScan] = useState(false)
  const [showRouteOptimize, setShowRouteOptimize] = useState(false)
  const [showNRWReport, setShowNRWReport] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)
  
  // AI Results
  const [leakPredictions, setLeakPredictions] = useState<LeakPrediction[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [optimizedRoute, setOptimizedRoute] = useState<RouteOptimization | null>(null)
  const [nrwReport, setNRWReport] = useState<NRWReport | null>(null)

  const metrics: AIMetric[] = [
    { label: 'AI Predictions', value: '12', change: 3, icon: TrendingUp, color: 'blue' },
    { label: 'Anomalies Detected', value: '8', change: -2, icon: AlertTriangle, color: 'red' },
    { label: 'Recommendations', value: '15', change: 5, icon: Lightbulb, color: 'yellow' },
    { label: 'Potential Savings', value: 'K892K', change: 12, icon: DollarSign, color: 'emerald' },
  ]

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastAnalysis(new Date())
      setIsRefreshing(false)
    }, 2000)
  }

  // Simulate AI Processing
  const simulateProcessing = (duration: number): Promise<void> => {
    return new Promise((resolve) => {
      setIsProcessing(true)
      setProcessingProgress(0)
      const interval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval)
            setIsProcessing(false)
            resolve()
            return 100
          }
          return prev + Math.random() * 15
        })
      }, duration / 10)
    })
  }

  // Run Leak Prediction
  const runLeakPrediction = async () => {
    setShowLeakPrediction(true)
    setLeakPredictions([])
    await simulateProcessing(3000)
    
    setLeakPredictions([
      { id: 'LP-001', location: 'Junction Rd & Main St', dma: 'Kabulonga', probability: 94, estimatedLoss: 450, riskLevel: 'high', coordinates: { lat: -15.4167, lng: 28.2833 } },
      { id: 'LP-002', location: 'Industrial Zone Block C', dma: 'Roma', probability: 87, estimatedLoss: 280, riskLevel: 'high', coordinates: { lat: -15.3833, lng: 28.3167 } },
      { id: 'LP-003', location: 'Residential Area 4B', dma: 'Chelstone', probability: 72, estimatedLoss: 120, riskLevel: 'medium', coordinates: { lat: -15.4000, lng: 28.3500 } },
      { id: 'LP-004', location: 'Market Square Pipeline', dma: 'Matero', probability: 65, estimatedLoss: 95, riskLevel: 'medium', coordinates: { lat: -15.3700, lng: 28.2600 } },
      { id: 'LP-005', location: 'School Zone Main', dma: 'Woodlands', probability: 45, estimatedLoss: 60, riskLevel: 'low', coordinates: { lat: -15.4100, lng: 28.2900 } },
    ])
  }

  // Scan for Anomalies
  const scanForAnomalies = async () => {
    setShowAnomalyScan(true)
    setAnomalies([])
    await simulateProcessing(4000)
    
    setAnomalies([
      { id: 'AN-001', type: 'Pressure Drop', sensor: 'ESP32-007', location: 'Kabulonga Zone', severity: 'critical', description: 'Sudden 45% pressure drop detected - possible major leak or burst', detectedAt: new Date(Date.now() - 300000).toISOString() },
      { id: 'AN-002', type: 'Flow Surge', sensor: 'ESP32-012', location: 'Industrial Area', severity: 'warning', description: 'Abnormal flow increase of 230% above baseline', detectedAt: new Date(Date.now() - 900000).toISOString() },
      { id: 'AN-003', type: 'Night Flow Alert', sensor: 'DMA-004', location: 'Chelstone', severity: 'warning', description: 'Minimum night flow 35% above threshold - indicates background leakage', detectedAt: new Date(Date.now() - 3600000).toISOString() },
      { id: 'AN-004', type: 'Sensor Drift', sensor: 'ESP32-003', location: 'Roma Zone', severity: 'info', description: 'Calibration drift detected - readings ±8% from expected', detectedAt: new Date(Date.now() - 7200000).toISOString() },
      { id: 'AN-005', type: 'Pattern Anomaly', sensor: 'DMA-002', location: 'Matero', severity: 'warning', description: 'Consumption pattern deviates from ML model prediction by 28%', detectedAt: new Date(Date.now() - 1800000).toISOString() },
    ])
  }

  // Optimize Routes
  const optimizeRoutes = async () => {
    setShowRouteOptimize(true)
    setOptimizedRoute(null)
    await simulateProcessing(3500)
    
    setOptimizedRoute({
      id: 'ROUTE-001',
      tasks: ['WO-2847 Leak Repair', 'WO-2846 Valve Check', 'WO-2845 Sensor Calibration', 'WO-2844 Meter Install'],
      distance: 18.5,
      estimatedTime: '4h 20m',
      savings: '32% less travel time',
      route: ['Depot', 'Kabulonga (WO-2847)', 'Roma (WO-2846)', 'Chelstone (WO-2845)', 'Woodlands (WO-2844)', 'Depot']
    })
  }

  // Generate NRW Report
  const generateNRWReport = async () => {
    setShowNRWReport(true)
    setNRWReport(null)
    await simulateProcessing(5000)
    
    setNRWReport({
      period: 'January 2026',
      totalNrw: 32.4,
      physicalLosses: 22.1,
      commercialLosses: 10.3,
      recoveredRevenue: 892000,
      recommendations: [
        'Priority repair: Junction Rd leak causing 450 m³/day loss',
        'Install 5 additional pressure sensors in Kabulonga zone',
        'Implement active leakage control in Matero DMA',
        'Upgrade aging infrastructure in Industrial Zone (23% of losses)',
        'Customer meter audit recommended for Chelstone area'
      ]
    })
  }

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string }> = {
      blue: { bg: 'bg-blue-100', text: 'text-blue-600' },
      red: { bg: 'bg-red-100', text: 'text-red-600' },
      yellow: { bg: 'bg-yellow-100', text: 'text-yellow-600' },
      emerald: { bg: 'bg-emerald-100', text: 'text-emerald-600' },
      purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
    }
    return colors[color] || colors.blue
  }

  return (
    <div className="space-y-3 sm:space-y-4 lg:space-y-6 min-h-[calc(100vh-120px)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
              <Brain className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <span className="text-lg sm:text-2xl">AI Intelligence Center</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 sm:mt-1">
            Machine learning powered insights and predictions for LWSC network
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          <div className="text-right mr-2">
            <p className="text-xs text-slate-500">Last Analysis</p>
            <p className="text-sm font-medium text-slate-700">{lastAnalysis.toLocaleTimeString()}</p>
          </div>
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Analyzing...' : 'Refresh'}
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
            <Download className="w-4 h-4" />
            Export Report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        {metrics.map((metric) => {
          const colors = getColorClasses(metric.color)
          return (
            <div key={metric.label} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg ${colors.bg} flex items-center justify-center`}>
                  <metric.icon className={`w-5 h-5 ${colors.text}`} />
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  metric.change > 0 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  {metric.change > 0 ? '+' : ''}{metric.change}%
                </span>
              </div>
              <p className="text-2xl font-bold text-slate-900">{metric.value}</p>
              <p className="text-xs text-slate-500">{metric.label}</p>
            </div>
          )
        })}
      </div>

      <div className="bg-gradient-to-r from-slate-900 via-purple-900 to-slate-900 rounded-2xl p-4 sm:p-6 text-white">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 lg:gap-6">
          <div className="flex items-center gap-3 sm:gap-4">
            <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-xl sm:rounded-2xl bg-white/10 flex items-center justify-center flex-shrink-0">
              <Brain className="w-6 h-6 sm:w-8 sm:h-8 text-purple-300" />
            </div>
            <div>
              <h3 className="text-base sm:text-xl font-bold">LWSC Neural Network Engine</h3>
              <p className="text-purple-200 text-xs sm:text-sm">Deep learning models for water network analysis</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-6 lg:gap-8">
            <div className="text-center bg-white/5 rounded-xl p-3 sm:p-0 sm:bg-transparent">
              <p className="text-xl sm:text-3xl font-bold text-emerald-400">98.2%</p>
              <p className="text-[10px] sm:text-xs text-purple-200">Model Accuracy</p>
            </div>
            <div className="text-center bg-white/5 rounded-xl p-3 sm:p-0 sm:bg-transparent">
              <p className="text-xl sm:text-3xl font-bold text-blue-400">156</p>
              <p className="text-[10px] sm:text-xs text-purple-200">Data Sources</p>
            </div>
            <div className="text-center bg-white/5 rounded-xl p-3 sm:p-0 sm:bg-transparent">
              <p className="text-xl sm:text-3xl font-bold text-yellow-400">2.4M</p>
              <p className="text-[10px] sm:text-xs text-purple-200">Data Points/Day</p>
            </div>
            <div className="text-center bg-white/5 rounded-xl p-3 sm:p-0 sm:bg-transparent">
              <p className="text-xl sm:text-3xl font-bold text-cyan-400">&lt; 50ms</p>
              <p className="text-[10px] sm:text-xs text-purple-200">Response Time</p>
            </div>
          </div>
        </div>

        <div className="mt-4 sm:mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-3">
          {[
            { name: 'Leak Predictor', status: 'active', accuracy: 94 },
            { name: 'Anomaly Detector', status: 'active', accuracy: 92 },
            { name: 'Demand Forecaster', status: 'active', accuracy: 89 },
            { name: 'Pipe Health Model', status: 'active', accuracy: 87 },
            { name: 'NRW Optimizer', status: 'training', accuracy: 85 },
          ].map((model) => (
            <div key={model.name} className="bg-white/10 rounded-xl p-2.5 sm:p-3 hover:bg-white/15 transition-colors">
              <div className="flex items-center justify-between mb-1.5 sm:mb-2">
                <span className={`w-2 h-2 rounded-full ${
                  model.status === 'active' ? 'bg-emerald-400' : 'bg-yellow-400 animate-pulse'
                }`} />
                <span className="text-[10px] sm:text-xs text-purple-200">{model.accuracy}%</span>
              </div>
              <p className="text-xs sm:text-sm font-medium truncate">{model.name}</p>
              <p className="text-[10px] sm:text-xs text-purple-300 capitalize">{model.status}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="lg:col-span-2 order-2 lg:order-1">
          <AIInsightsPanel 
            type="nrw_insights"
            title="AI System Analysis"
            data={{
              predictions: leakPredictions,
              anomalies: anomalies,
              metrics: metrics
            }}
            autoLoad={true}
          />
        </div>

        <div className="space-y-4 order-1 lg:order-2">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" />
              AI Quick Actions
            </h3>
            <div className="space-y-2">
              <button 
                onClick={runLeakPrediction}
                className="w-full flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 group-hover:text-blue-700">Run Leak Prediction</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600" />
              </button>
              <button 
                onClick={scanForAnomalies}
                className="w-full flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-red-50 hover:border-red-200 border border-transparent transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center group-hover:bg-red-200 transition-colors">
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 group-hover:text-red-700">Scan for Anomalies</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-red-600" />
              </button>
              <button 
                onClick={optimizeRoutes}
                className="w-full flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-purple-50 hover:border-purple-200 border border-transparent transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                    <Activity className="w-4 h-4 text-purple-600" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 group-hover:text-purple-700">Optimize Routes</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-600" />
              </button>
              <button 
                onClick={generateNRWReport}
                className="w-full flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-emerald-50 hover:border-emerald-200 border border-transparent transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center group-hover:bg-emerald-200 transition-colors">
                    <BarChart3 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <span className="text-sm font-medium text-slate-700 group-hover:text-emerald-700">Generate NRW Report</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600" />
              </button>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-500" />
              Continuous Learning
            </h3>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-600">Training Progress</span>
                  <span className="font-medium text-slate-900">87%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full w-[87%] bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full" />
                </div>
              </div>
              <div className="text-xs text-slate-500">
                <p>• Processing 24h of new sensor data</p>
                <p>• Incorporating 5 new leak events</p>
                <p>• Updating pipe degradation model</p>
              </div>
              <div className="pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Next model update</span>
                  <span className="text-xs font-medium text-blue-600">2h 34m</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              Data Quality Score
            </h3>
            <div className="flex items-center justify-center mb-3">
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle cx="48" cy="48" r="40" stroke="#e2e8f0" strokeWidth="8" fill="none" />
                  <circle cx="48" cy="48" r="40" stroke="url(#gradient)" strokeWidth="8" fill="none" 
                    strokeDasharray="251.2" strokeDashoffset="25.12" strokeLinecap="round" />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#8b5cf6" />
                      <stop offset="100%" stopColor="#3b82f6" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-slate-900">90%</span>
                </div>
              </div>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Sensor Coverage</span>
                <span className="font-medium text-emerald-600">95%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Data Freshness</span>
                <span className="font-medium text-emerald-600">98%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Completeness</span>
                <span className="font-medium text-yellow-600">87%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Accuracy</span>
                <span className="font-medium text-emerald-600">92%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Leak Prediction Modal */}
      {showLeakPrediction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">AI Leak Prediction</h2>
                    <p className="text-blue-100 text-sm">Neural network analysis of network data</p>
                  </div>
                </div>
                <button onClick={() => setShowLeakPrediction(false)} className="p-2 hover:bg-white/20 rounded-lg">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {isProcessing ? (
                <div className="text-center py-12">
                  <Brain className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-pulse" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Running AI Analysis...</h3>
                  <p className="text-slate-500 mb-4">Analyzing pressure patterns, flow data, and historical trends</p>
                  <div className="w-64 h-3 bg-slate-100 rounded-full mx-auto overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(processingProgress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-blue-600 mt-2">{Math.round(Math.min(processingProgress, 100))}% Complete</p>
                </div>
              ) : leakPredictions.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      <span className="font-semibold text-slate-900">Found {leakPredictions.length} Potential Leaks</span>
                    </div>
                    <button className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1">
                      <Download className="w-4 h-4" />
                      Export
                    </button>
                  </div>
                  
                  {leakPredictions.map((leak) => (
                    <div key={leak.id} className={`p-4 rounded-xl border-2 ${
                      leak.riskLevel === 'high' ? 'bg-red-50 border-red-200' :
                      leak.riskLevel === 'medium' ? 'bg-amber-50 border-amber-200' :
                      'bg-blue-50 border-blue-200'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-slate-900">{leak.id}</span>
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                              leak.riskLevel === 'high' ? 'bg-red-600 text-white' :
                              leak.riskLevel === 'medium' ? 'bg-amber-500 text-white' :
                              'bg-blue-500 text-white'
                            }`}>
                              {leak.riskLevel.toUpperCase()} RISK
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-slate-700 mb-1">
                            <MapPin className="w-4 h-4" />
                            <span className="font-medium">{leak.location}</span>
                          </div>
                          <p className="text-sm text-slate-500">DMA: {leak.dma}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-slate-900">{leak.probability}%</div>
                          <p className="text-xs text-slate-500">Probability</p>
                          <p className="text-sm font-medium text-red-600 mt-1">~{leak.estimatedLoss} m³/day</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-200">
                    <p className="text-sm text-blue-800">
                      <strong>AI Recommendation:</strong> Prioritize Junction Rd leak (94% probability) - addressing this alone could recover ~K540,000/month in lost revenue.
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Anomaly Scan Modal */}
      {showAnomalyScan && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-red-600 to-orange-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">Anomaly Detection Scan</h2>
                    <p className="text-red-100 text-sm">Real-time pattern analysis across all sensors</p>
                  </div>
                </div>
                <button onClick={() => setShowAnomalyScan(false)} className="p-2 hover:bg-white/20 rounded-lg">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {isProcessing ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-red-500 mx-auto mb-4 animate-pulse" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Scanning Network...</h3>
                  <p className="text-slate-500 mb-4">Analyzing 156 sensors for anomalous patterns</p>
                  <div className="w-64 h-3 bg-slate-100 rounded-full mx-auto overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(processingProgress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-red-600 mt-2">{Math.round(Math.min(processingProgress, 100))}% Complete</p>
                </div>
              ) : anomalies.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <span className="font-semibold text-slate-900">Detected {anomalies.length} Anomalies</span>
                    </div>
                    <div className="flex gap-2">
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full">{anomalies.filter(a => a.severity === 'critical').length} Critical</span>
                      <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full">{anomalies.filter(a => a.severity === 'warning').length} Warning</span>
                    </div>
                  </div>
                  
                  {anomalies.map((anomaly) => (
                    <div key={anomaly.id} className={`p-4 rounded-xl border-l-4 ${
                      anomaly.severity === 'critical' ? 'bg-red-50 border-red-500' :
                      anomaly.severity === 'warning' ? 'bg-amber-50 border-amber-500' :
                      'bg-blue-50 border-blue-500'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                              anomaly.severity === 'critical' ? 'bg-red-600 text-white' :
                              anomaly.severity === 'warning' ? 'bg-amber-500 text-white' :
                              'bg-blue-500 text-white'
                            }`}>
                              {anomaly.severity.toUpperCase()}
                            </span>
                            <span className="font-bold text-slate-900">{anomaly.type}</span>
                          </div>
                          <p className="text-sm text-slate-600 mb-2">{anomaly.description}</p>
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {anomaly.location}
                            </span>
                            <span>Sensor: {anomaly.sensor}</span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(anomaly.detectedAt).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* Route Optimization Modal */}
      {showRouteOptimize && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <Route className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">Route Optimization</h2>
                    <p className="text-purple-100 text-sm">AI-powered dispatch routing for field teams</p>
                  </div>
                </div>
                <button onClick={() => setShowRouteOptimize(false)} className="p-2 hover:bg-white/20 rounded-lg">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {isProcessing ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-purple-500 mx-auto mb-4 animate-pulse" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Optimizing Routes...</h3>
                  <p className="text-slate-500 mb-4">Calculating optimal paths for 4 work orders</p>
                  <div className="w-64 h-3 bg-slate-100 rounded-full mx-auto overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(processingProgress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-purple-600 mt-2">{Math.round(Math.min(processingProgress, 100))}% Complete</p>
                </div>
              ) : optimizedRoute ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-purple-50 rounded-xl p-4 text-center">
                      <p className="text-3xl font-bold text-purple-700">{optimizedRoute.distance} km</p>
                      <p className="text-sm text-purple-600">Total Distance</p>
                    </div>
                    <div className="bg-emerald-50 rounded-xl p-4 text-center">
                      <p className="text-3xl font-bold text-emerald-700">{optimizedRoute.estimatedTime}</p>
                      <p className="text-sm text-emerald-600">Est. Time</p>
                    </div>
                    <div className="bg-blue-50 rounded-xl p-4 text-center">
                      <p className="text-xl font-bold text-blue-700">{optimizedRoute.savings}</p>
                      <p className="text-sm text-blue-600">Efficiency Gain</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-xl p-4">
                    <h4 className="font-semibold text-slate-900 mb-3">Optimized Route</h4>
                    <div className="space-y-2">
                      {optimizedRoute.route.map((stop, i) => (
                        <div key={i} className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                            i === 0 || i === optimizedRoute.route.length - 1 
                              ? 'bg-emerald-100 text-emerald-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {i + 1}
                          </div>
                          <span className="text-slate-700">{stop}</span>
                          {i < optimizedRoute.route.length - 1 && (
                            <ChevronRight className="w-4 h-4 text-slate-400 ml-auto" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-xl p-4">
                    <h4 className="font-semibold text-slate-900 mb-3">Tasks Included</h4>
                    <div className="space-y-2">
                      {optimizedRoute.tasks.map((task, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-slate-600">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          {task}
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <button className="w-full py-3 bg-purple-600 text-white font-semibold rounded-xl hover:bg-purple-700 transition-colors">
                    Send to Technician App
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}

      {/* NRW Report Modal */}
      {showNRWReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">NRW Analysis Report</h2>
                    <p className="text-emerald-100 text-sm">AI-generated insights and recommendations</p>
                  </div>
                </div>
                <button onClick={() => setShowNRWReport(false)} className="p-2 hover:bg-white/20 rounded-lg">
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {isProcessing ? (
                <div className="text-center py-12">
                  <BarChart3 className="w-16 h-16 text-emerald-500 mx-auto mb-4 animate-pulse" />
                  <h3 className="text-lg font-semibold text-slate-900 mb-2">Generating Report...</h3>
                  <p className="text-slate-500 mb-4">Analyzing water balance data and loss patterns</p>
                  <div className="w-64 h-3 bg-slate-100 rounded-full mx-auto overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(processingProgress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-emerald-600 mt-2">{Math.round(Math.min(processingProgress, 100))}% Complete</p>
                </div>
              ) : nrwReport ? (
                <div className="space-y-6">
                  <div className="text-center pb-4 border-b border-slate-200">
                    <h3 className="text-lg font-bold text-slate-900">NRW Report: {nrwReport.period}</h3>
                    <p className="text-sm text-slate-500">Generated by LWSC AI Engine</p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-red-50 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Droplets className="w-5 h-5 text-red-600" />
                        <span className="text-sm text-red-700">Total NRW</span>
                      </div>
                      <p className="text-3xl font-bold text-red-700">{nrwReport.totalNrw}%</p>
                    </div>
                    <div className="bg-emerald-50 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="w-5 h-5 text-emerald-600" />
                        <span className="text-sm text-emerald-700">Revenue Recovered</span>
                      </div>
                      <p className="text-3xl font-bold text-emerald-700">K{nrwReport.recoveredRevenue.toLocaleString()}</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-xl p-4">
                    <h4 className="font-semibold text-slate-900 mb-3">Loss Breakdown</h4>
                    <div className="space-y-3">
                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-slate-600">Physical Losses (Real Losses)</span>
                          <span className="font-medium text-slate-900">{nrwReport.physicalLosses}%</span>
                        </div>
                        <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                          <div className="h-full bg-red-500 rounded-full" style={{ width: `${(nrwReport.physicalLosses / nrwReport.totalNrw) * 100}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-slate-600">Commercial Losses (Apparent Losses)</span>
                          <span className="font-medium text-slate-900">{nrwReport.commercialLosses}%</span>
                        </div>
                        <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full" style={{ width: `${(nrwReport.commercialLosses / nrwReport.totalNrw) * 100}%` }} />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-blue-50 rounded-xl p-4">
                    <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-blue-600" />
                      AI Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {nrwReport.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-blue-800">
                          <span className="w-5 h-5 bg-blue-200 rounded-full flex items-center justify-center text-xs font-bold text-blue-700 flex-shrink-0 mt-0.5">
                            {i + 1}
                          </span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="flex gap-3">
                    <button className="flex-1 py-3 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2">
                      <Download className="w-5 h-5" />
                      Download PDF
                    </button>
                    <button className="flex-1 py-3 border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-colors">
                      Share Report
                    </button>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
