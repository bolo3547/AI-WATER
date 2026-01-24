'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  Droplets, TrendingUp, TrendingDown, Users, AlertTriangle, CheckCircle,
  Clock, Target, BarChart3, PieChart, Download, Calendar, RefreshCw,
  ArrowUpRight, ArrowDownRight, MapPin, Zap, Brain, Award, FileText,
  Phone, Globe, MessageCircle, Filter
} from 'lucide-react'

// Types
interface AnalyticsMetrics {
  totalReports: number
  totalReportsChange: number
  confirmedReports: number
  confirmedRate: number
  falseReports: number
  falseRate: number
  avgResponseTimeHours: number
  avgResponseTimeChange: number
  avgResolutionTimeHours: number
  avgResolutionTimeChange: number
  workOrdersCreated: number
  workOrdersCreatedChange: number
  leaksLinked: number
  leaksLinkedChange: number
  uniqueReporters: number
  topAreas: Array<{ name: string; count: number }>
  byCategory: Record<string, number>
  bySource: Record<string, number>
  byStatus: Record<string, number>
  monthlyTrend: Array<{ month: string; reports: number; confirmed: number }>
}

// Mock data generator
const generateMockMetrics = (): AnalyticsMetrics => ({
  totalReports: 1284,
  totalReportsChange: 12.5,
  confirmedReports: 847,
  confirmedRate: 65.9,
  falseReports: 156,
  falseRate: 12.1,
  avgResponseTimeHours: 4.2,
  avgResponseTimeChange: -8.3,
  avgResolutionTimeHours: 18.6,
  avgResolutionTimeChange: -15.2,
  workOrdersCreated: 623,
  workOrdersCreatedChange: 28.4,
  leaksLinked: 312,
  leaksLinkedChange: 45.2,
  uniqueReporters: 956,
  topAreas: [
    { name: 'Central Business District', count: 187 },
    { name: 'Kabulonga', count: 156 },
    { name: 'Chilenje South', count: 142 },
    { name: 'Matero', count: 128 },
    { name: 'Garden Compound', count: 98 },
    { name: 'Kamwala', count: 87 },
    { name: 'Kalingalinga', count: 76 },
    { name: 'Woodlands', count: 65 },
  ],
  byCategory: {
    leak: 524,
    burst: 187,
    no_water: 213,
    low_pressure: 156,
    illegal_connection: 89,
    overflow: 67,
    contamination: 32,
    other: 16,
  },
  bySource: {
    web: 567,
    whatsapp: 423,
    ussd: 189,
    mobile_app: 78,
    call_center: 27,
  },
  byStatus: {
    received: 145,
    under_review: 89,
    technician_assigned: 67,
    in_progress: 156,
    resolved: 712,
    closed: 115,
  },
  monthlyTrend: [
    { month: 'Jul', reports: 89, confirmed: 52 },
    { month: 'Aug', reports: 102, confirmed: 68 },
    { month: 'Sep', reports: 118, confirmed: 78 },
    { month: 'Oct', reports: 134, confirmed: 92 },
    { month: 'Nov', reports: 156, confirmed: 108 },
    { month: 'Dec', reports: 167, confirmed: 118 },
    { month: 'Jan', reports: 178, confirmed: 121 },
    { month: 'Feb', reports: 189, confirmed: 132 },
    { month: 'Mar', reports: 156, confirmed: 98 },
  ],
})

const CATEGORY_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  leak: { label: 'Leak', color: 'bg-blue-500', icon: '💧' },
  burst: { label: 'Burst Pipe', color: 'bg-red-500', icon: '💦' },
  no_water: { label: 'No Water', color: 'bg-slate-500', icon: '🚫' },
  low_pressure: { label: 'Low Pressure', color: 'bg-amber-500', icon: '📉' },
  illegal_connection: { label: 'Illegal Conn.', color: 'bg-purple-500', icon: '⚠️' },
  overflow: { label: 'Overflow', color: 'bg-cyan-500', icon: '🌊' },
  contamination: { label: 'Contamination', color: 'bg-emerald-500', icon: '☣️' },
  other: { label: 'Other', color: 'bg-slate-400', icon: '❓' },
}

