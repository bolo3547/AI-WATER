'use client'

// =============================================================================
// AUTONOMOUS OPERATIONS PAGE - PRODUCTION VERSION
// =============================================================================
// Real-time autonomous valve control, AI decisions, and self-healing network
// Connected to live API - NO DEMO DATA
// =============================================================================

import { useState, useEffect, useCallback } from 'react'
import { 
  Cpu, Power, Wifi, AlertTriangle, CheckCircle, 
  Settings, Activity, Zap, Shield, RefreshCw,
  Play, Pause, ChevronRight, ArrowRight, Clock,
  Network, GitBranch, Gauge, BarChart3, Eye,
  Globe, Server, Radio, Bot, Brain, Sparkles,
  XCircle, CheckCircle2, AlertCircle, Loader2,
  Users, Droplets, Timer, TrendingUp, WifiOff
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'
import {
  Valve,
  NetworkSegment,
  AIDecision,
  PendingAction,
  AutonomousStats,
  getValves,
  getNetworkSegments,
  getDecisions,
  getPendingActions,
  getStats,
  controlValve,
  toggleValveAutoMode,
  setAutonomyLevel,
  toggleEmergencyMode,
  approveAction,
  rejectAction,
  simulateIncident,
  subscribeToUpdates,
  getValveStatusColor,
  getSegmentStatusColor,
  getAutonomyLevelInfo,
  formatTimeAgo
} from '@/lib/autonomous-service'

export default function AutonomousPage() {
  // State
  const [activeTab, setActiveTab] = useState('valves')
  const [valves, setValves] = useState<Valve[]>([])
  const [segments, setSegments] = useState<NetworkSegment[]>([])
  const [decisions, setDecisions] = useState<AIDecision[]>([])
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([])
  const [stats, setStats] = useState<AutonomousStats | null>(null)
  const [selectedValve, setSelectedValve] = useState<Valve | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  
  // Computed values
  const autonomousMode = stats?.autonomyLevel ? stats.autonomyLevel >= 2 : false
  const isEmergencyMode = stats?.emergencyMode || false

  // Load all data
  const loadData = useCallback(async () => {
    try {
      const [valvesData, segmentsData, decisionsData, pendingData, statsData] = await Promise.all([
        getValves(),
        getNetworkSegments(),
        getDecisions(50),
        getPendingActions(),
        getStats()
      ])
      
      setValves(valvesData)
      setSegments(segmentsData)
      setDecisions(decisionsData)
      setPendingActions(pendingData)
      setStats(statsData)
      setError(null)
    } catch (err) {
      console.error('Failed to load autonomous data:', err)
      setError('Failed to load system data')
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load and real-time updates
  useEffect(() => {
    loadData()
    
    // Subscribe to real-time updates
    const unsubscribe = subscribeToUpdates((state) => {
      setValves(state.valves)
      setSegments(state.segments)
      setDecisions(state.decisions)
      setPendingActions(state.pendingActions)
      if (state.stats) {
        setStats({
          ...state.stats,
          autonomyLevel: state.autonomyLevel,
          emergencyMode: state.emergencyMode,
        } as AutonomousStats)
      }
    }, 5000) // Update every 5 seconds
    
    return () => unsubscribe()
  }, [loadData])

  // Handlers
  const handleValveControl = async (valveId: string, position: number) => {
    setActionLoading(valveId)
    const result = await controlValve(valveId, position, 'Manual operator adjustment', true)
    if (result.success && result.valve) {
      setValves(prev => prev.map(v => v.id === valveId ? result.valve! : v))
      if (result.decision) {
        setDecisions(prev => [result.decision!, ...prev])
      }
    }
    setActionLoading(null)
  }

  const handleToggleAutoMode = async (valveId: string, enabled: boolean) => {
    setActionLoading(valveId)
    const result = await toggleValveAutoMode(valveId, enabled)
    if (result.success && result.valve) {
      setValves(prev => prev.map(v => v.id === valveId ? result.valve! : v))
      setSelectedValve(result.valve)
    }
    setActionLoading(null)
  }

  const handleSetAutonomyLevel = async (level: number) => {
    setActionLoading('autonomy')
    const result = await setAutonomyLevel(level)
    if (result.success) {
      setStats(prev => prev ? { ...prev, autonomyLevel: level } : null)
    }
    setActionLoading(null)
  }

  const handleToggleEmergency = async () => {
    setActionLoading('emergency')
    const newState = !isEmergencyMode
    const result = await toggleEmergencyMode(newState, newState ? 'Manual emergency activation' : 'Emergency resolved')
    if (result.success) {
      setStats(prev => prev ? { ...prev, emergencyMode: newState } : null)
      await loadData() // Reload all data as emergency mode changes valve states
    }
    setActionLoading(null)
  }

  const handleApproveAction = async (actionId: string) => {
    setActionLoading(actionId)
    const result = await approveAction(actionId)
    if (result.success) {
      setPendingActions(prev => prev.filter(a => a.id !== actionId))
      await loadData() // Reload decisions
    }
    setActionLoading(null)
  }

  const handleRejectAction = async (actionId: string) => {
    setActionLoading(actionId)
    const result = await rejectAction(actionId)
    if (result.success) {
      setPendingActions(prev => prev.filter(a => a.id !== actionId))
    }
    setActionLoading(null)
  }

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-600 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Loading Autonomous Operations...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <WifiOff className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 font-semibold">{error}</p>
          <Button variant="secondary" onClick={loadData} className="mt-4">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  const autonomyInfo = getAutonomyLevelInfo(stats?.autonomyLevel || 0)

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
            AI-controlled valve management & self-healing network • Level {stats?.autonomyLevel || 0}: {autonomyInfo.name}
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Autonomy Level Selector */}
          <select
            value={stats?.autonomyLevel || 0}
            onChange={(e) => handleSetAutonomyLevel(parseInt(e.target.value))}
            disabled={actionLoading === 'autonomy'}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm font-medium bg-white"
          >
            <option value={0}>Level 0: Manual</option>
            <option value={1}>Level 1: Assisted</option>
            <option value={2}>Level 2: Supervised</option>
            <option value={3}>Level 3: Conditional</option>
            <option value={4}>Level 4: High Autonomy</option>
            <option value={5}>Level 5: Full Autonomy</option>
          </select>

          {/* Autonomous Mode Indicator */}
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl ${autonomousMode ? 'bg-green-100' : 'bg-slate-100'}`}>
            <span className={`w-2 h-2 rounded-full ${autonomousMode ? 'bg-green-500 animate-pulse' : 'bg-slate-400'}`} />
            <span className={`text-sm font-medium ${autonomousMode ? 'text-green-700' : 'text-slate-600'}`}>
              {autonomousMode ? 'Autonomous Active' : 'Manual Mode'}
            </span>
          </div>

          {/* Emergency Button */}
          <button
            onClick={handleToggleEmergency}
            disabled={actionLoading === 'emergency'}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              isEmergencyMode 
                ? 'bg-red-500 text-white animate-pulse hover:bg-red-600' 
                : 'bg-slate-200 text-slate-700 hover:bg-red-100 hover:text-red-700'
            }`}
          >
            {actionLoading === 'emergency' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isEmergencyMode ? (
              '🚨 EMERGENCY ACTIVE'
            ) : (
              '🚨 Emergency'
            )}
          </button>
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
              <p className="text-purple-200 text-sm">Real-time network optimization • Live Data</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-purple-200">System Status:</span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white/20 rounded-full text-sm">
              {isEmergencyMode ? (
                <>
                  <AlertTriangle className="w-4 h-4 text-red-300 animate-pulse" />
                  Emergency Mode
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 text-green-300" />
                  All Systems Operational
                </>
              )}
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold">{stats?.aiControlled || 0}</p>
            <p className="text-purple-200 text-xs">AI Controlled</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold">{stats?.healthySegments || 0}/{stats?.totalSegments || 0}</p>
            <p className="text-purple-200 text-xs">Healthy Segments</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold text-green-300">{stats?.waterSavedToday || 0}</p>
            <p className="text-purple-200 text-xs">m³ Saved Today</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold text-yellow-300">{stats?.decisionsToday || 0}</p>
            <p className="text-purple-200 text-xs">AI Decisions</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold text-cyan-300">{stats?.incidentsHandled || 0}</p>
            <p className="text-purple-200 text-xs">Incidents Handled</p>
          </div>
          <div className="bg-white/10 rounded-xl p-3 text-center">
            <p className="text-3xl font-bold">{stats?.uptime?.toFixed(2) || 0}%</p>
            <p className="text-purple-200 text-xs">System Uptime</p>
          </div>
        </div>
      </div>

      {/* Pending Actions Alert */}
      {pendingActions.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-orange-600" />
            <h3 className="font-semibold text-orange-800">
              {pendingActions.length} Action{pendingActions.length > 1 ? 's' : ''} Awaiting Approval
            </h3>
          </div>
          <div className="space-y-2">
            {pendingActions.slice(0, 3).map((action) => (
              <div key={action.id} className="flex items-center justify-between bg-white rounded-lg p-3">
                <div>
                  <p className="font-medium text-slate-900">{action.type}: {action.target}</p>
                  <p className="text-xs text-slate-500">Risk: {(action.riskScore * 100).toFixed(0)}% • {action.affectedCustomers} customers affected</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApproveAction(action.id)}
                    disabled={actionLoading === action.id}
                    className="px-3 py-1 bg-green-500 text-white rounded-lg text-sm hover:bg-green-600"
                  >
                    {actionLoading === action.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Approve'}
                  </button>
                  <button
                    onClick={() => handleRejectAction(action.id)}
                    disabled={actionLoading === action.id}
                    className="px-3 py-1 bg-red-100 text-red-700 rounded-lg text-sm hover:bg-red-200"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'valves', label: `Valve Control (${valves.length})` },
          { id: 'network', label: `Self-Healing Network (${segments.length})` },
          { id: 'decisions', label: `AI Decisions (${decisions.length})` }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* VALVES TAB */}
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
                    <p className="font-semibold text-slate-900 text-sm">{valve.name}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getValveStatusColor(valve.status)}`}>
                    {valve.status.toUpperCase()}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] ${
                    valve.actuatorStatus === 'online' ? 'bg-green-100 text-green-700' :
                    valve.actuatorStatus === 'degraded' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {valve.actuatorStatus}
                  </span>
                </div>
              </div>

              {/* Valve Visual */}
              <div className="relative h-4 bg-slate-200 rounded-full overflow-hidden mb-3">
                <div 
                  className={`h-full transition-all duration-500 ${
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

              <div className="grid grid-cols-3 gap-1 sm:gap-2 text-center text-xs mb-3">
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="font-semibold text-slate-900">{valve.pressure.toFixed(1)}</p>
                  <p className="text-slate-500">bar</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className="font-semibold text-slate-900">{valve.flow}</p>
                  <p className="text-slate-500">m³/hr</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-2">
                  <p className={`font-semibold ${valve.health > 80 ? 'text-green-600' : valve.health > 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {valve.health}%
                  </p>
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

      {/* NETWORK TAB */}
      {activeTab === 'network' && (
        <div className="space-y-4">
          {/* Network Visualization */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-4 sm:p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Network className="w-5 h-5" />
              Network Topology - Live Status
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {segments.map((segment) => (
                <div key={segment.id} className="bg-white/10 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-3 h-3 rounded-full ${getSegmentStatusColor(segment.status)} ${
                      segment.status !== 'healthy' ? 'animate-pulse' : ''
                    }`} />
                    <span className="text-white text-xs font-medium truncate">{segment.name}</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span>In:</span>
                      <span className="text-white font-semibold">{segment.flowIn}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Out:</span>
                      <span className="text-white font-semibold">{segment.flowOut}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Loss:</span>
                      <span className={`font-semibold ${
                        segment.flowIn - segment.flowOut > 50 ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {segment.flowIn - segment.flowOut} m³/hr
                      </span>
                    </div>
                    {segment.leakDetected && (
                      <div className="flex items-center gap-1 text-red-400 mt-2">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Leak!</span>
                      </div>
                    )}
                    {segment.autoHealing && segment.status !== 'healthy' && (
                      <div className="flex items-center gap-1 text-cyan-400">
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>Healing</span>
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
                        <p className="text-xs text-slate-500">
                          {segment.dma} • {segment.activeValves} valves • {segment.affectedCustomers.toLocaleString()} customers
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className={`text-sm font-semibold ${
                          segment.flowIn - segment.flowOut > 50 ? 'text-red-600' : 'text-slate-900'
                        }`}>
                          {segment.flowIn - segment.flowOut} m³/hr
                        </p>
                        <p className="text-xs text-slate-500">Loss</p>
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
                  {segment.lastIncident && (
                    <div className="mt-2 text-xs text-slate-500">
                      Last incident: {formatTimeAgo(segment.lastIncident)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      )}

      {/* DECISIONS TAB */}
      {activeTab === 'decisions' && (
        <SectionCard 
          title="AI Decision Log" 
          subtitle="Autonomous decisions made by the AI control engine - Live Feed"
          noPadding
        >
          <div className="divide-y divide-slate-100">
            {decisions.map((decision) => (
              <div key={decision.id} className="p-4 hover:bg-slate-50">
                <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                  <div className={`w-10 h-10 rounded-lg flex-shrink-0 flex items-center justify-center ${
                    decision.type === 'isolation' ? 'bg-red-100' :
                    decision.type === 'reroute' ? 'bg-yellow-100' :
                    decision.type === 'pressure_adjust' ? 'bg-blue-100' :
                    decision.type === 'dispatch' ? 'bg-purple-100' :
                    decision.type === 'notify' ? 'bg-cyan-100' : 'bg-orange-100'
                  }`}>
                    {decision.type === 'isolation' && <Shield className="w-5 h-5 text-red-600" />}
                    {decision.type === 'reroute' && <GitBranch className="w-5 h-5 text-yellow-600" />}
                    {decision.type === 'pressure_adjust' && <Gauge className="w-5 h-5 text-blue-600" />}
                    {decision.type === 'valve_control' && <Settings className="w-5 h-5 text-slate-600" />}
                    {decision.type === 'dispatch' && <Users className="w-5 h-5 text-purple-600" />}
                    {decision.type === 'notify' && <Activity className="w-5 h-5 text-cyan-600" />}
                    {decision.type === 'alert' && <AlertTriangle className="w-5 h-5 text-orange-600" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-slate-400">{decision.id.substring(0, 12)}</span>
                      <span className="text-xs text-slate-500">{formatTimeAgo(decision.timestamp)}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        decision.status === 'executed' ? 'bg-green-100 text-green-700' :
                        decision.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                        decision.status === 'overridden' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {decision.status}
                      </span>
                      <span className="text-xs text-purple-600 flex items-center gap-1">
                        <Brain className="w-3 h-3" />
                        {decision.confidence.toFixed(0)}% confident
                      </span>
                    </div>
                    <p className="font-semibold text-slate-900 mt-1">{decision.action}</p>
                    <p className="text-sm text-slate-600 mt-1">{decision.reason}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <span>Area: {decision.affectedArea}</span>
                      <span>By: {decision.triggeredBy}</span>
                      {decision.waterSaved > 0 && (
                        <span className="text-green-600 flex items-center gap-1">
                          <Droplets className="w-3 h-3" />
                          {decision.waterSaved} m³ saved
                        </span>
                      )}
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
                  onChange={(e) => {
                    const newPosition = parseInt(e.target.value)
                    setSelectedValve({ ...selectedValve, openPercent: newPosition })
                  }}
                  onMouseUp={(e) => {
                    if (!selectedValve.autoMode) {
                      handleValveControl(selectedValve.id, selectedValve.openPercent)
                    }
                  }}
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
              <div className="grid grid-cols-3 gap-1 sm:gap-2">
                <Button 
                  variant="secondary" 
                  disabled={selectedValve.autoMode || actionLoading === selectedValve.id}
                  onClick={() => handleValveControl(selectedValve.id, 0)}
                >
                  {actionLoading === selectedValve.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Close'}
                </Button>
                <Button 
                  variant="secondary" 
                  disabled={selectedValve.autoMode || actionLoading === selectedValve.id}
                  onClick={() => handleValveControl(selectedValve.id, 50)}
                >
                  50%
                </Button>
                <Button 
                  variant="secondary" 
                  disabled={selectedValve.autoMode || actionLoading === selectedValve.id}
                  onClick={() => handleValveControl(selectedValve.id, 100)}
                >
                  Open
                </Button>
              </div>

              {/* Valve Info */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Type</p>
                  <p className="font-semibold capitalize">{selectedValve.type}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">DMA</p>
                  <p className="font-semibold">{selectedValve.dma}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Last Action</p>
                  <p className="font-semibold">{formatTimeAgo(selectedValve.lastAction)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">By</p>
                  <p className="font-semibold capitalize">{selectedValve.lastActionBy}</p>
                </div>
              </div>

              {/* Auto Mode */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-semibold text-slate-900">Autonomous Mode</p>
                  <p className="text-xs text-slate-500">Let AI control this valve</p>
                </div>
                <button 
                  onClick={() => handleToggleAutoMode(selectedValve.id, !selectedValve.autoMode)}
                  disabled={actionLoading === selectedValve.id}
                  className={`w-12 h-6 rounded-full transition-colors relative ${selectedValve.autoMode ? 'bg-green-500' : 'bg-slate-300'}`}
                >
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${selectedValve.autoMode ? 'left-7' : 'left-1'}`} />
                </button>
              </div>

              {selectedValve.autoMode && (
                <div className="bg-purple-50 rounded-lg p-3 text-sm text-purple-700 flex items-center gap-2">
                  <Bot className="w-4 h-4" />
                  This valve is controlled by AI. Disable autonomous mode for manual control.
                </div>
              )}

              {selectedValve.actuatorStatus !== 'online' && (
                <div className="bg-red-50 rounded-lg p-3 text-sm text-red-700 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Actuator status: {selectedValve.actuatorStatus}. Remote control may be limited.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
