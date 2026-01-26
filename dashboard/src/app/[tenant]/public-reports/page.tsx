'use client'

import { useState, useEffect, useMemo } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { 
  Droplets, Search, Filter, MapPin, Clock, AlertTriangle, CheckCircle,
  ChevronDown, ChevronRight, Eye, Merge, FileText, Wrench, MoreVertical,
  Phone, Mail, User, Flag, Trash2, RefreshCw, Download, Map,
  AlertCircle, X, Check, Loader2, Settings, Plus, ExternalLink, 
  TrendingUp, Users, Target, Brain, Link2
} from 'lucide-react'

// Types
interface PublicReport {
  id: string
  ticket: string
  tenant_id: string
  category: string
  description: string | null
  latitude: number | null
  longitude: number | null
  area_text: string | null
  source: string
  reporter_name: string | null
  reporter_phone: string | null
  reporter_email: string | null
  reporter_consent: boolean
  status: string
  verification: string
  trust_score_delta: number
  spam_flag: boolean
  quarantine: boolean
  master_report_id: string | null
  is_master: boolean
  duplicate_count: number
  linked_leak_id: string | null
  linked_work_order_id: string | null
  admin_notes: string | null
  assigned_to_user_id: string | null
  assigned_team: string | null
  assigned_at: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
  media_count: number
}

// Status badge colors
const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  received: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
  under_review: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  technician_assigned: { bg: 'bg-amber-500/20', text: 'text-amber-400' },
  in_progress: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  resolved: { bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
  closed: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
}

const VERIFICATION_COLORS: Record<string, { bg: string; text: string }> = {
  pending: { bg: 'bg-slate-500/20', text: 'text-slate-400' },
  confirmed: { bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
  duplicate: { bg: 'bg-amber-500/20', text: 'text-amber-400' },
  false_report: { bg: 'bg-red-500/20', text: 'text-red-400' },
  needs_review: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  spam: { bg: 'bg-red-500/20', text: 'text-red-400' },
}

const CATEGORY_ICONS: Record<string, string> = {
  leak: '💧',
  burst: '💦',
  no_water: '🚫',
  low_pressure: '📉',
  illegal_connection: '⚠️',
  overflow: '🌊',
  contamination: '☣️',
  other: '❓',
}

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  web: { label: 'Web', color: 'text-blue-400' },
  whatsapp: { label: 'WhatsApp', color: 'text-emerald-400' },
  ussd: { label: 'USSD', color: 'text-amber-400' },
  mobile_app: { label: 'App', color: 'text-purple-400' },
  call_center: { label: 'Call', color: 'text-slate-400' },
}

// Mock data
const generateMockReports = (count: number): PublicReport[] => {
  const categories = ['leak', 'burst', 'no_water', 'low_pressure', 'illegal_connection', 'overflow']
  const statuses = ['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved']
  const verifications = ['pending', 'confirmed', 'duplicate', 'false_report', 'needs_review']
  const sources = ['web', 'whatsapp', 'ussd']
  const areas = [
    'Central Business District',
    'Kabulonga',
    'Chilenje South',
    'Matero',
    'Garden Compound',
    'Kamwala',
    'Kalingalinga',
    'Woodlands',
  ]

  return Array.from({ length: count }, (_, i) => ({
    id: `${i + 1}`,
    ticket: `TKT-${String(i + 1).padStart(6, 'A').slice(-6).replace(/\d/g, c => 'ABCDEFGHIJ'[parseInt(c)])}${i}`,
    tenant_id: 'lwsc-zambia',
    category: categories[i % categories.length],
    description: i % 3 === 0 ? 'Water leaking from pipe near the road junction' : null,
    latitude: -15.4 + (Math.random() * 0.1),
    longitude: 28.27 + (Math.random() * 0.1),
    area_text: areas[i % areas.length],
    source: sources[i % sources.length],
    reporter_name: i % 2 === 0 ? `Reporter ${i + 1}` : null,
    reporter_phone: i % 2 === 0 ? `+260 97${i}234567` : null,
    reporter_email: null,
    reporter_consent: i % 2 === 0,
    status: statuses[i % statuses.length],
    verification: verifications[i % verifications.length],
    trust_score_delta: 0,
    spam_flag: i === 7,
    quarantine: i === 7,
    master_report_id: null,
    is_master: true,
    duplicate_count: i % 5 === 0 ? Math.floor(Math.random() * 3) + 1 : 0,
    linked_leak_id: i === 0 ? 'leak-123' : null,
    linked_work_order_id: i === 2 ? 'wo-456' : null,
    admin_notes: null,
    assigned_to_user_id: i % 4 === 0 ? 'user-123' : null,
    assigned_team: i % 4 === 0 ? 'Team Alpha' : null,
    assigned_at: i % 4 === 0 ? new Date(Date.now() - i * 3600000).toISOString() : null,
    resolved_at: statuses[i % statuses.length] === 'resolved' ? new Date().toISOString() : null,
    created_at: new Date(Date.now() - i * 7200000).toISOString(),
    updated_at: new Date(Date.now() - i * 3600000).toISOString(),
    media_count: i % 3 === 0 ? 2 : 0,
  }))
}