const SOURCE_LABELS: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  web: { label: 'Web Portal', color: 'bg-blue-500', icon: <Globe className="w-4 h-4" /> },
  whatsapp: { label: 'WhatsApp', color: 'bg-emerald-500', icon: <MessageCircle className="w-4 h-4" /> },
  ussd: { label: 'USSD', color: 'bg-amber-500', icon: <Phone className="w-4 h-4" /> },
  mobile_app: { label: 'Mobile App', color: 'bg-purple-500', icon: <Zap className="w-4 h-4" /> },
  call_center: { label: 'Call Center', color: 'bg-slate-500', icon: <Phone className="w-4 h-4" /> },
}

// Simple bar chart component
function BarChart({ data, maxValue, labelKey, valueKey, colorFn }: {
  data: Array<Record<string, any>>
  maxValue: number
  labelKey: string
  valueKey: string
  colorFn?: (item: Record<string, any>) => string
}) {
  return (
    <div className="space-y-2">
      {data.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-sm text-slate-400 w-24 truncate">{item[labelKey]}</span>
          <div className="flex-1 h-6 bg-slate-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${colorFn ? colorFn(item) : 'bg-blue-500'}`}
              style={{ width: `${(item[valueKey] / maxValue) * 100}%` }}
            />
          </div>
          <span className="text-sm text-slate-300 w-12 text-right">{item[valueKey]}</span>
        </div>
      ))}
    </div>
  )
}

// Trend chart component
function TrendChart({ data }: { data: Array<{ month: string; reports: number; confirmed: number }> }) {
  const maxValue = Math.max(...data.map(d => d.reports))
  
  return (
    <div className="flex items-end gap-2 h-48">
      {data.map((item, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col items-center gap-0.5">
            <div
              className="w-full bg-blue-500/30 rounded-t"
              style={{ height: `${(item.reports / maxValue) * 150}px` }}
            >
              <div
                className="w-full bg-blue-500 rounded-t"
                style={{ height: `${(item.confirmed / item.reports) * 100}%` }}
              />
            </div>
          </div>
          <span className="text-xs text-slate-500">{item.month}</span>
        </div>
      ))}
    </div>
  )
}

