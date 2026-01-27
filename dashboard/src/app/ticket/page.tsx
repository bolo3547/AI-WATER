'use client'

import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { 
  MessageCircle, Send, Clock, CheckCircle, AlertTriangle, 
  MapPin, Calendar, User, ArrowLeft, Loader2, Image as ImageIcon,
  Phone, Droplets, RefreshCw
} from 'lucide-react'

interface Message {
  id: string
  sender: 'user' | 'team'
  senderName?: string
  content: string
  timestamp: string
  read: boolean
}

interface TicketData {
  ticketId: string
  status: 'pending' | 'acknowledged' | 'in-progress' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'critical'
  reportType: string
  description: string
  location: string
  createdAt: string
  updatedAt: string
  assignedTo?: string
  estimatedResolution?: string
  messages: Message[]
  images?: string[]
}

const statusConfig = {
  'pending': { label: 'Pending Review', color: 'bg-amber-500', textColor: 'text-amber-400', icon: Clock },
  'acknowledged': { label: 'Acknowledged', color: 'bg-blue-500', textColor: 'text-blue-400', icon: CheckCircle },
  'in-progress': { label: 'In Progress', color: 'bg-purple-500', textColor: 'text-purple-400', icon: RefreshCw },
  'resolved': { label: 'Resolved', color: 'bg-emerald-500', textColor: 'text-emerald-400', icon: CheckCircle },
  'closed': { label: 'Closed', color: 'bg-slate-500', textColor: 'text-slate-400', icon: CheckCircle },
}

const priorityConfig = {
  'low': { label: 'Low', color: 'bg-slate-500' },
  'medium': { label: 'Medium', color: 'bg-amber-500' },
  'high': { label: 'High', color: 'bg-orange-500' },
  'critical': { label: 'Critical', color: 'bg-red-500' },
}

