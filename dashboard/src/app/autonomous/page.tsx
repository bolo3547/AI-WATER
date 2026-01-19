'use client'

import { useState, useEffect } from 'react'
import { 
  Cpu, Power, Wifi, AlertTriangle, CheckCircle, 
  Settings, Activity, Zap, Shield, RefreshCw,
  Play, Pause, ChevronRight, ArrowRight, Clock,
  Network, GitBranch, Gauge, BarChart3, Eye,
  Globe, Server, Radio, Bot, Brain, Sparkles
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface Valve {
  id: string
  name: string
  location: string
  dma: string
  status: 'open' | 'closed' | 'partial' | 'error'
  openPercent: number
  pressure: number
  flow: number
  autoMode: boolean
  lastAction: string
  controlledBy: 'manual' | 'ai' | 'schedule'
  health: number
}

interface NetworkSegment {
  id: string
  name: string
  dma: string
  status: 'healthy' | 'isolated' | 'rerouting' | 'alert'
  flowIn: number
  flowOut: number
  pressure: number
  activeValves: number
  leakDetected: boolean
  autoHealing: boolean
  lastIncident: string | null
}

interface AIDecision {
  id: string
  timestamp: string
  type: 'valve_control' | 'isolation' | 'reroute' | 'pressure_adjust' | 'alert'
  action: string
  reason: string
  affectedArea: string
  status: 'executed' | 'pending' | 'overridden' | 'failed'
  impact: string
  confidence: number
}

export default function AutonomousPage() {
  const [activeTab, setActiveTab] = useState('valves')
  const [valves, setValves] = useState<Valve[]>([])
  const [segments, setSegments] = useState<NetworkSegment[]>([])
  const [decisions, setDecisions] = useState<AIDecision[]>([])
  const [selectedValve, setSelectedValve] = useState<Valve | null>(null)
  const [autonomousMode, setAutonomousMode] = useState(true)
  const [isEmergencyMode, setIsEmergencyMode] = useState(false)

  useEffect(() => {
    loadValves()
    loadSegments()
    loadDecisions()
  }, [])

  const loadValves = () => {
    setValves([
      {
        id: 'VLV-001',
        name: 'Main Trunk Valve K1',
        location: 'Kabulonga Reservoir',
        dma: 'Kabulonga',
        status: 'open',
        openPercent: 100,
        pressure: 4.2,
        flow: 850,
        autoMode: true,
        lastAction: '2 hours ago',
        controlledBy: 'ai',
        health: 95
      },
      {
        id: 'VLV-002',
        name: 'Roma Distribution Gate',
        location: 'Roma Junction',
        dma: 'Roma',
        status: 'partial',
        openPercent: 65,
        pressure: 3.8,
        flow: 420,
        autoMode: true,
        lastAction: '30 min ago',
        controlledBy: 'ai',
        health: 88
      },
      {
        id: 'VLV-003',
        name: 'Chelstone Pressure Reducer',
        location: 'Chelstone Main',
        dma: 'Chelstone',
        status: 'partial',
        openPercent: 45,
        pressure: 2.5,
        flow: 310,
        autoMode: true,
        lastAction: '15 min ago',
        controlledBy: 'schedule',
        health: 92
      },
      {
        id: 'VLV-004',
        name: 'Matero Isolation Valve',
        location: 'Matero Industrial',
        dma: 'Matero',
        status: 'closed',
        openPercent: 0,
        pressure: 0,
        flow: 0,
        autoMode: true,
        lastAction: '5 min ago',
        controlledBy: 'ai',
        health: 100
      },
      {
        id: 'VLV-005',
        name: 'Woodlands Branch Gate',
        location: 'Woodlands Shopping',
        dma: 'Woodlands',
        status: 'error',
        openPercent: 78,
        pressure: 3.2,
        flow: 180,
        autoMode: false,
        lastAction: 'Manual override',
        controlledBy: 'manual',
        health: 45
      },
      {
        id: 'VLV-006',
        name: 'Chilenje PRV Station',
        location: 'Chilenje South',
        dma: 'Chilenje',
        status: 'open',
        openPercent: 100,
        pressure: 3.9,
        flow: 520,
        autoMode: true,
        lastAction: '1 hour ago',
        controlledBy: 'ai',
        health: 98
      }
    ])
  }

  const loadSegments = () => {
    setSegments([
      {
        id: 'SEG-001',
        name: 'Kabulonga Main Line',
        dma: 'Kabulonga',
        status: 'healthy',
        flowIn: 850,
        flowOut: 830,
        pressure: 4.0,
        activeValves: 3,
        leakDetected: false,
        autoHealing: true,
        lastIncident: null
      },
      {
        id: 'SEG-002',
        name: 'Roma Supply Network',
        dma: 'Roma',
        status: 'rerouting',
        flowIn: 620,
        flowOut: 580,
        pressure: 3.5,
        activeValves: 4,
        leakDetected: true,
        autoHealing: true,
        lastIncident: '2026-01-29 08:30'
      },
      {
        id: 'SEG-003',
        name: 'Matero Industrial Zone',
        dma: 'Matero',
        status: 'isolated',
        flowIn: 0,
        flowOut: 0,
        pressure: 0,
        activeValves: 2,
        leakDetected: true,
        autoHealing: true,
        lastIncident: '2026-01-29 10:15'
      },
      {
        id: 'SEG-004',
        name: 'Chelstone Residential',
        dma: 'Chelstone',
        status: 'healthy',
        flowIn: 450,
        flowOut: 440,
        pressure: 2.8,
        activeValves: 3,
        leakDetected: false,
        autoHealing: true,
        lastIncident: null
      }
    ])
  }

  const loadDecisions = () => {
    setDecisions([
      {
        id: 'DEC-001',
        timestamp: '2026-01-29 10:15',
        type: 'isolation',
        action: 'Close VLV-004 (Matero Isolation)',
        reason: 'Major leak detected - flow anomaly 280% above normal',
        affectedArea: 'Matero Industrial Zone',
        status: 'executed',
        impact: 'Isolated leak, prevented 450 m³/hr water loss',
        confidence: 97
      },
      {
        id: 'DEC-002',
        timestamp: '2026-01-29 10:16',
        type: 'reroute',
        action: 'Increase flow through VLV-002 to 65%',
        reason: 'Maintain pressure for Roma after Matero isolation',
        affectedArea: 'Roma Distribution',
        status: 'executed',
        impact: 'Maintained service to 12,000 customers',
        confidence: 94
      },
      {
        id: 'DEC-003',
        timestamp: '2026-01-29 09:45',
        type: 'pressure_adjust',
        action: 'Reduce VLV-003 to 45% open',
        reason: 'Night-time pressure optimization',
        affectedArea: 'Chelstone',
        status: 'executed',
        impact: 'Reduced background losses by 15%',
        confidence: 89
      },
      {
        id: 'DEC-004',
        timestamp: '2026-01-29 08:30',
        type: 'alert',
        action: 'Generate work order WO-2854',
        reason: 'Valve VLV-005 health degradation detected',
        affectedArea: 'Woodlands',
        status: 'pending',
        impact: 'Scheduled maintenance to prevent failure',
        confidence: 86
      }
    ])
  }

  const getValveStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-green-100 text-green-700 border-green-200'
      case 'closed': return 'bg-red-100 text-red-700 border-red-200'
      case 'partial': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'error': return 'bg-red-100 text-red-700 border-red-200 animate-pulse'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getSegmentStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500'
      case 'isolated': return 'bg-red-500'
      case 'rerouting': return 'bg-yellow-500 animate-pulse'
      case 'alert': return 'bg-orange-500 animate-pulse'
      default: return 'bg-gray-500'
    }
  }

  const stats = {
    totalValves: valves.length,
    autoValves: valves.filter(v => v.autoMode).length,
    aiControlled: valves.filter(v => v.controlledBy === 'ai').length,
    errors: valves.filter(v => v.status === 'error').length,
    healthySegments: segments.filter(s => s.status === 'healthy').length,
    isolatedSegments: segments.filter(s => s.status === 'isolated').length,
    decisionsToday: decisions.length,
    waterSaved: 450 // m³
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bot className="w-6 h-6 sm:w-7 sm:h-7 text-purple-600" />
            Autonomous Operations
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AI-controlled valve management & self-healing network
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Autonomous Mode Toggle */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${autonomousMode ? 'bg-green-100' : 'bg-slate-100'}`}>
            <span className={`w-2 h-2 rounded-full ${autonomousMode ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`} />
            <span className={`text-sm font-medium ${autonomousMode ? 'text-green-700' : 'text-slate-600'}`}>
              {autonomousMode ? 'Autonomous Active' : 'Manual Mode'}
            </span>
            <button
              onClick={() => setAutonomousMode(!autonomousMode)}
              className={`w-12 h-6 rounded-full transition-colors relative ${autonomousMode ? 'bg-green-500' : 'bg-slate-300'}`}
            >
              <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${autonomousMode ? 'left-7' : 'left-1'}`} />
            </button>
          </div>
          {isEmergencyMode && (
            <span className="px-3 py-1 bg-red-500 text-white rounded-lg text-sm font-semibold animate-pulse">
              🚨 EMERGENCY
            </span>
          )}
        </div>
      </div>

      {/* AI Control Center */}
      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 rounded-xl p-4 sm:p-6 text-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl bg-white/20 flex items-center justify-center">
              <Brain className="w-8 h-8" />
            </div>
            <div>
              <h3 className="font-bold text-lg flex items-center gap-2">
                AI Control Engine
                <Sparkles className="w-4 h-4 text-yellow-300" />
              </h3>
              <p className="text-purple-200 text-sm">Real-time network optimization</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-purple-200">System Status:</span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white/20 rounded-full text-sm">
              <CheckCircle className="w-4 h-4 text-green-300" />
              All Systems Operational
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold">{stats.aiControlled}</p>
            <p className="text-purple-200 text-xs">AI Controlled Valves</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold">{stats.healthySegments}/{segments.length}</p>
            <p className="text-purple-200 text-xs">Healthy Segments</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold text-green-300">{stats.waterSaved}</p>
            <p className="text-purple-200 text-xs">m³ Saved Today</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold text-yellow-300">{stats.decisionsToday}</p>
            <p className="text-purple-200 text-xs">AI Decisions Today</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'valves', label: 'Valve Control' },
          { id: 'network', label: 'Self-Healing Network' },
          { id: 'decisions', label: 'AI Decisions' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'valves' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {valves.map((valve) => (
            <div 
              key={valve.id}
              className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-lg transition-all cursor-pointer"
              onClick={() => setSelectedValve(valve)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    valve.status === 'open' ? 'bg-green-100' :
                    valve.status === 'closed' ? 'bg-red-100' :
                    valve.status === 'error' ? 'bg-red-100' : 'bg-yellow-100'
                  }`}>
                    <Settings className={`w-6 h-6 ${
                      valve.status === 'open' ? 'text-green-600' :
                      valve.status === 'closed' ? 'text-red-600' :
                      valve.status === 'error' ? 'text-red-600 animate-spin' : 'text-yellow-600'
                    }`} />
                  </div>
                  <div>
                    <p className="font-mono text-xs text-slate-400">{valve.id}</p>
                    <p className="font-semibold text-slate-900">{valve.name}</p>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getValveStatusColor(valve.status)}`}>
                  {valve.status.toUpperCase()}
                </span>
              </div>

              {/* Valve Visual */}
              <div className="relative h-4 bg-slate-200 rounded-full overflow-hidden mb-3">
                <div 
                  className={`h-full transition-all ${
                    valve.status === 'open' ? 'bg-green-500' :
                    valve.status === 'closed' ? 'bg-red-500' : 
                    valve.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}
                  style={{ width: `${valve.openPercent}%` }}
                />
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white mix-blend-difference">
                  {valve.openPercent}% OPEN
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs mb-3">
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="font-semibold text-slate-900">{valve.pressure}</p>
                  <p className="text-slate-500">bar</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="font-semibold text-slate-900">{valve.flow}</p>
                  <p className="text-slate-500">m³/hr</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="font-semibold text-slate-900">{valve.health}%</p>
                  <p className="text-slate-500">health</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1 text-slate-500">
                  {valve.controlledBy === 'ai' && <Bot className="w-3 h-3 text-purple-500" />}
                  {valve.controlledBy === 'schedule' && <Clock className="w-3 h-3 text-blue-500" />}
                  {valve.controlledBy === 'manual' && <Settings className="w-3 h-3 text-slate-500" />}
                  {valve.controlledBy}
                </span>
                <span className={`flex items-center gap-1 ${valve.autoMode ? 'text-green-600' : 'text-slate-500'}`}>
                  {valve.autoMode ? <Zap className="w-3 h-3" /> : <Power className="w-3 h-3" />}
                  {valve.autoMode ? 'Auto' : 'Manual'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'network' && (
        <div className="space-y-4">
          {/* Network Visualization */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 sm:p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Network className="w-5 h-5" />
              Network Topology
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {segments.map((segment) => (
                <div key={segment.id} className="bg-white/10 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-3 h-3 rounded-full ${getSegmentStatusColor(segment.status)}`} />
                    <span className="text-white text-sm font-medium">{segment.name}</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span>Flow In:</span>
                      <span className="text-white font-semibold">{segment.flowIn} m³/hr</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Flow Out:</span>
                      <span className="text-white font-semibold">{segment.flowOut} m³/hr</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Status:</span>
                      <span className={`font-semibold ${
                        segment.status === 'healthy' ? 'text-green-400' :
                        segment.status === 'isolated' ? 'text-red-400' :
                        segment.status === 'rerouting' ? 'text-yellow-400' : 'text-orange-400'
                      }`}>
                        {segment.status}
                      </span>
                    </div>
                    {segment.leakDetected && (
                      <div className="flex items-center gap-1 text-red-400">
                        <AlertTriangle className="w-3 h-3" />
                        Leak Detected
                      </div>
                    )}
                    {segment.autoHealing && segment.status !== 'healthy' && (
                      <div className="flex items-center gap-1 text-cyan-400">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        Self-healing active
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Segment Details */}
          <SectionCard title="Network Segments" subtitle="Real-time segment health and flow balance">
            <div className="space-y-3">
              {segments.map((segment) => (
                <div key={segment.id} className="bg-slate-50 rounded-xl p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${getSegmentStatusColor(segment.status)}`} />
                      <div>
                        <p className="font-semibold text-slate-900">{segment.name}</p>
                        <p className="text-xs text-slate-500">{segment.dma} DMA • {segment.activeValves} valves</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-sm font-semibold text-slate-900">{segment.flowIn - segment.flowOut}</p>
                        <p className="text-xs text-slate-500">Loss (m³/hr)</p>
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-slate-900">{segment.pressure} bar</p>
                        <p className="text-xs text-slate-500">Pressure</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        segment.status === 'healthy' ? 'bg-green-100 text-green-700' :
                        segment.status === 'isolated' ? 'bg-red-100 text-red-700' :
                        segment.status === 'rerouting' ? 'bg-yellow-100 text-yellow-700' : 'bg-orange-100 text-orange-700'
                      }`}>
                        {segment.status}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      )}

      {activeTab === 'decisions' && (
        <SectionCard 
          title="AI Decision Log" 
          subtitle="Autonomous decisions made by the AI control engine"
          noPadding
        >
          <div className="divide-y divide-slate-100">
            {decisions.map((decision) => (
              <div key={decision.id} className="p-4 hover:bg-slate-50">
                <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className={`w-10 h-10 rounded-lg flex-shrink-0 flex items-center justify-center ${
                    decision.type === 'isolation' ? 'bg-red-100' :
                    decision.type === 'reroute' ? 'bg-yellow-100' :
                    decision.type === 'pressure_adjust' ? 'bg-blue-100' : 'bg-orange-100'
                  }`}>
                    {decision.type === 'isolation' && <Shield className="w-5 h-5 text-red-600" />}
                    {decision.type === 'reroute' && <GitBranch className="w-5 h-5 text-yellow-600" />}
                    {decision.type === 'pressure_adjust' && <Gauge className="w-5 h-5 text-blue-600" />}
                    {decision.type === 'alert' && <AlertTriangle className="w-5 h-5 text-orange-600" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-slate-400">{decision.id}</span>
                      <span className="text-xs text-slate-500">{decision.timestamp}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        decision.status === 'executed' ? 'bg-green-100 text-green-700' :
                        decision.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        decision.status === 'overridden' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {decision.status}
                      </span>
                    </div>
                    <p className="font-semibold text-slate-900 mt-1">{decision.action}</p>
                    <p className="text-sm text-slate-600 mt-1">{decision.reason}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <span>Area: {decision.affectedArea}</span>
                      <span>Confidence: {decision.confidence}%</span>
                    </div>
                    <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                      <CheckCircle className="w-4 h-4" />
                      {decision.impact}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Valve Control Modal */}
      {selectedValve && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className={`p-6 ${
              selectedValve.status === 'open' ? 'bg-green-600' :
              selectedValve.status === 'closed' ? 'bg-red-600' :
              selectedValve.status === 'error' ? 'bg-red-600' : 'bg-yellow-600'
            } text-white rounded-t-2xl`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/70 text-sm font-mono">{selectedValve.id}</p>
                  <h2 className="text-xl font-bold">{selectedValve.name}</h2>
                  <p className="text-white/70 mt-1">{selectedValve.location}</p>
                </div>
                <button onClick={() => setSelectedValve(null)} className="p-2 hover:bg-white/20 rounded-lg">✕</button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {/* Position Slider */}
              <div>
                <label className="text-sm text-slate-600 mb-2 block">Valve Position</label>
                <input 
                  type="range" 
                  min="0" 
                  max="100" 
                  value={selectedValve.openPercent}
                  className="w-full"
                  disabled={selectedValve.autoMode}
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>Closed</span>
                  <span className="font-semibold">{selectedValve.openPercent}%</span>
                  <span>Open</span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-3 gap-2">
                <Button variant="secondary" disabled={selectedValve.autoMode}>
                  <Power className="w-4 h-4" />
                  Close
                </Button>
                <Button variant="secondary" disabled={selectedValve.autoMode}>
                  50%
                </Button>
                <Button variant="secondary" disabled={selectedValve.autoMode}>
                  <Power className="w-4 h-4" />
                  Open
                </Button>
              </div>

              {/* Auto Mode */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-semibold text-slate-900">Autonomous Mode</p>
                  <p className="text-xs text-slate-500">Let AI control this valve</p>
                </div>
                <button className={`w-12 h-6 rounded-full transition-colors relative ${selectedValve.autoMode ? 'bg-green-500' : 'bg-slate-300'}`}>
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${selectedValve.autoMode ? 'left-7' : 'left-1'}`} />
                </button>
              </div>

              {selectedValve.autoMode && (
                <div className="bg-purple-50 rounded-lg p-3 text-sm text-purple-700 flex items-center gap-2">
                  <Bot className="w-4 h-4" />
                  This valve is controlled by AI. Disable autonomous mode for manual control.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
