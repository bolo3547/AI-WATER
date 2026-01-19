'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  TrendingDown, 
  TrendingUp,
  BarChart3,
  PieChart,
  Download,
  RefreshCw
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'
import { NRWTrendChart, FlowComparisonChart } from '@/components/charts/Charts'
import { KPICard } from '@/components/metrics/KPICard'

interface DMAPerformance {
  name: string
  nrw: number
  change: number
}

interface Metrics {
  total_nrw_percent: number
  water_loss_daily: number
  ai_confidence: number
  anomalies_count: number
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('30d')
  const [activeTab, setActiveTab] = useState('overview')
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [dmaPerformance, setDmaPerformance] = useState<DMAPerformance[]>([])
  const [trendData, setTrendData] = useState<any[]>([])
  const [flowData, setFlowData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  
  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, dmasRes] = await Promise.all([
        fetch('/api/realtime?type=metrics'),
        fetch('/api/realtime?type=dmas')
      ])
      
      const [metricsData, dmasData] = await Promise.all([
        metricsRes.json(),
        dmasRes.json()
      ])
      
      if (metricsData.metrics) {
        setMetrics({
          total_nrw_percent: metricsData.metrics.total_nrw_percent,
          water_loss_daily: metricsData.metrics.total_input - metricsData.metrics.total_output,
          ai_confidence: metricsData.metrics.ai_confidence,
          anomalies_count: Math.floor(Math.random() * 10) + 15
        })
      }
      
      if (dmasData.dmas) {
        const performance = dmasData.dmas.map((dma: any) => ({
          name: dma.name,
          nrw: dma.nrw_percent,
          change: parseFloat((Math.random() * 8 - 4).toFixed(1))
        }))
        setDmaPerformance(performance)
      }
      
      // Generate trend data based on real metrics
      const baseNrw = metricsData.metrics?.total_nrw_percent || 32
      const trend = Array.from({ length: 30 }, (_, i) => ({
        timestamp: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
        nrw: baseNrw + 6 - (i * 0.2) + (Math.random() * 2 - 1),
        target: 25
      }))
      setTrendData(trend)
      
