'use client'

import { useState, useEffect } from 'react'
import { 
  TrendingUp, TrendingDown, Droplets, DollarSign, Clock, AlertTriangle,
  Users, Wrench, Target, Award, Download, Calendar, ChevronRight,
  ArrowUpRight, ArrowDownRight, CheckCircle2, XCircle, Zap
} from 'lucide-react'

// KPI Card Component
function KPICard({ 
  title, 
  value, 
  unit, 
  change, 
  changeType, 
  icon: Icon, 
  color,
  subtitle 
}: {
  title: string
  value: string | number
  unit?: string
  change?: number
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: any
  color: string
  subtitle?: string
}) {
  const colorClasses: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-emerald-500 to-emerald-600',
    amber: 'from-amber-500 to-amber-600',
    red: 'from-red-500 to-red-600',
    purple: 'from-purple-500 to-purple-600',
    cyan: 'from-cyan-500 to-cyan-600',
  }

  return (
    <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center shadow-lg`}>
          <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
            changeType === 'positive' ? 'bg-emerald-100 text-emerald-700' :
            changeType === 'negative' ? 'bg-red-100 text-red-700' :
            'bg-slate-100 text-slate-600'
          }`}>
            {changeType === 'positive' ? <ArrowUpRight className="w-3 h-3" /> : 
             changeType === 'negative' ? <ArrowDownRight className="w-3 h-3" /> : null}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="mt-3 sm:mt-4">
        <p className="text-xs sm:text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-xl sm:text-3xl font-bold text-slate-900 mt-1">
          {value}
          {unit && <span className="text-base sm:text-lg font-medium text-slate-400 ml-1">{unit}</span>}
        </p>
        {subtitle && <p className="text-[10px] sm:text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
    </div>
  )
}

// Mini Chart Component
function MiniChart({ data, color }: { data: number[], color: string }) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1

  return (
    <div className="flex items-end gap-1 h-12">
      {data.map((value, i) => (
        <div
          key={i}
          className={`flex-1 rounded-t ${color} transition-all duration-300 hover:opacity-80`}
          style={{ height: `${((value - min) / range) * 100}%`, minHeight: '4px' }}
        />
      ))}
    </div>
  )
}

