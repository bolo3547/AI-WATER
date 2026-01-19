'use client'

import Link from 'next/link'
import { 
  ArrowLeft, 
  TrendingDown, 
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
  Activity,
  Brain,
  Sparkles
} from 'lucide-react'
import { KPICard } from '@/components/metrics/KPICard'
import { StatusBadge, ConfidenceIndicator, PriorityScore } from '@/components/metrics/StatusIndicators'
import { SectionCard, AlertBanner } from '@/components/ui/Cards'
import { Button, Tabs } from '@/components/ui/Controls'
import { DataTable } from '@/components/data/DataTable'
import { FlowComparisonChart, NRWTrendChart } from '@/components/charts/Charts'
import { useDMADetails, useDMATimeSeries, useLeaks, formatNumber, formatRelativeTime } from '@/lib/api'
import { useState } from 'react'
import { AIInsightsPanel } from '@/components/ai/AIInsightsPanel'

// Mock data
const MOCK_DMA = {
  dma_id: 'dma-001',
  name: 'Kabulonga North',
  nrw_percent: 45.2,
  real_losses: 565,
  priority_score: 87,
  status: 'critical' as const,
  trend: 'up' as const,
  inflow: 1250,
  consumption: 685,
  leak_count: 3,
  confidence: 92,
  last_updated: new Date().toISOString()
}

const MOCK_FLOW_DATA = Array.from({ length: 24 }, (_, i) => ({
  timestamp: `${i.toString().padStart(2, '0')}:00`,
  inflow: 45 + Math.sin(i / 3) * 15 + (i > 2 && i < 6 ? -20 : 0),
  consumption: 30 + Math.sin(i / 3) * 10 + (i > 2 && i < 6 ? -25 : 0),
  minimumNightFlow: i > 1 && i < 5 ? 8 : undefined
}))

const MOCK_NRW_TREND = Array.from({ length: 30 }, (_, i) => ({
  timestamp: new Date(Date.now() - (29 - i) * 86400000).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
  nrw: 40 + (i * 0.15) + (Math.random() * 3 - 1.5),
  target: 25
}))

const MOCK_LEAKS = [
  { id: 'leak-001', location: 'Junction Rd & Leopards Hill Rd', estimated_loss: 280, priority: 'high' as const, status: 'detected', confidence: 92, detected_at: new Date(Date.now() - 3600000).toISOString(), method: 'Acoustic + Flow Analysis' },
  { id: 'leak-002', location: 'Plot 4521 Service Line', estimated_loss: 150, priority: 'medium' as const, status: 'investigating', confidence: 78, detected_at: new Date(Date.now() - 86400000).toISOString(), method: 'Night Flow Analysis' },
  { id: 'leak-003', location: 'Main Distribution Pipe - Block C', estimated_loss: 135, priority: 'medium' as const, status: 'confirmed', confidence: 95, detected_at: new Date(Date.now() - 172800000).toISOString(), method: 'Pressure Transient' },
]

interface PageProps {
  params: { id: string }
}