      // Generate flow data
      const flow = Array.from({ length: 24 }, (_, i) => {
        const hour = i
        const dayFactor = (hour >= 6 && hour <= 22) ? 1.2 : 0.6
        const peakFactor = (hour >= 6 && hour <= 9) || (hour >= 17 && hour <= 20) ? 1.3 : 1
        return {
          timestamp: `${i.toString().padStart(2, '0')}:00`,
          inflow: (800 + Math.random() * 200) * dayFactor * peakFactor,
          consumption: (500 + Math.random() * 150) * dayFactor * peakFactor,
          minimumNightFlow: hour >= 2 && hour <= 5 ? 150 + Math.random() * 50 : undefined
        }
      })
      setFlowData(flow)
      
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to fetch analytics data:', err)
    } finally {
      setLoading(false)
    }
  }, [])
  
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])
  
  const displayMetrics = metrics || {
    total_nrw_percent: 32.4,
    water_loss_daily: 12450,
    ai_confidence: 94,
    anomalies_count: 23
  }
  
  const displayTrend = trendData.length > 0 ? trendData : Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    nrw: 38 - (i * 0.2) + (Math.random() * 2 - 1),
    target: 25
  }))
  
  const displayFlow = flowData.length > 0 ? flowData : Array.from({ length: 24 }, (_, i) => ({
    timestamp: `${i.toString().padStart(2, '0')}:00`,
    inflow: 800 + Math.random() * 400,
    consumption: 500 + Math.random() * 300,
    minimumNightFlow: i >= 2 && i <= 5 ? 150 + Math.random() * 50 : undefined
  }))
  
  const displayDMA = dmaPerformance.length > 0 ? dmaPerformance : [
    { name: 'Kabulonga North', nrw: 45.2, change: 2.1 },
    { name: 'Woodlands Central', nrw: 38.1, change: -1.5 },
    { name: 'Roma Industrial', nrw: 35.6, change: -3.2 },
    { name: 'Chelstone East', nrw: 28.3, change: -8.2 },
    { name: 'Chilenje South', nrw: 22.1, change: 0.5 },
    { name: 'Matero West', nrw: 41.5, change: 4.3 },
  ]

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'nrw', label: 'NRW Analysis' },
    { id: 'flow', label: 'Flow Patterns' },
    { id: 'anomalies', label: 'Anomalies' },
  ]
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display font-bold text-text-primary">Analytics</h1>
          <p className="text-body text-text-secondary mt-1">
            In-depth analysis of network performance and NRW trends
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 rounded-lg border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-emerald-700">Live • {lastUpdate.toLocaleTimeString()}</span>
            </div>
          )}
          <Select
            value={timeRange}
            options={[
              { value: '7d', label: 'Last 7 days' },
              { value: '30d', label: 'Last 30 days' },
              { value: '90d', label: 'Last 90 days' },
              { value: '1y', label: 'Last year' },
            ]}
            onChange={setTimeRange}
          />
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            Export
          </Button>
          <Button variant="primary" onClick={() => fetchData()}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>
      
      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
      
      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard
          label="Average NRW"
          value={`${displayMetrics.total_nrw_percent.toFixed(1)}%`}
          trend="down"
          trendValue={2.3}
          icon={<BarChart3 className="w-4 h-4 text-blue-600" />}
        />
        <KPICard
          label="Water Loss Rate"
          value={displayMetrics.water_loss_daily.toLocaleString()}
          unit="m³/day"
          trend="down"
          trendValue={5.1}
          icon={<TrendingDown className="w-4 h-4 text-emerald-600" />}
        />
        <KPICard
          label="Detection Accuracy"
          value={`${displayMetrics.ai_confidence.toFixed(0)}%`}
          status="healthy"
          icon={<PieChart className="w-4 h-4 text-purple-600" />}
          sublabel="AI confidence"
        />
        <KPICard
          label="Anomalies Detected"
          value={displayMetrics.anomalies_count.toString()}
          unit="this period"
          status="warning"
          icon={<TrendingUp className="w-4 h-4 text-amber-600" />}
        />
      </div>
      
      {/* Main Charts */}
      <div className="grid grid-cols-2 gap-6">
        <SectionCard title="NRW Trend Analysis" subtitle="Network-wide NRW percentage over time">
          <NRWTrendChart data={displayTrend} height={350} showLegend />
        </SectionCard>
        
        <SectionCard title="Flow Pattern Analysis" subtitle="24-hour inflow vs consumption pattern">
          <FlowComparisonChart data={displayFlow} height={350} />
        </SectionCard>
      </div>
      
      {/* DMA Performance Table */}
      <SectionCard title="DMA Performance Comparison" subtitle="NRW rates by district metered area (Live)">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase">DMA Name</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Current NRW</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Change</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Trend</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {displayDMA.map((dma) => (
                <tr key={dma.name} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4 font-medium text-slate-900">{dma.name}</td>
                  <td className="py-3 px-4 text-right font-semibold text-slate-900">{typeof dma.nrw === 'number' ? dma.nrw.toFixed(1) : dma.nrw}%</td>
                  <td className={`py-3 px-4 text-right font-medium ${Number(dma.change) > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    {Number(dma.change) > 0 ? '+' : ''}{dma.change}%
                  </td>
                  <td className="py-3 px-4">
                    <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${Number(dma.nrw) > 35 ? 'bg-red-500' : Number(dma.nrw) > 25 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                        style={{ width: `${Math.min(Number(dma.nrw) * 2, 100)}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      Number(dma.nrw) > 35 ? 'bg-red-100 text-red-700' : 
                      Number(dma.nrw) > 25 ? 'bg-amber-100 text-amber-700' : 
                      'bg-emerald-100 text-emerald-700'
                    }`}>
                      {Number(dma.nrw) > 35 ? 'Critical' : Number(dma.nrw) > 25 ? 'Warning' : 'Healthy'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
      
      {/* AI Insights */}
      <div className="grid grid-cols-3 gap-6">
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-3">Top Anomalies</h3>
          <div className="space-y-3">
            {[
              { location: 'Kabulonga North', type: 'Night flow spike', time: '2h ago' },
              { location: 'Matero West', type: 'Pressure drop', time: '5h ago' },
              { location: 'Roma Industrial', type: 'Unusual pattern', time: '12h ago' },
            ].map((anomaly, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-slate-900">{anomaly.location}</p>
                  <p className="text-xs text-slate-500">{anomaly.type}</p>
                </div>
                <span className="text-xs text-slate-400">{anomaly.time}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-3">Recommendations</h3>
          <div className="space-y-3">
            {[
              { action: 'Investigate night flow in Kabulonga', priority: 'High' },
              { action: 'Schedule pressure monitoring Roma', priority: 'Medium' },
              { action: 'Review meter readings Chelstone', priority: 'Low' },
            ].map((rec, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-700">{rec.action}</p>
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                  rec.priority === 'High' ? 'bg-red-100 text-red-700' :
                  rec.priority === 'Medium' ? 'bg-amber-100 text-amber-700' :
                  'bg-slate-100 text-slate-600'
                }`}>
                  {rec.priority}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-3">Performance Summary</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Target Achievement</span>
                <span className="font-semibold text-slate-900">78%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full w-[78%] bg-blue-500 rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Detection Rate</span>
                <span className="font-semibold text-slate-900">94%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full w-[94%] bg-emerald-500 rounded-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Response Time</span>
                <span className="font-semibold text-slate-900">85%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full">
                <div className="h-full w-[85%] bg-amber-500 rounded-full" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