export default function TicketPage() {
  const searchParams = useSearchParams()
  const ticketId = searchParams.get('id') || searchParams.get('ticket')
  
  const [ticket, setTicket] = useState<TicketData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch ticket data
  useEffect(() => {
    if (!ticketId) {
      setLoading(false)
      return
    }

    const fetchTicket = async () => {
      try {
        const response = await fetch(`/api/ticket/${ticketId}`)
        if (!response.ok) {
          throw new Error('Ticket not found')
        }
        const data = await response.json()
        setTicket(data)
      } catch (err) {
        // Demo data for display
        setTicket({
          ticketId: ticketId,
          status: 'in-progress',
          priority: 'high',
          reportType: 'Water Leak',
          description: 'Large water leak near the main road junction. Water is flowing continuously and causing road damage.',
          location: 'Plot 123, Great East Road, Lusaka',
          createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          updatedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          assignedTo: 'Field Team Alpha',
          estimatedResolution: '24-48 hours',
          messages: [
            {
              id: '1',
              sender: 'team',
              senderName: 'LWSC Support',
              content: 'Thank you for reporting this issue. Your report has been received and assigned to our field team.',
              timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
              read: true
            },
            {
              id: '2',
              sender: 'team',
              senderName: 'Field Team Alpha',
              content: 'We have dispatched a team to assess the situation. They should arrive within the next 2 hours.',
              timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
              read: true
            },
            {
              id: '3',
              sender: 'user',
              content: 'The leak seems to be getting worse. Please hurry.',
              timestamp: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
              read: true
            },
            {
              id: '4',
              sender: 'team',
              senderName: 'Field Team Alpha',
              content: 'Our team is now on site and has begun repair work. We expect to complete the repair within the next few hours. Thank you for your patience.',
              timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
              read: true
            },
          ]
        })
      } finally {
        setLoading(false)
      }
    }

    fetchTicket()
  }, [ticketId])

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [ticket?.messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !ticket) return

    setSending(true)
    try {
      // In production, this would send to the API
      const newMsg: Message = {
        id: Date.now().toString(),
        sender: 'user',
        content: newMessage,
        timestamp: new Date().toISOString(),
        read: false
      }
      
      setTicket({
        ...ticket,
        messages: [...ticket.messages, newMsg]
      })
      setNewMessage('')
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setSending(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-ZM', { 
      day: 'numeric', 
      month: 'short', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatMessageTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60 * 60 * 1000) {
      const mins = Math.floor(diff / 60000)
      return mins <= 1 ? 'Just now' : `${mins} mins ago`
    }
    if (diff < 24 * 60 * 60 * 1000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours}h ago`
    }
    return date.toLocaleDateString('en-ZM', { day: 'numeric', month: 'short' })
  }

  // No ticket ID provided - show search form
  if (!ticketId) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-2xl font-bold text-slate-100 mb-2">View Your Ticket</h1>
            <p className="text-slate-400">Enter your ticket number to view status and chat with our team</p>
          </div>

          <form action="/ticket" method="GET" className="space-y-4">
            <div>
              <label htmlFor="id" className="block text-sm font-medium text-slate-300 mb-2">
                Ticket Number
              </label>
              <input
                type="text"
                id="id"
                name="id"
                placeholder="TKT-XXXXXX"
                required
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-mono text-lg tracking-wider text-center"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors"
            >
              View Ticket
            </button>
          </form>

          <div className="mt-8 text-center space-y-2">
            <Link href="/report" className="block text-blue-400 hover:text-blue-300 text-sm">
              Submit a new report →
            </Link>
            <Link href="/" className="block text-slate-400 hover:text-slate-300 text-sm">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading ticket...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error || !ticket) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <h1 className="text-xl font-bold text-slate-100 mb-2">Ticket Not Found</h1>
          <p className="text-slate-400 mb-6">We couldn't find a ticket with that number. Please check and try again.</p>
          <Link
            href="/ticket"
            className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors"
          >
            Try Again
          </Link>
        </div>
      </div>
    )
  }

  const StatusIcon = statusConfig[ticket.status].icon

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back to Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <Droplets className="w-6 h-6 text-blue-400" />
              <span className="font-bold text-white">AquaWatch</span>
            </div>
            <Link href="/report" className="text-blue-400 hover:text-blue-300 text-sm font-medium">
              New Report
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Ticket Info Card */}
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700 p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
            <div>
              <p className="text-slate-400 text-sm mb-1">Ticket Number</p>
              <p className="text-2xl font-bold text-white font-mono">{ticket.ticketId}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-xs font-semibold text-white ${priorityConfig[ticket.priority].color}`}>
                {priorityConfig[ticket.priority].label} Priority
              </span>
              <span className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${statusConfig[ticket.status].textColor} bg-slate-700`}>
                <StatusIcon className="w-3.5 h-3.5" />
                {statusConfig[ticket.status].label}
              </span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
                <div>
                  <p className="text-slate-400 text-xs">Issue Type</p>
                  <p className="text-white font-medium">{ticket.reportType}</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-slate-400 text-xs">Location</p>
                  <p className="text-white font-medium">{ticket.location}</p>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-emerald-400 mt-0.5" />
                <div>
                  <p className="text-slate-400 text-xs">Reported</p>
                  <p className="text-white font-medium">{formatDate(ticket.createdAt)}</p>
                </div>
              </div>
              {ticket.assignedTo && (
                <div className="flex items-start gap-3">
                  <User className="w-5 h-5 text-purple-400 mt-0.5" />
                  <div>
                    <p className="text-slate-400 text-xs">Assigned To</p>
                    <p className="text-white font-medium">{ticket.assignedTo}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {ticket.estimatedResolution && (
            <div className="mt-4 p-3 bg-blue-500/10 rounded-xl border border-blue-500/30">
              <p className="text-blue-400 text-sm">
                <span className="font-semibold">Estimated Resolution:</span> {ticket.estimatedResolution}
              </p>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-slate-700">
            <p className="text-slate-400 text-sm">{ticket.description}</p>
          </div>
        </div>

        {/* Chat Section */}
        <div className="bg-slate-800/50 rounded-2xl border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700 bg-slate-800/50">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-blue-400" />
              Messages
            </h2>
            <p className="text-slate-400 text-sm mt-1">Chat with our team about this report</p>
          </div>

          {/* Messages List */}
          <div className="h-[400px] overflow-y-auto p-4 space-y-4">
            {ticket.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${message.sender === 'user' ? 'order-1' : 'order-2'}`}>
                  {message.sender === 'team' && message.senderName && (
                    <p className="text-xs text-slate-500 mb-1 ml-1">{message.senderName}</p>
                  )}
                  <div
                    className={`p-3 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-br-md'
                        : 'bg-slate-700 text-slate-100 rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                  </div>
                  <p className={`text-xs text-slate-500 mt-1 ${message.sender === 'user' ? 'text-right mr-1' : 'ml-1'}`}>
                    {formatMessageTime(message.timestamp)}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-700 bg-slate-800/50">
            <div className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl text-white placeholder:text-slate-400 focus:outline-none focus:border-blue-500"
                disabled={ticket.status === 'closed'}
              />
              <button
                type="submit"
                disabled={!newMessage.trim() || sending || ticket.status === 'closed'}
                className="px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            {ticket.status === 'closed' && (
              <p className="text-slate-500 text-xs mt-2 text-center">This ticket is closed. Submit a new report if you need further assistance.</p>
            )}
          </form>
        </div>

        {/* Help Section */}
        <div className="mt-6 p-4 bg-slate-800/30 rounded-xl border border-slate-700/50">
          <p className="text-slate-400 text-sm text-center">
            Need urgent help? Call our hotline: <a href="tel:+260211250155" className="text-blue-400 font-semibold">+260 211 250 155</a>
          </p>
        </div>
      </div>
    </div>
  )
}
