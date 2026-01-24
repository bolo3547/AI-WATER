'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { 
  Droplets, CheckCircle, Clock, Loader2, AlertTriangle,
  Search, ChevronRight, Phone, Mail, MapPin, User,
  CircleDot, ArrowRight, ExternalLink, RefreshCw
} from 'lucide-react'

// Status configuration
const STATUS_CONFIG = {
  received: {
    label: 'Report Received',
    description: 'Your report has been received and logged in our system.',
    color: 'text-slate-400',
    bgColor: 'bg-slate-400',
    icon: CircleDot,
  },
  under_review: {
    label: 'Under Review',
    description: 'Our team is reviewing your report.',
    color: 'text-blue-400',
    bgColor: 'bg-blue-400',
    icon: Search,
  },
  technician_assigned: {
    label: 'Team Assigned',
    description: 'A field team has been assigned to investigate.',
    color: 'text-amber-400',
    bgColor: 'bg-amber-400',
    icon: User,
  },
  in_progress: {
    label: 'Work In Progress',
    description: 'Our team is actively working on resolving this issue.',
    color: 'text-purple-400',
    bgColor: 'bg-purple-400',
    icon: Loader2,
  },
  resolved: {
    label: 'Issue Resolved',
    description: 'The reported issue has been successfully resolved.',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400',
    icon: CheckCircle,
  },
  closed: {
    label: 'Case Closed',
    description: 'This case has been closed.',
    color: 'text-slate-400',
    bgColor: 'bg-slate-400',
    icon: CheckCircle,
  },
}

// Category labels
const CATEGORY_LABELS: Record<string, string> = {
  leak: '💧 Leak / Drip',
  burst: '💦 Burst Pipe',
  no_water: '🚫 No Water',
  low_pressure: '📉 Low Pressure',
  illegal_connection: '⚠️ Illegal Connection',
  overflow: '🌊 Overflow / Flooding',
  contamination: '☣️ Water Quality Issue',
  other: '❓ Other Issue',
}

interface TimelineEntry {
  status: string
  message: string
  timestamp: string
}

interface TrackingData {
  ticket: string
  status: string
  status_label: string
  category: string
  area: string | null
  timeline: TimelineEntry[]
  created_at: string
  last_updated: string
  resolved_at: string | null
}

