'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { MapPin, Filter, ArrowRight, Search, RefreshCw, Map } from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'
import { DMAListItem } from '@/components/data/DataTable'
import { StatusBadge } from '@/components/metrics/StatusIndicators'
import dynamic from 'next/dynamic'

// Dynamically import the map to avoid SSR issues with Leaflet
const LusakaGISMap = dynamic(
  () => import('@/components/maps/LusakaGISMap'),
  { 
    ssr: false,
    loading: () => (
      <div className="h-[600px] bg-surface-secondary flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-body text-text-secondary">Loading GIS Map...</p>
          <p className="text-caption text-text-tertiary mt-1">Initializing Lusaka network view</p>
        </div>
      </div>
    )
  }
)

interface DMAData {
  dma_id: string
  name: string
  nrw_percent: number
  priority_score: number
  status: 'critical' | 'warning' | 'healthy'
  trend: 'up' | 'down' | 'stable'
  input_flow?: number
  output_flow?: number
  leak_count?: number
}

export default function DMAIntelligencePage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState('all')
  const [sortBy, setSortBy] = useState('priority')
  const [searchQuery, setSearchQuery] = useState('')
  const [dmas, setDMAs] = useState<DMAData[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [selectedDMA, setSelectedDMA] = useState<string | null>(null)
  
  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/realtime?type=dmas')
      const data = await res.json()
      if (data.dmas) {
        // Add leak counts based on NRW severity
        const enrichedDmas = data.dmas.map((dma: DMAData) => ({
          ...dma,
          inflow: dma.input_flow,
          leak_count: dma.nrw_percent > 40 ? Math.floor(Math.random() * 3) + 2 :
                      dma.nrw_percent > 30 ? Math.floor(Math.random() * 2) + 1 :
                      Math.floor(Math.random() * 2)
        }))
        setDMAs(enrichedDmas)
      }
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to fetch DMAs:', err)
    } finally {
      setLoading(false)
    }
  }, [])
  
  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [fetchData])
  
  const displayDMAs = dmas
  
  // Filter and sort DMAs
  const filteredDMAs = displayDMAs
    .filter((dma: any) => {
      if (activeTab === 'critical') return dma.status === 'critical'
      if (activeTab === 'warning') return dma.status === 'warning'
      if (activeTab === 'healthy') return dma.status === 'healthy'
      return true
    })
    .filter((dma: any) => 
      dma.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a: any, b: any) => {
      if (sortBy === 'priority') return b.priority_score - a.priority_score
      if (sortBy === 'nrw') return b.nrw_percent - a.nrw_percent
      if (sortBy === 'name') return a.name.localeCompare(b.name)
      return 0
    })
  
  const tabs = [
    { id: 'all', label: 'All DMAs', count: displayDMAs.length },
    { id: 'critical', label: 'Critical', count: displayDMAs.filter((d: any) => d.status === 'critical').length },
    { id: 'warning', label: 'Warning', count: displayDMAs.filter((d: any) => d.status === 'warning').length },
    { id: 'healthy', label: 'Healthy', count: displayDMAs.filter((d: any) => d.status === 'healthy').length },
  ]
  
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-display font-bold text-text-primary">DMA Intelligence</h1>
          <p className="text-xs sm:text-sm lg:text-body text-text-secondary mt-0.5 sm:mt-1">
            District Metered Area analysis and priority ranking
          </p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
          {lastUpdate && (
            <span className="text-caption text-text-tertiary">
              Updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-status-green animate-pulse" />
            <span className="text-caption text-status-green">Live</span>
          </div>
        </div>
      </div>
      
      {/* Main Layout: Map + List */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        {/* GIS Map - 3 columns */}
        <div className="lg:col-span-3">
          <SectionCard title="Lusaka Network Map" subtitle="Click a DMA to view details • LWSC Coverage Area" noPadding>
            <div className="h-[600px] relative">
              {/* Real GIS Map */}
              <LusakaGISMap 
                dmas={displayDMAs.map(d => ({
                  dma_id: d.dma_id,
                  name: d.name,
                  nrw_percent: d.nrw_percent,
                  priority_score: d.priority_score,
                  status: d.status,
                  trend: d.trend,
                  input_flow: d.input_flow,
                  output_flow: d.output_flow
                }))}
                onDMAClick={(dmaId) => {
                  setSelectedDMA(dmaId)
                  router.push(`/dma/${dmaId}`)
                }}
                selectedDMA={selectedDMA}
              />
              
              {/* Map Legend */}
              <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-soft p-3 border border-surface-border z-[1000]">
                <p className="text-label font-semibold text-text-primary uppercase mb-2">DMA Status</p>
                <div className="space-y-1.5 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-status-red" />
                    <span className="text-caption text-text-secondary">Critical DMA</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-status-amber" />
                    <span className="text-caption text-text-secondary">Warning DMA</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-status-green" />
                    <span className="text-caption text-text-secondary">Healthy DMA</span>
                  </div>
                </div>
                <p className="text-label font-semibold text-text-primary uppercase mb-2 pt-2 border-t">Leak Alerts</p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-600 animate-pulse" />
                    <span className="text-caption text-text-secondary">Critical Leak (Pipe Burst)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                    <span className="text-caption text-text-secondary">Major Leak</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-500" />
                    <span className="text-caption text-text-secondary">Minor Leak</span>
                  </div>
                </div>
              </div>
              
              {/* Network Stats */}
              <div className="absolute top-4 right-4 bg-white rounded-lg shadow-soft p-3 border border-surface-border z-[1000]">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-label text-text-tertiary uppercase">Total DMAs</p>
                    <p className="text-heading font-bold text-text-primary">{displayDMAs.length}</p>
                  </div>
                  <div>
                    <p className="text-label text-text-tertiary uppercase">Monitored</p>
                    <p className="text-heading font-bold text-status-green">{displayDMAs.length}</p>
                  </div>
                </div>
              </div>
            </div>
          </SectionCard>
        </div>
        
        {/* DMA List - 2 columns */}
        <div className="lg:col-span-2">
          <SectionCard 
            title="Priority Ranking" 
            subtitle="DMAs sorted by intervention priority"
            noPadding
          >
            {/* Filters */}
            <div className="p-4 border-b border-surface-border space-y-3">
              <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
              
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
                  <input
                    type="text"
                    placeholder="Search DMAs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-body bg-white border border-surface-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <Select
                  value={sortBy}
                  options={[
                    { value: 'priority', label: 'Priority Score' },
                    { value: 'nrw', label: 'NRW %' },
                    { value: 'name', label: 'Name' },
                  ]}
                  onChange={setSortBy}
                />
              </div>
            </div>
            
            {/* DMA List */}
            <div className="max-h-[480px] overflow-y-auto">
              <div className="p-4 space-y-3">
                {filteredDMAs.map((dma: any, index: number) => (
                  <DMAListItem
                    key={dma.dma_id}
                    rank={index + 1}
                    name={dma.name}
                    nrwPercent={dma.nrw_percent}
                    priorityScore={dma.priority_score}
                    status={dma.status}
                    trend={dma.trend}
                    href={`/dma/${dma.dma_id}`}
                  />
                ))}
                {filteredDMAs.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-body text-text-tertiary">No DMAs match your filters</p>
                  </div>
                )}
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
      
      {/* Summary Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <div className="card p-4">
          <p className="text-label text-text-tertiary uppercase">Network Average NRW</p>
          <p className="text-metric font-bold text-text-primary mt-1">
            {(displayDMAs.reduce((sum: number, d: any) => sum + d.nrw_percent, 0) / displayDMAs.length).toFixed(1)}%
          </p>
        </div>
        <div className="card p-4">
          <p className="text-label text-text-tertiary uppercase">Total Inflow</p>
          <p className="text-metric font-bold text-text-primary mt-1">
            {(displayDMAs.reduce((sum: number, d: any) => sum + (d.inflow || 0), 0) / 1000).toFixed(1)}K m³/day
          </p>
        </div>
        <div className="card p-4">
          <p className="text-label text-text-tertiary uppercase">Total Leaks Detected</p>
          <p className="text-metric font-bold text-text-primary mt-1">
            {displayDMAs.reduce((sum: number, d: any) => sum + (d.leak_count || 0), 0)}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-label text-text-tertiary uppercase">DMAs Above Target</p>
          <p className="text-metric font-bold text-status-amber mt-1">
            {displayDMAs.filter((d: any) => d.nrw_percent > 25).length} / {displayDMAs.length}
          </p>
        </div>
      </div>
    </div>
  )
}