export default function PublicReportsPage() {
  const params = useParams()
  const tenantId = params.tenant as string || 'lwsc-zambia'

  const [reports, setReports] = useState<PublicReport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedReports, setSelectedReports] = useState<Set<string>>(new Set())
  const [expandedReport, setExpandedReport] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')
  
  // Filters
  const [filters, setFilters] = useState({
    status: '',
    category: '',
    verification: '',
    source: '',
    spamOnly: false,
    quarantineOnly: false,
    search: '',
    dateRange: 'all',
  })

  // Modal states
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showMergeModal, setShowMergeModal] = useState(false)
  const [showWorkOrderModal, setShowWorkOrderModal] = useState(false)
  const [actionReport, setActionReport] = useState<PublicReport | null>(null)

  // Load data from API
  const fetchReports = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/public-reports?tenant_id=${tenantId}&page_size=100`)
      const data = await response.json()
      
      if (data.items && data.items.length > 0) {
        // Map API response to expected format
        const mappedReports: PublicReport[] = data.items.map((item: PublicReport) => ({
          ...item,
          area_text: item.area_text || 'Location not specified',
        }))
        setReports(mappedReports)
      } else {
        // If no reports in database, show some mock data for demo
        setReports(generateMockReports(5))
      }
    } catch (error) {
      console.error('Error fetching reports:', error)
      // Fallback to mock data if API fails
      setReports(generateMockReports(5))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchReports()
  }, [tenantId])

  // Filter reports
  const filteredReports = useMemo(() => {
    return reports.filter(r => {
      if (filters.status && r.status !== filters.status) return false
      if (filters.category && r.category !== filters.category) return false
      if (filters.verification && r.verification !== filters.verification) return false
      if (filters.source && r.source !== filters.source) return false
      if (filters.spamOnly && !r.spam_flag) return false
      if (filters.quarantineOnly && !r.quarantine) return false
      if (filters.search) {
        const search = filters.search.toLowerCase()
        if (!r.ticket.toLowerCase().includes(search) &&
            !r.area_text?.toLowerCase().includes(search) &&
            !r.description?.toLowerCase().includes(search)) {
          return false
        }
      }
      return true
    })
  }, [reports, filters])

  // Stats
  const stats = useMemo(() => ({
    total: reports.length,
    new: reports.filter(r => r.status === 'received').length,
    inProgress: reports.filter(r => ['under_review', 'technician_assigned', 'in_progress'].includes(r.status)).length,
    spam: reports.filter(r => r.spam_flag).length,
    quarantine: reports.filter(r => r.quarantine).length,
  }), [reports])

  // Toggle report selection
  const toggleSelect = (id: string) => {
    const newSelected = new Set(selectedReports)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedReports(newSelected)
  }

  // Select all visible
  const selectAll = () => {
    if (selectedReports.size === filteredReports.length) {
      setSelectedReports(new Set())
    } else {
      setSelectedReports(new Set(filteredReports.map(r => r.id)))
    }
  }

  // Update status
  const updateStatus = async (reportId: string, newStatus: string) => {
    setReports(prev => prev.map(r => 
      r.id === reportId ? { ...r, status: newStatus, updated_at: new Date().toISOString() } : r
    ))
  }

  // Update verification
  const updateVerification = async (reportId: string, verification: string) => {
    setReports(prev => prev.map(r => 
      r.id === reportId ? { ...r, verification, updated_at: new Date().toISOString() } : r
    ))
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-40">
        <div className="max-w-[1800px] mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Users className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-100">Public Reports</h1>
                <p className="text-sm text-slate-400">Community-reported water issues</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* View toggle */}
              <div className="flex bg-slate-800 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 rounded text-sm ${viewMode === 'list' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
                >
                  List
                </button>
                <button
                  onClick={() => setViewMode('map')}
                  className={`px-3 py-1.5 rounded text-sm ${viewMode === 'map' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
                >
                  <Map className="w-4 h-4 inline mr-1" />
                  Map
                </button>
              </div>

              <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-400">
                <Download className="w-5 h-5" />
              </button>
              <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-400">
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-[1800px] mx-auto px-4 py-6">
        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">Total Reports</p>
              <Droplets className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-slate-100 mt-1">{stats.total}</p>
          </div>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">New</p>
              <AlertCircle className="w-5 h-5 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-amber-400 mt-1">{stats.new}</p>
          </div>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">In Progress</p>
              <Loader2 className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-2xl font-bold text-blue-400 mt-1">{stats.inProgress}</p>
          </div>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">Spam Flagged</p>
              <Flag className="w-5 h-5 text-red-400" />
            </div>
            <p className="text-2xl font-bold text-red-400 mt-1">{stats.spam}</p>
          </div>
          <div className="p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">Quarantine</p>
              <AlertTriangle className="w-5 h-5 text-amber-400" />
            </div>
            <p className="text-2xl font-bold text-amber-400 mt-1">{stats.quarantine}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 mb-6">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  placeholder="Search ticket, area, description..."
                  className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Status filter */}
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="received">Received</option>
              <option value="under_review">Under Review</option>
              <option value="technician_assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>

            {/* Category filter */}
            <select
              value={filters.category}
              onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Categories</option>
              <option value="leak">💧 Leak</option>
              <option value="burst">💦 Burst</option>
              <option value="no_water">🚫 No Water</option>
              <option value="low_pressure">📉 Low Pressure</option>
              <option value="illegal_connection">⚠️ Illegal Connection</option>
              <option value="overflow">🌊 Overflow</option>
            </select>

            {/* Verification filter */}
            <select
              value={filters.verification}
              onChange={(e) => setFilters(prev => ({ ...prev, verification: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Verifications</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="duplicate">Duplicate</option>
              <option value="false_report">False Report</option>
              <option value="needs_review">Needs Review</option>
            </select>

            {/* Source filter */}
            <select
              value={filters.source}
              onChange={(e) => setFilters(prev => ({ ...prev, source: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="">All Sources</option>
              <option value="web">Web</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="ussd">USSD</option>
            </select>

            {/* Quick filters */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.spamOnly}
                onChange={(e) => setFilters(prev => ({ ...prev, spamOnly: e.target.checked }))}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700"
              />
              <span className="text-sm text-slate-300">Spam Only</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.quarantineOnly}
                onChange={(e) => setFilters(prev => ({ ...prev, quarantineOnly: e.target.checked }))}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700"
              />
              <span className="text-sm text-slate-300">Quarantine</span>
            </label>
          </div>
        </div>

        {/* Bulk actions */}
        {selectedReports.size > 0 && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-4 flex items-center justify-between">
            <p className="text-blue-200">
              <strong>{selectedReports.size}</strong> reports selected
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setShowMergeModal(true)}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm flex items-center gap-2"
              >
                <Merge className="w-4 h-4" /> Merge
              </button>
              <button className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm flex items-center gap-2">
                <Check className="w-4 h-4" /> Mark Confirmed
              </button>
              <button className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm flex items-center gap-2">
                <Flag className="w-4 h-4" /> Mark Spam
              </button>
            </div>
          </div>
        )}

        {/* Reports list */}
        {viewMode === 'list' && (
          <div className="bg-slate-900/60 rounded-xl border border-slate-800 overflow-hidden">
            {/* Table header */}
            <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-slate-800/50 text-sm text-slate-400 font-medium">
              <div className="col-span-1 flex items-center">
                <input
                  type="checkbox"
                  checked={selectedReports.size === filteredReports.length && filteredReports.length > 0}
                  onChange={selectAll}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700"
                />
              </div>
              <div className="col-span-2">Ticket</div>
              <div className="col-span-2">Category</div>
              <div className="col-span-2">Location</div>
              <div className="col-span-1">Source</div>
              <div className="col-span-1">Status</div>
              <div className="col-span-1">Verification</div>
              <div className="col-span-1">Time</div>
              <div className="col-span-1">Actions</div>
            </div>

            {/* Loading */}
            {isLoading && (
              <div className="p-8 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-400 mx-auto mb-2" />
                <p className="text-slate-400">Loading reports...</p>
              </div>
            )}

            {/* Reports */}
            {!isLoading && filteredReports.map((report) => (
              <div key={report.id}>
                <div
                  className={`grid grid-cols-12 gap-4 px-4 py-3 border-t border-slate-800 hover:bg-slate-800/30 cursor-pointer ${
                    selectedReports.has(report.id) ? 'bg-blue-500/10' : ''
                  } ${report.spam_flag ? 'bg-red-500/5' : ''} ${report.quarantine ? 'bg-amber-500/5' : ''}`}
                  onClick={() => setExpandedReport(expandedReport === report.id ? null : report.id)}
                >
                  {/* Checkbox */}
                  <div className="col-span-1 flex items-center" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedReports.has(report.id)}
                      onChange={() => toggleSelect(report.id)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700"
                    />
                  </div>

                  {/* Ticket */}
                  <div className="col-span-2 flex items-center gap-2">
                    <span className="font-mono text-blue-400">{report.ticket}</span>
                    {report.duplicate_count > 0 && (
                      <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded">
                        +{report.duplicate_count}
                      </span>
                    )}
                    {report.spam_flag && (
                      <Flag className="w-4 h-4 text-red-400" />
                    )}
                  </div>

                  {/* Category */}
                  <div className="col-span-2 flex items-center gap-2">
                    <span className="text-xl">{CATEGORY_ICONS[report.category]}</span>
                    <span className="text-slate-200 capitalize">{report.category.replace('_', ' ')}</span>
                  </div>

                  {/* Location */}
                  <div className="col-span-2 text-slate-300 truncate">
                    {report.area_text || (report.latitude ? `${report.latitude.toFixed(4)}, ${report.longitude?.toFixed(4)}` : '-')}
                  </div>

                  {/* Source */}
                  <div className="col-span-1">
                    <span className={SOURCE_LABELS[report.source]?.color || 'text-slate-400'}>
                      {SOURCE_LABELS[report.source]?.label || report.source}
                    </span>
                  </div>

                  {/* Status */}
                  <div className="col-span-1">
                    <span className={`px-2 py-1 rounded text-xs ${STATUS_COLORS[report.status]?.bg} ${STATUS_COLORS[report.status]?.text}`}>
                      {report.status.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Verification */}
                  <div className="col-span-1">
                    <span className={`px-2 py-1 rounded text-xs ${VERIFICATION_COLORS[report.verification]?.bg} ${VERIFICATION_COLORS[report.verification]?.text}`}>
                      {report.verification.replace('_', ' ')}
                    </span>
                  </div>

                  {/* Time */}
                  <div className="col-span-1 text-slate-400 text-sm">
                    {formatDate(report.created_at)}
                  </div>

                  {/* Actions */}
                  <div className="col-span-1 flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="p-1.5 hover:bg-slate-700 rounded text-slate-400"
                      onClick={() => {
                        setActionReport(report)
                        setShowAssignModal(true)
                      }}
                      title="Assign"
                    >
                      <User className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1.5 hover:bg-slate-700 rounded text-slate-400"
                      onClick={() => {
                        setActionReport(report)
                        setShowWorkOrderModal(true)
                      }}
                      title="Create Work Order"
                    >
                      <Wrench className="w-4 h-4" />
                    </button>
                    <ChevronRight className={`w-4 h-4 text-slate-500 transition-transform ${expandedReport === report.id ? 'rotate-90' : ''}`} />
                  </div>
                </div>

                {/* Expanded details */}
                {expandedReport === report.id && (
                  <div className="px-4 py-4 bg-slate-800/30 border-t border-slate-800">
                    <div className="grid grid-cols-3 gap-6">
                      {/* Details */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-slate-200">Details</h4>
                        {report.description && (
                          <p className="text-sm text-slate-400">{report.description}</p>
                        )}
                        {report.media_count > 0 && (
                          <p className="text-sm text-blue-400">📷 {report.media_count} media attached</p>
                        )}
                        {report.linked_leak_id && (
                          <div className="flex items-center gap-2 text-sm text-emerald-400">
                            <Brain className="w-4 h-4" />
                            Linked to AI Leak
                          </div>
                        )}
                        {report.linked_work_order_id && (
                          <div className="flex items-center gap-2 text-sm text-purple-400">
                            <Wrench className="w-4 h-4" />
                            Work Order Created
                          </div>
                        )}
                      </div>

                      {/* Reporter */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-slate-200">Reporter</h4>
                        {report.reporter_name && (
                          <div className="flex items-center gap-2 text-sm text-slate-300">
                            <User className="w-4 h-4 text-slate-500" />
                            {report.reporter_name}
                          </div>
                        )}
                        {report.reporter_phone && (
                          <div className="flex items-center gap-2 text-sm text-slate-300">
                            <Phone className="w-4 h-4 text-slate-500" />
                            {report.reporter_phone}
                          </div>
                        )}
                        {!report.reporter_name && !report.reporter_phone && (
                          <p className="text-sm text-slate-500">Anonymous report</p>
                        )}
                      </div>

                      {/* Quick actions */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-slate-200">Quick Actions</h4>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => updateVerification(report.id, 'confirmed')}
                            className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 rounded text-sm"
                          >
                            ✓ Confirm
                          </button>
                          <button
                            onClick={() => updateVerification(report.id, 'duplicate')}
                            className="px-3 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 rounded text-sm"
                          >
                            Duplicate
                          </button>
                          <button
                            onClick={() => updateVerification(report.id, 'false_report')}
                            className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm"
                          >
                            False
                          </button>
                          <button
                            onClick={() => {
                              setActionReport(report)
                              setShowWorkOrderModal(true)
                            }}
                            className="px-3 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 rounded text-sm"
                          >
                            → Work Order
                          </button>
                        </div>

                        {/* Status update */}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-400">Status:</span>
                          <select
                            value={report.status}
                            onChange={(e) => updateStatus(report.id, e.target.value)}
                            className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-sm text-slate-200"
                          >
                            <option value="received">Received</option>
                            <option value="under_review">Under Review</option>
                            <option value="technician_assigned">Assigned</option>
                            <option value="in_progress">In Progress</option>
                            <option value="resolved">Resolved</option>
                            <option value="closed">Closed</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Empty state */}
            {!isLoading && filteredReports.length === 0 && (
              <div className="p-8 text-center">
                <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No reports match your filters</p>
              </div>
            )}
          </div>
        )}

        {/* Map view */}
        {viewMode === 'map' && (
          <div className="bg-slate-900/60 rounded-xl border border-slate-800 overflow-hidden">
            <div className="h-[600px] flex items-center justify-center bg-slate-800/30">
              <div className="text-center">
                <Map className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Map clustering view</p>
                <p className="text-sm text-slate-500 mt-1">
                  {filteredReports.length} reports with location data
                </p>
                <p className="text-xs text-slate-600 mt-4">
                  (Map integration with Leaflet/Mapbox would go here)
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Assign Modal */}
      {showAssignModal && actionReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="font-semibold text-slate-100">Assign Report</h3>
              <button onClick={() => setShowAssignModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-sm text-slate-400">
                Assigning: <span className="text-blue-400 font-mono">{actionReport.ticket}</span>
              </p>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Team</label>
                <select className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100">
                  <option>Team Alpha</option>
                  <option>Team Beta</option>
                  <option>Team Gamma</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Technician</label>
                <select className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100">
                  <option>John Mwansa</option>
                  <option>Mary Banda</option>
                  <option>Peter Phiri</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t border-slate-800">
              <button
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  updateStatus(actionReport.id, 'technician_assigned')
                  setShowAssignModal(false)
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
              >
                Assign
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Work Order Modal */}
      {showWorkOrderModal && actionReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-xl border border-slate-800 w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h3 className="font-semibold text-slate-100">Create Work Order</h3>
              <button onClick={() => setShowWorkOrderModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-sm text-slate-400">
                From report: <span className="text-blue-400 font-mono">{actionReport.ticket}</span>
              </p>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Task Type</label>
                <select className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100">
                  <option>Investigation</option>
                  <option>Repair</option>
                  <option>Inspection</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Priority</label>
                <select className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100">
                  <option value="1">🔴 Critical</option>
                  <option value="2">🟠 High</option>
                  <option value="3" selected>🟡 Medium</option>
                  <option value="4">🟢 Low</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Notes</label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder:text-slate-500"
                  placeholder="Additional instructions..."
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t border-slate-800">
              <button
                onClick={() => setShowWorkOrderModal(false)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Would create work order via API
                  setReports(prev => prev.map(r => 
                    r.id === actionReport.id 
                      ? { ...r, linked_work_order_id: 'wo-new', verification: 'confirmed' }
                      : r
                  ))
                  setShowWorkOrderModal(false)
                }}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2"
              >
                <Wrench className="w-4 h-4" /> Create Work Order
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