export default function TrackReportPage() {
  const params = useParams()
  const ticketFromUrl = params.ticket as string | undefined
  
  const [ticketInput, setTicketInput] = useState(ticketFromUrl || '')
  const [searchedTicket, setSearchedTicket] = useState(ticketFromUrl || '')
  const [trackingData, setTrackingData] = useState<TrackingData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  // Fetch tracking data
  const fetchTracking = async (ticket: string) => {
    if (!ticket || ticket.length < 6) return

    setIsLoading(true)
    setError(null)

    try {
      const tenantId = 'lwsc-zambia' // Would come from context
      const response = await fetch(`/api/public-reports/track/${ticket}?tenant_id=${tenantId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          setError(`Ticket ${ticket.toUpperCase()} not found. Please check the number and try again.`)
        } else {
          setError('Unable to fetch report status. Please try again.')
        }
        setTrackingData(null)
        return
      }

      const data = await response.json()
      setTrackingData(data)
      setLastRefresh(new Date())
    } catch (err) {
      console.error('Tracking error:', err)
      setError('Connection error. Please check your internet and try again.')
      setTrackingData(null)
    } finally {
      setIsLoading(false)
    }
  }

  // Fetch on mount if ticket in URL
  useEffect(() => {
    if (ticketFromUrl) {
      setTicketInput(ticketFromUrl)
      setSearchedTicket(ticketFromUrl)
      fetchTracking(ticketFromUrl)
    }
  }, [ticketFromUrl])

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const cleanTicket = ticketInput.trim().toUpperCase()
    setSearchedTicket(cleanTicket)
    fetchTracking(cleanTicket)
  }

  // Refresh
  const handleRefresh = () => {
    if (searchedTicket) {
      fetchTracking(searchedTicket)
    }
  }

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-ZM', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Get status step index (for progress display)
  const getStatusStep = (status: string) => {
    const steps = ['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved']
    return steps.indexOf(status)
  }

  const currentStatusConfig = trackingData ? STATUS_CONFIG[trackingData.status as keyof typeof STATUS_CONFIG] : null

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/report" className="flex items-center gap-2">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Droplets className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100">AquaWatch</h1>
              <p className="text-xs text-slate-400">Track Your Report</p>
            </div>
          </Link>
          <Link 
            href="/report" 
            className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            New Report <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-4 py-6">
        {/* Search form */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-100 text-center mb-2">
            Track Your Report
          </h2>
          <p className="text-slate-400 text-center mb-6">
            Enter your ticket number to check status
          </p>

          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={ticketInput}
                onChange={(e) => setTicketInput(e.target.value.toUpperCase())}
                placeholder="TKT-XXXXXX"
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono text-lg tracking-wider"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading || ticketInput.length < 6}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-semibold rounded-xl transition-colors flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Search className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>

        {/* Error state */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3 mb-6">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-red-200 font-medium">Report Not Found</p>
              <p className="text-red-200/70 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="text-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-blue-400 mx-auto mb-4" />
            <p className="text-slate-400">Looking up your report...</p>
          </div>
        )}

        {/* Tracking results */}
        {trackingData && !isLoading && currentStatusConfig && (
          <div className="space-y-6">
            {/* Ticket header */}
            <div className="p-6 bg-slate-800/50 rounded-xl border border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-slate-400">Ticket Number</p>
                  <p className="text-2xl font-mono font-bold text-blue-400">
                    {trackingData.ticket}
                  </p>
                </div>
                <button
                  onClick={handleRefresh}
                  disabled={isLoading}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                  title="Refresh status"
                >
                  <RefreshCw className={`w-5 h-5 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {/* Current status badge */}
              <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${currentStatusConfig.bgColor}/20`}>
                <currentStatusConfig.icon className={`w-5 h-5 ${currentStatusConfig.color}`} />
                <span className={`font-semibold ${currentStatusConfig.color}`}>
                  {currentStatusConfig.label}
                </span>
              </div>

              <p className="text-slate-400 text-sm mt-3">
                {currentStatusConfig.description}
              </p>
            </div>

            {/* Progress bar */}
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <p className="text-sm text-slate-400 mb-4">Progress</p>
              <div className="flex items-center justify-between relative">
                {/* Progress line */}
                <div className="absolute top-3 left-4 right-4 h-0.5 bg-slate-700">
                  <div 
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ 
                      width: `${(getStatusStep(trackingData.status) / 4) * 100}%`
                    }}
                  />
                </div>

                {/* Steps */}
                {['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved'].map((step, index) => {
                  const isCompleted = getStatusStep(trackingData.status) >= index
                  const isCurrent = trackingData.status === step
                  const config = STATUS_CONFIG[step as keyof typeof STATUS_CONFIG]
                  
                  return (
                    <div key={step} className="flex flex-col items-center relative z-10">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        isCompleted 
                          ? isCurrent ? config.bgColor : 'bg-blue-500'
                          : 'bg-slate-700'
                      }`}>
                        {isCompleted && <CheckCircle className="w-4 h-4 text-white" />}
                      </div>
                      <span className={`text-xs mt-2 ${
                        isCurrent ? config.color : isCompleted ? 'text-slate-300' : 'text-slate-500'
                      }`}>
                        {index + 1}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Report details */}
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 space-y-3">
              <p className="text-sm text-slate-400">Report Details</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500">Category</p>
                  <p className="text-slate-100">
                    {CATEGORY_LABELS[trackingData.category] || trackingData.category}
                  </p>
                </div>
                
                {trackingData.area && (
                  <div>
                    <p className="text-xs text-slate-500">Area</p>
                    <p className="text-slate-100">{trackingData.area}</p>
                  </div>
                )}
                
                <div>
                  <p className="text-xs text-slate-500">Reported</p>
                  <p className="text-slate-100">{formatDate(trackingData.created_at)}</p>
                </div>
                
                <div>
                  <p className="text-xs text-slate-500">Last Updated</p>
                  <p className="text-slate-100">{formatDate(trackingData.last_updated)}</p>
                </div>

                {trackingData.resolved_at && (
                  <div className="col-span-2">
                    <p className="text-xs text-slate-500">Resolved</p>
                    <p className="text-emerald-400">{formatDate(trackingData.resolved_at)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Timeline */}
            <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <p className="text-sm text-slate-400 mb-4">Timeline</p>
              
              <div className="space-y-4">
                {trackingData.timeline.map((entry, index) => {
                  const config = STATUS_CONFIG[entry.status as keyof typeof STATUS_CONFIG]
                  const isLast = index === trackingData.timeline.length - 1
                  
                  return (
                    <div key={index} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-3 h-3 rounded-full ${isLast ? config?.bgColor : 'bg-slate-600'}`} />
                        {index < trackingData.timeline.length - 1 && (
                          <div className="w-0.5 h-full bg-slate-700 mt-1" />
                        )}
                      </div>
                      <div className="flex-1 pb-4">
                        <p className={`font-medium ${isLast ? config?.color : 'text-slate-300'}`}>
                          {config?.label || entry.status}
                        </p>
                        <p className="text-sm text-slate-400 mt-1">{entry.message}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {formatDate(entry.timestamp)}
                        </p>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Last refresh time */}
            {lastRefresh && (
              <p className="text-xs text-slate-500 text-center">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </p>
            )}
          </div>
        )}

        {/* No search yet */}
        {!trackingData && !isLoading && !error && !searchedTicket && (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">Enter your ticket number above to track your report</p>
            <p className="text-sm text-slate-500 mt-2">
              The ticket number was provided when you submitted your report
            </p>
          </div>
        )}
      </main>

      {/* Help section */}
      <section className="max-w-2xl mx-auto px-4 py-8">
        <div className="p-4 bg-slate-800/30 rounded-xl border border-slate-800">
          <h3 className="font-semibold text-slate-200 mb-2">Need help?</h3>
          <p className="text-sm text-slate-400 mb-3">
            If you have questions about your report or need to provide additional information:
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <a 
              href="tel:+260211123456" 
              className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
            >
              <Phone className="w-4 h-4" />
              +260 211 123 456
            </a>
            <a 
              href="mailto:support@aquawatch.zm" 
              className="flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm"
            >
              <Mail className="w-4 h-4" />
              support@aquawatch.zm
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-2xl mx-auto px-4 py-8 text-center">
        <p className="text-sm text-slate-500">
          Powered by <span className="text-blue-400">AquaWatch NRW</span>
        </p>
        <p className="text-xs text-slate-600 mt-1">
          Helping reduce water loss in Zambia
        </p>
      </footer>
    </div>
  )
}