export default function PublicAnalyticsPage() {
  const params = useParams()
  const tenantId = params.tenant as string || 'lwsc-zambia'

  const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30d')
  const [isExporting, setIsExporting] = useState(false)

  // Load metrics
  useEffect(() => {
    setIsLoading(true)
    setTimeout(() => {
      setMetrics(generateMockMetrics())
      setIsLoading(false)
    }, 500)
  }, [dateRange])

  // Calculate totals
  const categoryTotal = metrics ? Object.values(metrics.byCategory).reduce((a, b) => a + b, 0) : 0
  const sourceTotal = metrics ? Object.values(metrics.bySource).reduce((a, b) => a + b, 0) : 0

  // Export handler
  const handleExport = async () => {
    setIsExporting(true)
    // Simulate export
    setTimeout(() => {
      setIsExporting(false)
      alert('CSV exported successfully!')
    }, 1500)
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-40">
        <div className="max-w-[1800px] mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <BarChart3 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-100">Public Engagement Analytics</h1>
                <p className="text-sm text-slate-400">Community reporting KPIs & trends</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Date range selector */}
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="365d">Last year</option>
                <option value="all">All time</option>
              </select>

              <button
                onClick={handleExport}
                disabled={isExporting}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
              >
                {isExporting ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-4 py-6">
        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center h-96">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-400" />
          </div>
        )}

        {/* Metrics */}
        {!isLoading && metrics && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
              {/* Total Reports */}
              <div className="col-span-2 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">Total Reports</p>
                  <Droplets className="w-5 h-5 text-blue-400" />
                </div>
                <p className="text-3xl font-bold text-slate-100">{metrics.totalReports.toLocaleString()}</p>
                <div className="flex items-center gap-1 mt-1">
                  {metrics.totalReportsChange >= 0 ? (
                    <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4 text-red-400" />
                  )}
                  <span className={`text-sm ${metrics.totalReportsChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {Math.abs(metrics.totalReportsChange)}% vs prev. period
                  </span>
                </div>
              </div>

              {/* Confirmed Rate */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">Confirmed</p>
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <p className="text-2xl font-bold text-emerald-400">{metrics.confirmedRate}%</p>
                <p className="text-xs text-slate-500 mt-1">{metrics.confirmedReports} reports</p>
              </div>

              {/* False Rate */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">False Reports</p>
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
                <p className="text-2xl font-bold text-red-400">{metrics.falseRate}%</p>
                <p className="text-xs text-slate-500 mt-1">{metrics.falseReports} reports</p>
              </div>

              {/* Avg Response Time */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">Response Time</p>
                  <Clock className="w-5 h-5 text-amber-400" />
                </div>
                <p className="text-2xl font-bold text-slate-100">{metrics.avgResponseTimeHours}h</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">{Math.abs(metrics.avgResponseTimeChange)}%</span>
                </div>
              </div>

              {/* Avg Resolution Time */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">Resolution Time</p>
                  <Target className="w-5 h-5 text-purple-400" />
                </div>
                <p className="text-2xl font-bold text-slate-100">{metrics.avgResolutionTimeHours}h</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">{Math.abs(metrics.avgResolutionTimeChange)}%</span>
                </div>
              </div>

              {/* Work Orders */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">Work Orders</p>
                  <FileText className="w-5 h-5 text-blue-400" />
                </div>
                <p className="text-2xl font-bold text-blue-400">{metrics.workOrdersCreated}</p>
                <div className="flex items-center gap-1 mt-1">
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">{metrics.workOrdersCreatedChange}%</span>
                </div>
              </div>

              {/* AI Leaks Linked */}
              <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">AI Links</p>
                  <Brain className="w-5 h-5 text-emerald-400" />
                </div>
                <p className="text-2xl font-bold text-emerald-400">{metrics.leaksLinked}</p>
                <div className="flex items-center gap-1 mt-1">
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">{metrics.leaksLinkedChange}%</span>
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid lg:grid-cols-2 gap-6 mb-6">
              {/* Monthly Trend */}
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="font-semibold text-slate-100">Monthly Report Trend</h3>
                    <p className="text-sm text-slate-400">Reports received vs confirmed</p>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-blue-500/30" />
                      <span className="text-slate-400">Total</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-blue-500" />
                      <span className="text-slate-400">Confirmed</span>
                    </div>
                  </div>
                </div>
                <TrendChart data={metrics.monthlyTrend} />
              </div>

              {/* By Category */}
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="font-semibold text-slate-100">Reports by Category</h3>
                    <p className="text-sm text-slate-400">Distribution of issue types</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {Object.entries(metrics.byCategory)
                    .sort(([, a], [, b]) => b - a)
                    .map(([category, count]) => (
                      <div key={category} className="flex items-center gap-3">
                        <span className="text-xl w-8">{CATEGORY_LABELS[category]?.icon || '❓'}</span>
                        <span className="text-sm text-slate-300 w-28 truncate">
                          {CATEGORY_LABELS[category]?.label || category}
                        </span>
                        <div className="flex-1 h-6 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${CATEGORY_LABELS[category]?.color || 'bg-slate-500'}`}
                            style={{ width: `${(count / Math.max(...Object.values(metrics.byCategory))) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-300 w-16 text-right">{count}</span>
                        <span className="text-xs text-slate-500 w-12 text-right">
                          {((count / categoryTotal) * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* Second Row */}
            <div className="grid lg:grid-cols-3 gap-6 mb-6">
              {/* By Source */}
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-slate-100">Reports by Channel</h3>
                  <p className="text-sm text-slate-400">How reports are submitted</p>
                </div>
                <div className="space-y-4">
                  {Object.entries(metrics.bySource)
                    .sort(([, a], [, b]) => b - a)
                    .map(([source, count]) => {
                      const pct = (count / sourceTotal) * 100
                      return (
                        <div key={source} className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${SOURCE_LABELS[source]?.color}/20`}>
                            {SOURCE_LABELS[source]?.icon}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="text-sm text-slate-200">
                                {SOURCE_LABELS[source]?.label || source}
                              </span>
                              <span className="text-sm text-slate-400">{count}</span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${SOURCE_LABELS[source]?.color || 'bg-slate-500'}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                          <span className="text-xs text-slate-500 w-12">{pct.toFixed(1)}%</span>
                        </div>
                      )
                    })}
                </div>
              </div>

              {/* Top Areas */}
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-slate-100">Top Reporting Areas</h3>
                  <p className="text-sm text-slate-400">Hotspots by location</p>
                </div>
                <div className="space-y-3">
                  {metrics.topAreas.slice(0, 8).map((area, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-slate-500 w-5">{i + 1}.</span>
                      <MapPin className="w-4 h-4 text-blue-400" />
                      <span className="text-sm text-slate-200 flex-1 truncate">{area.name}</span>
                      <span className="text-sm text-slate-400">{area.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status Distribution */}
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-slate-100">Current Status</h3>
                  <p className="text-sm text-slate-400">Report pipeline status</p>
                </div>
                <div className="space-y-3">
                  {Object.entries(metrics.byStatus).map(([status, count]) => {
                    const colors: Record<string, string> = {
                      received: 'bg-slate-500',
                      under_review: 'bg-blue-500',
                      technician_assigned: 'bg-amber-500',
                      in_progress: 'bg-purple-500',
                      resolved: 'bg-emerald-500',
                      closed: 'bg-slate-400',
                    }
                    return (
                      <div key={status} className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${colors[status]}`} />
                        <span className="text-sm text-slate-300 flex-1 capitalize">
                          {status.replace('_', ' ')}
                        </span>
                        <span className="text-sm text-slate-400">{count}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6">
              <div className="mb-6">
                <h3 className="font-semibold text-slate-100">Performance Summary</h3>
                <p className="text-sm text-slate-400">Key operational metrics for management</p>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-emerald-500/20 rounded-lg">
                      <Award className="w-5 h-5 text-emerald-400" />
                    </div>
                    <span className="text-sm text-slate-400">Confirmation Rate</span>
                  </div>
                  <p className="text-3xl font-bold text-emerald-400">{metrics.confirmedRate}%</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Target: 70% | {metrics.confirmedRate >= 70 ? '✓ On track' : '⚠ Below target'}
                  </p>
                </div>

                <div className="p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <Clock className="w-5 h-5 text-blue-400" />
                    </div>
                    <span className="text-sm text-slate-400">First Response SLA</span>
                  </div>
                  <p className="text-3xl font-bold text-blue-400">{metrics.avgResponseTimeHours}h</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Target: 6h | {metrics.avgResponseTimeHours <= 6 ? '✓ Meeting SLA' : '⚠ Exceeds SLA'}
                  </p>
                </div>

                <div className="p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                      <Target className="w-5 h-5 text-purple-400" />
                    </div>
                    <span className="text-sm text-slate-400">Resolution Rate</span>
                  </div>
                  <p className="text-3xl font-bold text-purple-400">
                    {((metrics.byStatus.resolved / metrics.totalReports) * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500 mt-1">{metrics.byStatus.resolved} resolved</p>
                </div>

                <div className="p-4 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-amber-500/20 rounded-lg">
                      <Users className="w-5 h-5 text-amber-400" />
                    </div>
                    <span className="text-sm text-slate-400">Unique Reporters</span>
                  </div>
                  <p className="text-3xl font-bold text-amber-400">{metrics.uniqueReporters}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {(metrics.totalReports / metrics.uniqueReporters).toFixed(1)} reports/user avg
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
