'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import {
  MessageCircle, Send, Clock, CheckCircle, AlertTriangle,
  MapPin, Calendar, User, Search, Filter, RefreshCw,
  Loader2, ChevronRight, Phone, Mail, ExternalLink,
  CheckCheck, XCircle, Users, Wrench, Eye
} from 'lucide-react'

const fetcher = (url: string) => fetch(url).then(res => res.json())

interface Report {
  _id: string
  id: string
  ticket: string
  category: string
  description: string | null
  area_text: string | null
  latitude: number | null
  longitude: number | null
  reporter_name: string | null
  reporter_phone: string | null
  reporter_email: string | null
  status: string
  severity: string
  created_at: string
  updated_at: string
  assigned_to?: string
  timeline: Array<{ status: string; message: string; timestamp: string }>
}

interface Message {
  _id: string
  ticket_id: string
  sender_type: 'staff' | 'public'
  sender_name?: string
  content: string
  created_at: string
  read: boolean
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  'received': { label: 'New', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  'under_review': { label: 'Under Review', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  'technician_assigned': { label: 'Assigned', color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
  'in_progress': { label: 'In Progress', color: 'text-cyan-400', bgColor: 'bg-cyan-500/20' },
  'resolved': { label: 'Resolved', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  'closed': { label: 'Closed', color: 'text-slate-400', bgColor: 'bg-slate-500/20' },
}

const severityConfig: Record<string, { label: string; color: string }> = {
  'critical': { label: 'Critical', color: 'text-red-400' },
  'high': { label: 'High', color: 'text-orange-400' },
  'medium': { label: 'Medium', color: 'text-amber-400' },
  'low': { label: 'Low', color: 'text-slate-400' },
}

const categoryNames: Record<string, string> = {
  'leak': 'Water Leak',
  'burst': 'Burst Pipe',
  'no_water': 'No Water',
  'low_pressure': 'Low Pressure',
  'illegal_connection': 'Illegal Connection',
  'overflow': 'Overflow',
  'contamination': 'Contamination',
  'other': 'Other'
}

export default function TicketsPage() {
  const [selectedTicket, setSelectedTicket] = useState<Report | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch reports
  const { data, error, isLoading, mutate } = useSWR(
    `/api/public-reports?tenant_id=lwsc-zambia&page_size=50${statusFilter !== 'all' ? `&status=${statusFilter}` : ''}`,
    fetcher,
    { refreshInterval: 30000 }
  )

  const reports: Report[] = data?.items || []

  // Filter by search
  const filteredReports = reports.filter(report => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      report.ticket.toLowerCase().includes(query) ||
      report.description?.toLowerCase().includes(query) ||
      report.area_text?.toLowerCase().includes(query) ||
      report.reporter_name?.toLowerCase().includes(query) ||
      report.reporter_phone?.includes(query)
    )
  })

  // Fetch messages when ticket is selected
  useEffect(() => {
    if (selectedTicket) {
      fetchMessages(selectedTicket.ticket)
    }
  }, [selectedTicket])

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchMessages = async (ticketId: string) => {
    try {
      const response = await fetch(`/api/ticket/${ticketId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedTicket) return

    setSending(true)
    try {
      // Get current user from localStorage
      const userStr = localStorage.getItem('user')
      const user = userStr ? JSON.parse(userStr) : { username: 'Staff' }

      const response = await fetch(`/api/ticket/${selectedTicket.ticket}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: newMessage,
          sender_type: 'staff',
          sender_name: user.username || 'LWSC Support',
          sender_id: user.id
        })
      })

      if (response.ok) {
        setNewMessage('')
        // Refresh messages
        fetchMessages(selectedTicket.ticket)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setSending(false)
    }
  }

