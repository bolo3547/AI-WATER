'use client'

import { useState, useEffect } from 'react'
import { 
  DollarSign, TrendingUp, TrendingDown, BarChart3, 
  PieChart, Target, AlertTriangle, CheckCircle,
  Calendar, Download, RefreshCw, ArrowUp, ArrowDown,
  Wallet, CreditCard, Receipt, Banknote, Clock,
  Users, Building, Factory, Droplets, Zap, Info,
  AlertCircle, MapPin
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface RevenueData {
  date: string
  amount: number
  paymentCount: number
}

interface FinanceSummary {
  totalCollected: number
  totalBilled: number
  collectionRate: number
  paymentCount: number
  todayPayments: number
  averagePayment: number
  byMethod: Record<string, { count: number; total: number }>
  byDMA: Record<string, { count: number; total: number }>
}

interface RecentPayment {
  id: string
  accountNumber: string
  customerName: string
  amount: number
  method: string
  timestamp: string
  dma: string
}

export default function FinancePage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [revenueData, setRevenueData] = useState<RevenueData[]>([])
  const [summary, setSummary] = useState<FinanceSummary>({
    totalCollected: 0,
    totalBilled: 0,
    collectionRate: 0,
    paymentCount: 0,
    todayPayments: 0,
    averagePayment: 0,
    byMethod: {},
    byDMA: {}
  })
  const [recentPayments, setRecentPayments] = useState<RecentPayment[]>([])
  const [timeRange, setTimeRange] = useState('6')
  const [isLoading, setIsLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState('')

  useEffect(() => {
    loadData()
    // Refresh every 30 seconds to catch new payments
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [timeRange])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/finance?months=${timeRange}`)
      if (!response.ok) {
        throw new Error('API not available')
      }
      const data = await response.json()
      
      if (data.totals) {
        setSummary(data.totals)
      }
      if (data.revenueData) {
        setRevenueData(data.revenueData)
      }
      if (data.recentPayments) {
        setRecentPayments(data.recentPayments)
      }
      if (data.message) {
        setStatusMessage(data.message)
      }
    } catch (error) {
      console.error('Failed to load finance data:', error)
      // Keep default zero values - system starts fresh
      setStatusMessage('No payments received yet. Data will appear once payments are made.')
    } finally {
      setIsLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    if (amount === 0) return 'K0'
    if (amount >= 1000000) {
      return `K${(amount / 1000000).toFixed(1)}M`
    } else if (amount >= 1000) {
      return `K${(amount / 1000).toFixed(0)}K`
    }
    return `K${amount.toLocaleString()}`
  }

  // paymentCount used for conditional rendering

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
            Real-time payment tracking and financial analytics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={timeRange}
            options={[
              { value: '3', label: 'Last 3 Months' },
              { value: '6', label: 'Last 6 Months' },
              { value: '12', label: 'Last 12 Months' }
            ]}
            onChange={setTimeRange}
          />
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Status Message */}
      {summary.paymentCount === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-900">No Payments Recorded Yet</p>
            <p className="text-sm text-blue-700 mt-1">
              Revenue data will appear here once customers start making payments. 
              The system is ready to track all incoming payments in real-time.
            </p>
          </div>
        </div>
      )}

      {/* Key Metrics - Real Data from API */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Wallet className="w-8 h-8 opacity-80" />
            {summary.paymentCount > 0 && (
              <span className="flex items-center gap-1 text-green-200 text-xs">
                <ArrowUp className="w-3 h-3" /> New
              </span>
            )}
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(summary.totalCollected)}</p>
          <p className="text-green-200 text-xs sm:text-sm">Total Collected</p>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <CreditCard className="w-8 h-8 opacity-80" />
            <span className="text-blue-200 text-xs">{summary.paymentCount} payments</span>
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{summary.paymentCount}</p>
          <p className="text-blue-200 text-xs sm:text-sm">Transactions</p>
        </div>
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <Target className="w-8 h-8 opacity-80" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{formatCurrency(summary.averagePayment)}</p>
          <p className="text-purple-200 text-xs sm:text-sm">Avg Payment</p>
        </div>
        <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-xl p-4 text-white">
          <div className="flex items-center justify-between">
            <TrendingUp className="w-8 h-8 opacity-80" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold mt-2">{summary.todayPayments}</p>
          <p className="text-cyan-200 text-xs sm:text-sm">Today's Payments</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'payments', label: 'Recent Payments' },
          { id: 'analytics', label: 'Analytics' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Revenue Collection Chart */}
          <SectionCard title="Revenue Collection" subtitle="Daily collection trend">
            {revenueData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <Wallet className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No payment data yet</p>
                  <p className="text-sm">Chart will appear once payments are recorded</p>
                </div>
              </div>
            ) : (
              <>
                <div className="h-64 flex items-end gap-2 px-2">
                  {revenueData.slice(-7).map((data, idx) => {
                    const maxAmount = Math.max(...revenueData.map(d => d.amount), 1)
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <div className="w-full bg-slate-100 rounded-t relative overflow-hidden h-48">
                          <div 
                            className="absolute bottom-0 w-full bg-green-500 rounded-t"
                            style={{ height: `${(data.amount / maxAmount) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">{data.date}</span>
                        <span className="text-xs font-semibold text-green-600">{formatCurrency(data.amount)}</span>
                      </div>
                    )
                  })}
                </div>
                <div className="flex justify-center gap-6 mt-4 text-sm">
                  <span className="flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded" />
                    Collected
                  </span>
                </div>
              </>
            )}
          </SectionCard>

          {/* Payment Methods Breakdown */}
          <SectionCard title="Payment Methods" subtitle="Collection by payment channel">
            {summary.paymentCount === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <CreditCard className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No payments recorded</p>
                  <p className="text-sm">Payment method breakdown will appear here</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {summary.byMethod && Object.entries(summary.byMethod).map(([method, data]: [string, any], idx) => {
                  const colors: Record<string, string> = {
                    mobile_money: 'bg-green-500',
                    bank_transfer: 'bg-blue-500',
                    cash: 'bg-yellow-500',
                    card: 'bg-purple-500'
                  }
                  const labels: Record<string, string> = {
                    mobile_money: 'Mobile Money',
                    bank_transfer: 'Bank Transfer',
                    cash: 'Cash',
                    card: 'Card'
                  }
                  const percent = summary.totalCollected > 0 ? (data.total / summary.totalCollected) * 100 : 0
                  return (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-slate-700">{labels[method] || method}</span>
                        <span className="text-sm font-semibold text-slate-900">{formatCurrency(data.total)}</span>
                      </div>
                      <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${colors[method] || 'bg-slate-500'} rounded-full`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">{data.count} payments ({percent.toFixed(1)}%)</p>
                    </div>
                  )
                })}
              </div>
            )}
          </SectionCard>

          {/* Collection Summary */}
          <SectionCard title="Collection Summary" subtitle="Revenue totals">
            <div className="flex items-center justify-center py-8">
              <div className="relative w-48 h-48">
                <svg className="w-48 h-48 -rotate-90">
                  <circle
                    cx="96" cy="96" r="80"
                    stroke="#e2e8f0" strokeWidth="16" fill="none"
                  />
                  {summary.paymentCount > 0 && (
                    <circle
                      cx="96" cy="96" r="80"
                      stroke="url(#gradient)" strokeWidth="16" fill="none"
                      strokeDasharray={`${Math.min(100, summary.paymentCount) * 5.02} 502`}
                      strokeLinecap="round"
                    />
                  )}
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#22c55e" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold text-slate-900">{formatCurrency(summary.totalCollected)}</span>
                  <span className="text-sm text-slate-500">Total Collected</span>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center p-3 bg-green-50 rounded-xl">
                <p className="text-2xl font-bold text-green-600">{summary.paymentCount}</p>
                <p className="text-xs text-green-700">Total Payments</p>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-xl">
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(summary.averagePayment)}</p>
                <p className="text-xs text-blue-700">Average Payment</p>
              </div>
            </div>
          </SectionCard>

          {/* DMA Collection */}
          <SectionCard title="Collection by DMA" subtitle="Revenue per district metered area">
            {!summary.byDMA || Object.keys(summary.byDMA).length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <MapPin className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No DMA data yet</p>
                  <p className="text-sm">DMA collection breakdown will appear here</p>
                </div>
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {Object.entries(summary.byDMA).map(([dma, data]: [string, any], idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-medium text-slate-700">{dma}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-slate-900">{formatCurrency(data.total)}</p>
                      <p className="text-xs text-slate-500">{data.count} payments</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {activeTab === 'payments' && (
        <div className="space-y-4">
          {/* Recent Payments */}
          <SectionCard title="Recent Payments" subtitle="Latest payment transactions" noPadding>
            {recentPayments.length === 0 ? (
              <div className="p-12 text-center text-slate-400">
                <CreditCard className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">No Payments Yet</p>
                <p className="text-sm mt-2">
                  When customers make payments, they will appear here in real-time.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {recentPayments.map((payment, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          payment.method === 'mobile_money' ? 'bg-green-100' :
                          payment.method === 'bank_transfer' ? 'bg-blue-100' :
                          payment.method === 'cash' ? 'bg-yellow-100' : 'bg-purple-100'
                        }`}>
                          <CreditCard className={`w-5 h-5 ${
                            payment.method === 'mobile_money' ? 'text-green-600' :
                            payment.method === 'bank_transfer' ? 'text-blue-600' :
                            payment.method === 'cash' ? 'text-yellow-600' : 'text-purple-600'
                          }`} />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{payment.accountNumber}</p>
                          <p className="text-sm text-slate-500">{payment.dma} • {payment.method.replace('_', ' ')}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-600">{formatCurrency(payment.amount)}</p>
                        <p className="text-xs text-slate-400">{new Date(payment.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-4">
          {/* System Status */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-4 sm:p-6 text-white">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  LWSC Revenue Collection System
                </h3>
                <p className="text-blue-200 text-sm mt-1">
                  Real-time payment tracking and analytics
                </p>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-green-300">
                    {summary.paymentCount}
                  </p>
                  <p className="text-xs text-blue-200">Total Payments</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-yellow-300">
                    {formatCurrency(summary.totalCollected)}
                  </p>
                  <p className="text-xs text-blue-200">Revenue</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl sm:text-3xl font-bold text-cyan-300">
                    {summary.todayPayments}
                  </p>
                  <p className="text-xs text-blue-200">Today</p>
                </div>
              </div>
            </div>
          </div>

          {/* Analytics Info */}
          <SectionCard title="Analytics Overview" subtitle="Payment insights and trends">
            <div className="text-center py-8 text-slate-400">
              <TrendingUp className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">Building Analytics</p>
              <p className="text-sm mt-2 max-w-md mx-auto">
                As more payments are collected, detailed analytics including trends, 
                forecasts, and customer insights will become available here.
              </p>
              <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mx-auto">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <Users className="w-6 h-6 mx-auto text-slate-400 mb-1" />
                  <p className="text-xs text-slate-500">Customer Analytics</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <Building className="w-6 h-6 mx-auto text-slate-400 mb-1" />
                  <p className="text-xs text-slate-500">DMA Performance</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <Target className="w-6 h-6 mx-auto text-slate-400 mb-1" />
                  <p className="text-xs text-slate-500">Collection Targets</p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <AlertTriangle className="w-6 h-6 mx-auto text-slate-400 mb-1" />
                  <p className="text-xs text-slate-500">Defaulter Tracking</p>
                </div>
              </div>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  )
}