export default function DMADeepDivePage({ params }: PageProps) {
  const { id } = params
  const [activeTab, setActiveTab] = useState('24h')
  
  const { data: dma } = useDMADetails(id)
  const { data: flowData } = useDMATimeSeries(id, '24h')
  const { data: leaks } = useLeaks(id)
  
  const displayDMA = dma || MOCK_DMA
  const displayFlowData = flowData || MOCK_FLOW_DATA
  const displayLeaks = leaks || MOCK_LEAKS
  
  const tabs = [
    { id: '24h', label: 'Last 24 Hours' },
    { id: '7d', label: 'Last 7 Days' },
    { id: '30d', label: 'Last 30 Days' },
  ]
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'detected': return <AlertTriangle className="w-4 h-4 text-status-red" />
      case 'investigating': return <Clock className="w-4 h-4 text-status-amber" />
      case 'confirmed': return <Activity className="w-4 h-4 text-primary-600" />
      case 'repaired': return <CheckCircle className="w-4 h-4 text-status-green" />
      default: return null
    }
  }
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/dma" className="inline-flex items-center gap-1 text-caption text-text-secondary hover:text-text-primary mb-2">
            <ArrowLeft className="w-4 h-4" />
            Back to DMA List
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-display font-bold text-text-primary">{displayDMA.name}</h1>
            <StatusBadge status={displayDMA.status} />
          </div>
          <p className="text-body text-text-secondary mt-1">
            DMA ID: {displayDMA.dma_id} • Last updated: {formatRelativeTime(displayDMA.last_updated)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <PriorityScore score={displayDMA.priority_score} />
          <Button variant="primary">
            Create Work Order
          </Button>
        </div>
      </div>
      
      {/* Primary KPIs */}
      <div className="grid grid-cols-5 gap-4">
        <KPICard
          label="NRW Rate"
          value={displayDMA.nrw_percent}
          unit="%"
          trend={displayDMA.trend}
          trendValue={3.2}
          status={displayDMA.status}
          large
        />
        <KPICard
          label="Real Losses"
          value={formatNumber(displayDMA.real_losses)}
          unit="m³/day"
          trend="stable"
        />
        <KPICard
          label="Inflow"
          value={formatNumber(displayDMA.inflow)}
          unit="m³/day"
        />
        <KPICard
          label="Consumption"
          value={formatNumber(displayDMA.consumption)}
          unit="m³/day"
        />
        <KPICard
          label="Active Leaks"
          value={displayDMA.leak_count}
          status={displayDMA.leak_count > 2 ? 'critical' : displayDMA.leak_count > 0 ? 'warning' : 'healthy'}
        />
      </div>
      
      {/* AI Analysis Banner */}
      <AlertBanner
        type="info"
        title="AI Analysis: High night flow detected"
        message={`Minimum night flow of 8.2 m³/h significantly exceeds expected baseline of 3.5 m³/h. This indicates approximately ${displayDMA.real_losses} m³/day of real losses, primarily from suspected main pipe leak near Junction Rd.`}
        action={
          <Button variant="secondary" size="sm">View Details</Button>
        }
      />
      
      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Flow Chart - 2 columns */}
        <div className="col-span-2">
          <SectionCard 
            title="Flow Analysis"
            subtitle="Inflow vs metered consumption showing loss patterns"
            action={<Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />}
          >
            <FlowComparisonChart data={displayFlowData} height={320} />
            
            {/* Flow Insights */}
            <div className="mt-4 pt-4 border-t border-surface-border grid grid-cols-4 gap-4">
              <div>
                <p className="text-label text-text-tertiary uppercase">Avg Inflow</p>
                <p className="text-body font-semibold text-text-primary">52.1 m³/h</p>
              </div>
              <div>
                <p className="text-label text-text-tertiary uppercase">Avg Consumption</p>
                <p className="text-body font-semibold text-text-primary">28.5 m³/h</p>
              </div>
              <div>
                <p className="text-label text-text-tertiary uppercase">Min Night Flow</p>
                <p className="text-body font-semibold text-status-red">8.2 m³/h</p>
              </div>
              <div>
                <p className="text-label text-text-tertiary uppercase">Expected MNF</p>
                <p className="text-body font-semibold text-text-primary">3.5 m³/h</p>
              </div>
            </div>
          </SectionCard>
        </div>
        
        {/* NRW Trend - 1 column */}
        <div className="col-span-1">
          <SectionCard title="NRW Trend" subtitle="30-day historical">
            <NRWTrendChart data={MOCK_NRW_TREND} height={200} />
            
            <div className="mt-4 pt-4 border-t border-surface-border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-caption text-text-secondary">Target NRW</span>
                <span className="text-body font-semibold text-text-primary">25%</span>
              </div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-caption text-text-secondary">Current NRW</span>
                <span className="text-body font-semibold text-status-red">{displayDMA.nrw_percent}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-caption text-text-secondary">Gap to Target</span>
                <span className="text-body font-semibold text-status-amber">{(displayDMA.nrw_percent - 25).toFixed(1)}%</span>
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
      
      {/* Detected Leaks */}
      <SectionCard 
        title="Detected Leaks" 
        subtitle="AI-identified potential leak locations in this DMA"
        action={
          <div className="flex items-center gap-2">
            <ConfidenceIndicator value={displayDMA.confidence} showLabel />
          </div>
        }
      >
        <DataTable
          columns={[
            { 
              key: 'status', 
              header: 'Status', 
              width: '100px',
              render: (row: any) => (
                <div className="flex items-center gap-2">
                  {getStatusIcon(row.status)}
                  <span className="text-caption capitalize">{row.status}</span>
                </div>
              )
            },
            { key: 'location', header: 'Location' },
            { 
              key: 'estimated_loss', 
              header: 'Est. Loss',
              render: (row: any) => `${row.estimated_loss} m³/day`
            },
            { key: 'method', header: 'Detection Method' },
            { 
              key: 'confidence', 
              header: 'Confidence',
              align: 'center' as const,
              render: (row: any) => (
                <span className={`font-medium ${row.confidence >= 85 ? 'text-status-green' : row.confidence >= 70 ? 'text-status-amber' : 'text-text-secondary'}`}>
                  {row.confidence}%
                </span>
              )
            },
            { 
              key: 'detected_at', 
              header: 'Detected',
              render: (row: any) => formatRelativeTime(row.detected_at)
            },
            {
              key: 'actions',
              header: '',
              width: '120px',
              render: () => (
                <Button variant="ghost" size="sm">
                  View Details
                </Button>
              )
            }
          ]}
          data={displayLeaks}
          keyExtractor={(row: any) => row.id}
          onRowClick={(row: any) => console.log('Click leak', row.id)}
        />
      </SectionCard>
      
      {/* AI Analysis Panel - Powered by Groq */}
      <AIInsightsPanel 
        type="dma_recommendation"
        title="AI DMA Analysis"
        data={{
          dma: displayDMA,
          leaks: displayLeaks,
          flowData: MOCK_FLOW_DATA,
          nrwTrend: MOCK_NRW_TREND
        }}
        autoLoad={true}
      />
    </div>
  )
}