  const handleStatusUpdate = async (newStatus: string) => {
    if (!selectedTicket) return

    setUpdatingStatus(true)
    try {
      const response = await fetch(`/api/public-reports/${selectedTicket.ticket}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })

      if (response.ok) {
        mutate() // Refresh the list
        // Update selected ticket
        setSelectedTicket(prev => prev ? { ...prev, status: newStatus } : null)
      }
    } catch (error) {
      console.error('Failed to update status:', error)
    } finally {
      setUpdatingStatus(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-ZM', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const mins = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (mins < 60) return `${mins}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  }

  // Stats
  const stats = {
    total: reports.length,
    new: reports.filter(r => r.status === 'received').length,
    inProgress: reports.filter(r => ['under_review', 'technician_assigned', 'in_progress'].includes(r.status)).length,
    resolved: reports.filter(r => r.status === 'resolved').length
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="bg-[var(--bg-secondary)] border-b border-white/10 px-4 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <MessageCircle className="w-6 h-6 text-blue-400" />
              Public Tickets
            </h1>
            <p className="text-slate-400 text-sm mt-1">Manage reports from the public</p>
          </div>
          <button
            onClick={() => mutate()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mt-4">
          <div className="bg-white/5 rounded-lg p-3">
            <p className="text-2xl font-bold text-white">{stats.total}</p>
            <p className="text-xs text-slate-400">Total</p>
          </div>
          <div className="bg-blue-500/10 rounded-lg p-3 border border-blue-500/30">
            <p className="text-2xl font-bold text-blue-400">{stats.new}</p>
            <p className="text-xs text-slate-400">New</p>
          </div>
          <div className="bg-amber-500/10 rounded-lg p-3 border border-amber-500/30">
            <p className="text-2xl font-bold text-amber-400">{stats.inProgress}</p>
            <p className="text-xs text-slate-400">In Progress</p>
          </div>
          <div className="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/30">
            <p className="text-2xl font-bold text-emerald-400">{stats.resolved}</p>
            <p className="text-xs text-slate-400">Resolved</p>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-220px)]">
        {/* Tickets List */}
        <div className="w-full md:w-1/2 lg:w-2/5 border-r border-white/10 flex flex-col">
          {/* Filters */}
          <div className="p-3 border-b border-white/10 space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tickets..."
                className="w-full pl-9 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {['all', 'received', 'in_progress', 'resolved', 'closed'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                    statusFilter === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10'
                  }`}
                >
                  {status === 'all' ? 'All' : statusConfig[status]?.label || status}
                </button>
              ))}
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-slate-400">
                <MessageCircle className="w-8 h-8 mb-2 opacity-50" />
                <p>No tickets found</p>
              </div>
            ) : (
              filteredReports.map((report) => (
                <button
                  key={report._id}
                  onClick={() => setSelectedTicket(report)}
                  className={`w-full p-4 border-b border-white/5 text-left hover:bg-white/5 transition-colors ${
                    selectedTicket?.ticket === report.ticket ? 'bg-blue-500/10 border-l-2 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-sm text-blue-400">{report.ticket}</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${statusConfig[report.status]?.bgColor} ${statusConfig[report.status]?.color}`}>
                          {statusConfig[report.status]?.label || report.status}
                        </span>
                      </div>
                      <p className="text-white text-sm font-medium truncate">
                        {categoryNames[report.category] || report.category}
                      </p>
                      <p className="text-slate-400 text-xs truncate mt-0.5">
                        {report.area_text || report.description?.substring(0, 50) || 'No location'}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className={`text-xs font-medium ${severityConfig[report.severity]?.color}`}>
                        {severityConfig[report.severity]?.label}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">{getTimeAgo(report.created_at)}</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Ticket Detail & Chat */}
        <div className="hidden md:flex flex-1 flex-col">
          {selectedTicket ? (
            <>
              {/* Ticket Header */}
              <div className="p-4 border-b border-white/10 bg-[var(--bg-secondary)]">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-lg font-bold text-white font-mono">{selectedTicket.ticket}</h2>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${statusConfig[selectedTicket.status]?.bgColor} ${statusConfig[selectedTicket.status]?.color}`}>
                        {statusConfig[selectedTicket.status]?.label}
                      </span>
                      <span className={`text-xs font-medium ${severityConfig[selectedTicket.severity]?.color}`}>
                        {severityConfig[selectedTicket.severity]?.label} Priority
                      </span>
                    </div>
                    <p className="text-white font-medium">{categoryNames[selectedTicket.category]}</p>
                    <p className="text-slate-400 text-sm mt-1">{selectedTicket.description || 'No description'}</p>
                  </div>
                  <a
                    href={`/ticket?id=${selectedTicket.ticket}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-blue-400 text-sm hover:text-blue-300"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Public View
                  </a>
                </div>

                {/* Reporter & Location Info */}
                <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-4 h-4" />
                      <span>{selectedTicket.area_text || 'Location not specified'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(selectedTicket.created_at)}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {selectedTicket.reporter_name && (
                      <div className="flex items-center gap-2 text-slate-400">
                        <User className="w-4 h-4" />
                        <span>{selectedTicket.reporter_name}</span>
                      </div>
                    )}
                    {selectedTicket.reporter_phone && (
                      <div className="flex items-center gap-2 text-slate-400">
                        <Phone className="w-4 h-4" />
                        <a href={`tel:${selectedTicket.reporter_phone}`} className="hover:text-blue-400">
                          {selectedTicket.reporter_phone}
                        </a>
                      </div>
                    )}
                  </div>
                </div>

                {/* Status Actions */}
                <div className="flex gap-2 mt-4 flex-wrap">
                  {selectedTicket.status === 'received' && (
                    <button
                      onClick={() => handleStatusUpdate('under_review')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded-lg text-sm hover:bg-amber-500/30 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      Start Review
                    </button>
                  )}
                  {['received', 'under_review'].includes(selectedTicket.status) && (
                    <button
                      onClick={() => handleStatusUpdate('technician_assigned')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-lg text-sm hover:bg-purple-500/30 transition-colors"
                    >
                      <Users className="w-4 h-4" />
                      Assign Team
                    </button>
                  )}
                  {['technician_assigned', 'under_review'].includes(selectedTicket.status) && (
                    <button
                      onClick={() => handleStatusUpdate('in_progress')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-lg text-sm hover:bg-cyan-500/30 transition-colors"
                    >
                      <Wrench className="w-4 h-4" />
                      Start Work
                    </button>
                  )}
                  {['in_progress', 'technician_assigned'].includes(selectedTicket.status) && (
                    <button
                      onClick={() => handleStatusUpdate('resolved')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg text-sm hover:bg-emerald-500/30 transition-colors"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Mark Resolved
                    </button>
                  )}
                  {selectedTicket.status === 'resolved' && (
                    <button
                      onClick={() => handleStatusUpdate('closed')}
                      disabled={updatingStatus}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-500/20 text-slate-400 rounded-lg text-sm hover:bg-slate-500/30 transition-colors"
                    >
                      <XCircle className="w-4 h-4" />
                      Close Ticket
                    </button>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.map((message, index) => (
                  <div
                    key={message._id || index}
                    className={`flex ${message.sender_type === 'staff' ? 'justify-start' : 'justify-end'}`}
                  >
                    <div className={`max-w-[80%] ${message.sender_type === 'staff' ? '' : ''}`}>
                      {message.sender_type === 'staff' && message.sender_name && (
                        <p className="text-xs text-slate-500 mb-1 ml-1">{message.sender_name}</p>
                      )}
                      {message.sender_type === 'public' && (
                        <p className="text-xs text-slate-500 mb-1 mr-1 text-right">Customer</p>
                      )}
                      <div
                        className={`p-3 rounded-2xl ${
                          message.sender_type === 'staff'
                            ? 'bg-slate-700 text-slate-100 rounded-bl-md'
                            : 'bg-blue-600 text-white rounded-br-md'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                      </div>
                      <p className="text-xs text-slate-500 mt-1 px-1">
                        {formatDate(message.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Reply Input */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-white/10 bg-[var(--bg-secondary)]">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your response to the customer..."
                    className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
                    disabled={selectedTicket.status === 'closed'}
                  />
                  <button
                    type="submit"
                    disabled={!newMessage.trim() || sending || selectedTicket.status === 'closed'}
                    className="px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {sending ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400">
              <div className="text-center">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Select a ticket to view details and respond</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
