'use client'

import { useState, useEffect } from 'react'
import { 
  DollarSign, TrendingUp, TrendingDown, BarChart3, 
  PieChart, Target, AlertTriangle, CheckCircle,
  Calendar, Download, RefreshCw, ArrowUp, ArrowDown,
  Wallet, CreditCard, Receipt, Banknote, Clock,
  Users, Building, Factory, Droplets, Zap
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface RevenueData {
  month: string
  billed: number
  collected: number
  nrwLoss: number
  recovered: number
}

interface PredictionData {
  category: string
  currentLoss: number
  predictedRecovery: number
  investmentNeeded: number
  roi: number
  timeToRecovery: number
}

interface CustomerSegment {
  type: string
  count: number
  revenue: number
  nrwImpact: number
  collectionRate: number
}

export default function FinancePage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [revenueData, setRevenueData] = useState<RevenueData[]>([])
  const [predictions, setPredictions] = useState<PredictionData[]>([])
  const [segments, setSegments] = useState<CustomerSegment[]>([])
  const [timeRange, setTimeRange] = useState('12')
  const [currency] = useState('ZMW')

  useEffect(() => {
    loadData()
  }, [timeRange])

  const loadData = () => {
    setRevenueData([
      { month: 'Jan', billed: 12500000, collected: 10625000, nrwLoss: 3750000, recovered: 450000 },
      { month: 'Feb', billed: 13200000, collected: 11220000, nrwLoss: 3960000, recovered: 520000 },
      { month: 'Mar', billed: 13800000, collected: 12006000, nrwLoss: 4140000, recovered: 680000 },
      { month: 'Apr', billed: 14100000, collected: 12408000, nrwLoss: 4230000, recovered: 750000 },
      { month: 'May', billed: 14500000, collected: 13050000, nrwLoss: 4350000, recovered: 890000 },
      { month: 'Jun', billed: 15200000, collected: 13832000, nrwLoss: 4560000, recovered: 1020000 }
    ])

    setPredictions([
      {
        category: 'Physical Losses (Leaks)',
        currentLoss: 28000000,
        predictedRecovery: 19600000,
        investmentNeeded: 8500000,
        roi: 230,
        timeToRecovery: 18
      },
      {
        category: 'Commercial Losses (Theft)',
        currentLoss: 12000000,
        predictedRecovery: 9600000,
        investmentNeeded: 2800000,
        roi: 343,
        timeToRecovery: 12
      },
      {
        category: 'Meter Inaccuracy',
        currentLoss: 8500000,
        predictedRecovery: 6800000,
        investmentNeeded: 4200000,
        roi: 162,
        timeToRecovery: 24
      },
      {
        category: 'Unbilled Connections',
        currentLoss: 6200000,
        predictedRecovery: 5580000,
        investmentNeeded: 1500000,
        roi: 372,
        timeToRecovery: 8
      }
    ])

    setSegments([
      { type: 'Residential', count: 185000, revenue: 95000000, nrwImpact: 38, collectionRate: 82 },
      { type: 'Commercial', count: 12500, revenue: 45000000, nrwImpact: 22, collectionRate: 91 },
      { type: 'Industrial', count: 850, revenue: 28000000, nrwImpact: 15, collectionRate: 95 },
      { type: 'Government', count: 420, revenue: 18000000, nrwImpact: 12, collectionRate: 68 },
      { type: 'Institutional', count: 680, revenue: 12000000, nrwImpact: 8, collectionRate: 78 }
    ])
  }

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `K${(amount / 1000000).toFixed(1)}M`
    } else if (amount >= 1000) {
      return `K${(amount / 1000).toFixed(0)}K`
    }
    return `K${amount.toLocaleString()}`
  }

  const totalBilled = revenueData.reduce((sum, d) => sum + d.billed, 0)
  const totalCollected = revenueData.reduce((sum, d) => sum + d.collected, 0)
  const totalNRWLoss = revenueData.reduce((sum, d) => sum + d.nrwLoss, 0)
  const totalRecovered = revenueData.reduce((sum, d) => sum + d.recovered, 0)
  const collectionRate = Math.round((totalCollected / totalBilled) * 100)
  const predictedAnnualRecovery = predictions.reduce((sum, p) => sum + p.predictedRecovery, 0)
  const totalInvestment = predictions.reduce((sum, p) => sum + p.investmentNeeded, 0)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <DollarSign className="w-6 h-6 sm:w-7 sm:h-7 text-green-600" />
            Revenue Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            AI-powered revenue recovery and financial forecasting
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={timeRange}
            options={[
              { value: '6', label: 'Last 6 Months' },
              { value: '12', label: 'Last 12 Months' },
              { value: '24', label: 'Last 2 Years' }
            ]}
            onChange={setTimeRange}
          />
          <Button variant="secondary">
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Wallet className="w-8 h-8 opacity-80" />
            <span className="flex items-center gap-1 text-green-200 text-xs">
              <ArrowUp className="w-3 h-3" /> 8.2%
            </span>
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(totalBilled)}</p>
          <p className="text-green-200 text-xs sm:text-sm">Total Billed (6M)</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <CreditCard className="w-8 h-8 opacity-80" />
            <span className="text-blue-200 text-xs">{collectionRate}%</span>
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(totalCollected)}</p>
          <p className="text-blue-200 text-xs sm:text-sm">Collected</p>
        </div>
        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <AlertTriangle className="w-8 h-8 opacity-80" />
            <span className="flex items-center gap-1 text-red-200 text-xs">
              <ArrowDown className="w-3 h-3" /> 3.1%
            </span>
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(totalNRWLoss)}</p>
          <p className="text-red-200 text-xs sm:text-sm">NRW Loss</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Target className="w-8 h-8 opacity-80" />
            <span className="flex items-center gap-1 text-purple-200 text-xs">
              <ArrowUp className="w-3 h-3" /> 127%
            </span>
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(totalRecovered)}</p>
          <p className="text-purple-200 text-xs sm:text-sm">Recovered</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'predictions', label: 'AI Predictions' },
          { id: 'segments', label: 'Customer Segments' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Revenue Trend Chart */}
          <SectionCard title="Revenue Trend" subtitle="Monthly billed vs collected">
            <div className="h-64 flex items-end gap-2 px-2">
              {revenueData.map((data, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex gap-0.5 h-48">
                    <div className="flex-1 bg-slate-100 rounded-t relative overflow-hidden">
                      <div 
                        className="absolute bottom-0 w-full bg-green-500 rounded-t"
                        style={{ height: `${(data.billed / 16000000) * 100}%` }}
                      />
                    </div>
                    <div className="flex-1 bg-slate-100 rounded-t relative overflow-hidden">
                      <div 
                        className="absolute bottom-0 w-full bg-blue-500 rounded-t"
                        style={{ height: `${(data.collected / 16000000) * 100}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">{data.month}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-center gap-6 mt-4 text-sm">
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 bg-green-500 rounded" />
                Billed
              </span>
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 bg-blue-500 rounded" />
                Collected
              </span>
            </div>
          </SectionCard>

          {/* NRW Loss Breakdown */}
          <SectionCard title="NRW Financial Impact" subtitle="Revenue lost to non-revenue water">
            <div className="space-y-4">
              {[
                { label: 'Physical Losses', amount: 28000000, percent: 52, color: 'bg-red-500' },
                { label: 'Commercial Losses', amount: 12000000, percent: 22, color: 'bg-orange-500' },
                { label: 'Meter Inaccuracy', amount: 8500000, percent: 16, color: 'bg-yellow-500' },
                { label: 'Unbilled Connections', amount: 6200000, percent: 11, color: 'bg-blue-500' }
              ].map((item, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-700">{item.label}</span>
                    <span className="text-sm font-semibold text-slate-900">{formatCurrency(item.amount)}</span>
                  </div>
                  <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${item.color} rounded-full`}
                      style={{ width: `${item.percent}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{item.percent}% of total NRW loss</p>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Recovery Progress */}
          <SectionCard title="Recovery Progress" subtitle="Month-over-month recovery trends">
            <div className="h-48 flex items-end gap-4 px-2">
              {revenueData.map((data, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center">
                  <div 
                    className="w-full bg-gradient-to-t from-purple-600 to-purple-400 rounded-t"
                    style={{ height: `${(data.recovered / 1200000) * 100}%` }}
                  />
                  <span className="text-xs text-slate-500 mt-1">{data.month}</span>
                  <span className="text-xs font-semibold text-purple-600">{formatCurrency(data.recovered)}</span>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* Collection Rate */}
          <SectionCard title="Collection Performance" subtitle="Bill collection efficiency">
            <div className="flex items-center justify-center py-8">
              <div className="relative w-48 h-48">
                <svg className="w-48 h-48 -rotate-90">
                  <circle
                    cx="96" cy="96" r="80"
                    stroke="#e2e8f0" strokeWidth="16" fill="none"
                  />
                  <circle
                    cx="96" cy="96" r="80"
                    stroke="url(#gradient)" strokeWidth="16" fill="none"
                    strokeDasharray={`${collectionRate * 5.02} 502`}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-4xl font-bold text-slate-900">{collectionRate}%</span>
                  <span className="text-sm text-slate-500">Collection Rate</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center p-3 bg-green-50 rounded-xl">
                <p className="text-2xl font-bold text-green-600">{formatCurrency(totalCollected)}</p>
                <p className="text-xs text-green-700">Collected</p>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-xl">
                <p className="text-2xl font-bold text-red-600">{formatCurrency(totalBilled - totalCollected)}</p>
                <p className="text-xs text-red-700">Outstanding</p>
              </div>
            </div>
          </SectionCard>
        </div>
      )}

      {activeTab === 'predictions' && (
        <div className="space-y-4">
          {/* AI Prediction Summary */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-4 sm:p-6 text-white">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  AI Revenue Recovery Forecast
                </h3>
                <p className="text-indigo-200 text-sm mt-1">
                  Based on current NRW reduction initiatives
                </p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-green-300">
                    {formatCurrency(predictedAnnualRecovery)}
                  </p>
                  <p className="text-xs text-indigo-200">Annual Recovery</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-yellow-300">
                    {formatCurrency(totalInvestment)}
                  </p>
                  <p className="text-xs text-indigo-200">Investment Needed</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-cyan-300">
                    {Math.round((predictedAnnualRecovery / totalInvestment) * 100)}%
                  </p>
                  <p className="text-xs text-indigo-200">Avg ROI</p>
                </div>
              </div>
            </div>
          </div>

          {/* Prediction Details */}
          <SectionCard title="Recovery Opportunities" subtitle="AI-identified revenue recovery potential" noPadding>
            <div className="divide-y divide-slate-100">
              {predictions.map((pred, idx) => (
                <div key={idx} className="p-4 hover:bg-slate-50">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-900">{pred.category}</h4>
                      <div className="flex flex-wrap items-center gap-4 mt-2 text-sm">
                        <span className="text-red-600">
                          Loss: {formatCurrency(pred.currentLoss)}/yr
                        </span>
                        <span className="text-green-600">
                          Recoverable: {formatCurrency(pred.predictedRecovery)}/yr
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="bg-slate-50 rounded-lg p-2">
                        <p className="text-lg font-bold text-slate-900">{formatCurrency(pred.investmentNeeded)}</p>
                        <p className="text-xs text-slate-500">Investment</p>
                      </div>
                      <div className="bg-green-50 rounded-lg p-2">
                        <p className="text-lg font-bold text-green-600">{pred.roi}%</p>
                        <p className="text-xs text-slate-500">ROI</p>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-2">
                        <p className="text-lg font-bold text-blue-600">{pred.timeToRecovery}</p>
                        <p className="text-xs text-slate-500">Months</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-500">Recovery Progress</span>
                      <span className="font-semibold">{Math.round((pred.predictedRecovery / pred.currentLoss) * 100)}%</span>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"
                        style={{ width: `${(pred.predictedRecovery / pred.currentLoss) * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      )}

      {activeTab === 'segments' && (
        <div className="space-y-4">
          {/* Segment Overview */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {segments.map((seg, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
                <div className="flex items-center gap-2 mb-2">
                  {seg.type === 'Residential' && <Users className="w-5 h-5 text-blue-600" />}
                  {seg.type === 'Commercial' && <Building className="w-5 h-5 text-green-600" />}
                  {seg.type === 'Industrial' && <Factory className="w-5 h-5 text-orange-600" />}
                  {seg.type === 'Government' && <Building className="w-5 h-5 text-purple-600" />}
                  {seg.type === 'Institutional' && <Building className="w-5 h-5 text-cyan-600" />}
                  <span className="text-sm font-medium text-slate-900">{seg.type}</span>
                </div>
                <p className="text-xl font-bold text-slate-900">{seg.count.toLocaleString()}</p>
                <p className="text-xs text-slate-500">Customers</p>
              </div>
            ))}
          </div>

          {/* Detailed Segment Analysis */}
          <SectionCard title="Segment Performance" subtitle="Revenue and NRW impact by customer type" noPadding>
            <div className="divide-y divide-slate-100">
              {segments.map((seg, idx) => (
                <div key={idx} className="p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        seg.type === 'Residential' ? 'bg-blue-100' :
                        seg.type === 'Commercial' ? 'bg-green-100' :
                        seg.type === 'Industrial' ? 'bg-orange-100' :
                        seg.type === 'Government' ? 'bg-purple-100' : 'bg-cyan-100'
                      }`}>
                        {seg.type === 'Residential' && <Users className="w-6 h-6 text-blue-600" />}
                        {seg.type === 'Commercial' && <Building className="w-6 h-6 text-green-600" />}
                        {seg.type === 'Industrial' && <Factory className="w-6 h-6 text-orange-600" />}
                        {seg.type === 'Government' && <Building className="w-6 h-6 text-purple-600" />}
                        {seg.type === 'Institutional' && <Building className="w-6 h-6 text-cyan-600" />}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{seg.type}</p>
                        <p className="text-sm text-slate-500">{seg.count.toLocaleString()} customers</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <p className="text-lg font-bold text-slate-900">{formatCurrency(seg.revenue)}</p>
                        <p className="text-xs text-slate-500">Annual Revenue</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-red-600">{seg.nrwImpact}%</p>
                        <p className="text-xs text-slate-500">NRW Impact</p>
                      </div>
                      <div className="text-center">
                        <p className={`text-lg font-bold ${seg.collectionRate >= 90 ? 'text-green-600' : seg.collectionRate >= 75 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {seg.collectionRate}%
                        </p>
                        <p className="text-xs text-slate-500">Collection</p>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-500">NRW Impact</span>
                        <span>{seg.nrwImpact}%</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-red-500 rounded-full" style={{ width: `${seg.nrwImpact}%` }} />
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-slate-500">Collection Rate</span>
                        <span>{seg.collectionRate}%</span>
                      </div>
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-green-500 rounded-full" style={{ width: `${seg.collectionRate}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  )
}