export default function ExecutiveDashboard() {
  const [period, setPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month')
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  // Sample data - in production this would come from API
  const kpis = {
    nrwRate: 32.4,
    nrwChange: -2.1,
    waterSaved: 45600,
    moneySaved: 892500,
    leaksDetected: 47,
    leaksRepaired: 41,
    avgResponseTime: 4.2,
    systemUptime: 99.7,
    activeSensors: 156,
    fieldCrews: 12,
  }

  const weeklyNRW = [38.2, 36.5, 35.1, 34.8, 33.9, 33.2, 32.4]
  const monthlyRevenue = [720000, 780000, 845000, 892500]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-3 sm:p-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-500 mb-1">
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full font-medium text-[10px] sm:text-xs">LIVE</span>
              <span>{currentTime.toLocaleString('en-GB', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}</span>
            </div>
            <h1 className="text-xl sm:text-3xl font-bold text-slate-900">Executive Dashboard</h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">LWSC Non-Revenue Water Performance Overview</p>
          </div>
          
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Period Selector */}
            <div className="flex bg-white rounded-lg border border-slate-200 p-0.5 sm:p-1">
              {(['week', 'month', 'quarter', 'year'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-2 sm:px-3 py-1 sm:py-1.5 text-[10px] sm:text-xs font-medium rounded-md transition-colors ${
                    period === p 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
            
            {/* Export Button */}
            <button className="flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs sm:text-sm font-medium">
              <Download className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden sm:inline">Export Report</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <KPICard
          title="Current NRW Rate"
          value={kpis.nrwRate}
          unit="%"
          change={kpis.nrwChange}
          changeType="positive"
          icon={Droplets}
          color="blue"
          subtitle="Target: 25%"
        />
        <KPICard
          title="Water Saved"
          value={(kpis.waterSaved / 1000).toFixed(1)}
          unit="ML"
          change={12.5}
          changeType="positive"
          icon={TrendingUp}
          color="cyan"
          subtitle="This month"
        />
        <KPICard
          title="Revenue Recovered"
          value={`K${(kpis.moneySaved / 1000).toFixed(0)}k`}
          change={8.3}
          changeType="positive"
          icon={DollarSign}
          color="green"
          subtitle="From leak repairs"
        />
        <KPICard
          title="Avg Response Time"
          value={kpis.avgResponseTime}
          unit="hrs"
          change={-15}
          changeType="positive"
          icon={Clock}
          color="amber"
          subtitle="To first response"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* NRW Trend */}
        <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-slate-900">NRW Rate Trend</h3>
              <p className="text-[10px] sm:text-xs text-slate-500">Last 7 weeks</p>
            </div>
            <div className="flex items-center gap-2 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-[10px] sm:text-xs font-semibold">
              <TrendingDown className="w-3 h-3" />
              Improving
            </div>
          </div>
          <div className="h-32 sm:h-48 flex items-end justify-between gap-2 sm:gap-3 mb-3">
            {weeklyNRW.map((value, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <div 
                  className={`w-full rounded-t-lg transition-all ${
                    i === weeklyNRW.length - 1 ? 'bg-blue-500' : 'bg-slate-200'
                  }`}
                  style={{ height: `${(value / 45) * 100}%` }}
                />
                <span className="text-[8px] sm:text-[10px] text-slate-400">W{i + 1}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between text-xs sm:text-sm">
            <span className="text-slate-500">Started: {weeklyNRW[0]}%</span>
            <span className="font-semibold text-emerald-600">Now: {weeklyNRW[weeklyNRW.length - 1]}%</span>
          </div>
        </div>

        {/* Revenue Recovery */}
        <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-slate-900">Revenue Recovery</h3>
              <p className="text-[10px] sm:text-xs text-slate-500">Monthly trend (ZMW)</p>
            </div>
            <div className="flex items-center gap-2 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-[10px] sm:text-xs font-semibold">
              <TrendingUp className="w-3 h-3" />
              +24%
            </div>
          </div>
          <div className="h-32 sm:h-48 flex items-end justify-between gap-3 sm:gap-4 mb-3">
            {monthlyRevenue.map((value, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-[9px] sm:text-xs font-semibold text-slate-600">K{(value/1000).toFixed(0)}k</span>
                <div 
                  className={`w-full rounded-t-lg transition-all ${
                    i === monthlyRevenue.length - 1 ? 'bg-emerald-500' : 'bg-emerald-200'
                  }`}
                  style={{ height: `${(value / 1000000) * 100}%` }}
                />
                <span className="text-[8px] sm:text-[10px] text-slate-400">
                  {['Oct', 'Nov', 'Dec', 'Jan'][i]}
                </span>
              </div>
            ))}
          </div>
          <div className="text-center text-xs sm:text-sm text-slate-600">
            Total Recovered: <span className="font-bold text-emerald-600">K3.24M</span>
          </div>
        </div>
      </div>

      {/* Operations Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* Leak Status */}
        <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
          <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Leak Detection Status</h3>
          <div className="space-y-3 sm:space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Detected</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">This month</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-slate-900">{kpis.leaksDetected}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <CheckCircle2 className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Repaired</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">Completed</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-emerald-600">{kpis.leaksRepaired}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-red-100 flex items-center justify-center">
                  <XCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Pending</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">In progress</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-red-600">{kpis.leaksDetected - kpis.leaksRepaired}</span>
            </div>
          </div>
          {/* Progress */}
          <div className="mt-4 pt-4 border-t border-slate-100">
            <div className="flex justify-between text-xs sm:text-sm mb-2">
              <span className="text-slate-500">Repair Rate</span>
              <span className="font-semibold text-slate-900">{Math.round((kpis.leaksRepaired / kpis.leaksDetected) * 100)}%</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${(kpis.leaksRepaired / kpis.leaksDetected) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
          <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">System Health</h3>
          <div className="space-y-3 sm:space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Uptime</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">System availability</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-emerald-600">{kpis.systemUptime}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-cyan-100 flex items-center justify-center">
                  <Target className="w-4 h-4 sm:w-5 sm:h-5 text-cyan-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Active Sensors</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">Connected devices</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-slate-900">{kpis.activeSensors}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Users className="w-4 h-4 sm:w-5 sm:h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-xs sm:text-sm font-medium text-slate-900">Field Crews</p>
                  <p className="text-[10px] sm:text-xs text-slate-500">Active today</p>
                </div>
              </div>
              <span className="text-lg sm:text-2xl font-bold text-slate-900">{kpis.fieldCrews}</span>
            </div>
          </div>
        </div>

        {/* Targets */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-4 sm:p-6 shadow-sm text-white">
          <div className="flex items-center gap-2 mb-4">
            <Award className="w-5 h-5 sm:w-6 sm:h-6" />
            <h3 className="text-sm sm:text-base font-semibold">2026 Targets</h3>
          </div>
          <div className="space-y-3 sm:space-y-4">
            <div>
              <div className="flex justify-between text-xs sm:text-sm mb-1.5">
                <span className="text-blue-100">NRW Reduction</span>
                <span className="font-semibold">32.4% → 25%</span>
              </div>
              <div className="h-2 bg-blue-800/50 rounded-full overflow-hidden">
                <div className="h-full bg-white rounded-full" style={{ width: '65%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs sm:text-sm mb-1.5">
                <span className="text-blue-100">Revenue Recovery</span>
                <span className="font-semibold">K3.2M / K5M</span>
              </div>
              <div className="h-2 bg-blue-800/50 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-400 rounded-full" style={{ width: '64%' }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs sm:text-sm mb-1.5">
                <span className="text-blue-100">Sensor Coverage</span>
                <span className="font-semibold">156 / 200</span>
              </div>
              <div className="h-2 bg-blue-800/50 rounded-full overflow-hidden">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: '78%' }} />
              </div>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-blue-500/30">
            <p className="text-xs sm:text-sm text-blue-100">
              On track to achieve <span className="font-bold text-white">K1.8M</span> additional savings by Q4
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Row - DMA Performance */}
      <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
          <div>
            <h3 className="text-sm sm:text-base font-semibold text-slate-900">DMA Performance Ranking</h3>
            <p className="text-[10px] sm:text-xs text-slate-500">Top and bottom performing areas</p>
          </div>
          <button className="text-xs sm:text-sm text-blue-600 font-medium flex items-center gap-1 hover:underline">
            View All DMAs <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {/* Best Performers */}
          <div>
            <p className="text-xs font-medium text-emerald-600 mb-2 sm:mb-3 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Best Performers
            </p>
            <div className="space-y-2">
              {[
                { name: 'Woodlands', nrw: 18.5, change: -3.2 },
                { name: 'Kabulonga', nrw: 21.2, change: -2.8 },
                { name: 'Roma', nrw: 23.1, change: -1.9 },
              ].map((dma, i) => (
                <div key={i} className="flex items-center justify-between p-2 sm:p-3 bg-emerald-50 rounded-lg">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-emerald-500 text-white text-[10px] sm:text-xs font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="text-xs sm:text-sm font-medium text-slate-900">{dma.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs sm:text-sm font-bold text-slate-900">{dma.nrw}%</span>
                    <span className="text-[10px] sm:text-xs text-emerald-600 ml-2">{dma.change}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Needs Attention */}
          <div>
            <p className="text-xs font-medium text-red-600 mb-2 sm:mb-3 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Needs Attention
            </p>
            <div className="space-y-2">
              {[
                { name: 'Matero', nrw: 48.2, change: +1.5 },
                { name: 'Chilenje', nrw: 45.8, change: +0.8 },
                { name: 'Garden', nrw: 42.1, change: -0.5 },
              ].map((dma, i) => (
                <div key={i} className="flex items-center justify-between p-2 sm:p-3 bg-red-50 rounded-lg">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-red-500 text-white text-[10px] sm:text-xs font-bold flex items-center justify-center">
                      !
                    </span>
                    <span className="text-xs sm:text-sm font-medium text-slate-900">{dma.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs sm:text-sm font-bold text-slate-900">{dma.nrw}%</span>
                    <span className={`text-[10px] sm:text-xs ml-2 ${dma.change > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                      {dma.change > 0 ? '+' : ''}{dma.change}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
