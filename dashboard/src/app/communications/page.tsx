'use client'

import { useState, useEffect, useRef } from 'react'
import { 
  MessageSquare, Send, Users, Search, Phone, Mail, Bell,
  ChevronRight, Clock, CheckCheck, Check, Filter, Plus,
  AlertTriangle, MapPin, User, Globe, Inbox, Archive,
  RefreshCw, Paperclip, Smile, X, ExternalLink, Eye
} from 'lucide-react'

// Types
interface TeamMember {
  id: string
  name: string
  role: 'admin' | 'operator' | 'technician'
  status: 'online' | 'away' | 'offline'
  avatar?: string
  lastSeen?: string
  unread: number
}

interface PublicReport {
  id: string
  ticket: string
  reporterName: string
  reporterPhone?: string
  reporterEmail?: string
  category: string
  description: string
  location: string
  status: 'received' | 'under_review' | 'in_progress' | 'resolved'
  createdAt: string
  unread: number
}

interface Message {
  id: string
  content: string
  sender: string
  senderRole: string
  timestamp: string
  read: boolean
  type: 'text' | 'status_update' | 'system'
}

interface Conversation {
  id: string
  type: 'team' | 'public'
  participant: TeamMember | PublicReport
  messages: Message[]
  lastMessage?: Message
}

export default function CommunicationsPage() {
  const [activeTab, setActiveTab] = useState<'team' | 'public'>('team')
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [messageInput, setMessageInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Team members
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([
    { id: 'op-1', name: 'John Banda', role: 'operator', status: 'online', unread: 2 },
    { id: 'op-2', name: 'Mary Mwale', role: 'operator', status: 'online', unread: 0 },
    { id: 'op-3', name: 'Peter Phiri', role: 'operator', status: 'away', unread: 1 },
    { id: 'tech-1', name: 'James Zulu', role: 'technician', status: 'online', unread: 0 },
    { id: 'tech-2', name: 'David Tembo', role: 'technician', status: 'online', unread: 3 },
    { id: 'tech-3', name: 'Grace Lungu', role: 'technician', status: 'offline', unread: 0 },
    { id: 'tech-4', name: 'Samuel Mbewe', role: 'technician', status: 'online', unread: 0 },
    { id: 'admin-2', name: 'Christine Mumba', role: 'admin', status: 'online', unread: 0 },
  ])

  // Public reports
  const [publicReports, setPublicReports] = useState<PublicReport[]>([
    {
      id: 'rpt-1',
      ticket: 'TKT-A3X7K2',
      reporterName: 'Chilufya Mwansa',
      reporterPhone: '+260977123456',
      category: 'leak',
      description: 'Large water leak on main road near the market',
      location: 'Cairo Road, near Levy Junction',
      status: 'under_review',
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      unread: 1
    },
    {
      id: 'rpt-2',
      ticket: 'TKT-B8M4P9',
      reporterName: 'Anonymous',
      category: 'burst',
      description: 'Pipe burst flooding the street',
      location: 'Kabulonga, Plot 1234',
      status: 'in_progress',
      createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      unread: 0
    },
    {
      id: 'rpt-3',
      ticket: 'TKT-C2N8L5',
      reporterName: 'Bwalya Chanda',
      reporterPhone: '+260955789012',
      reporterEmail: 'bwalya@email.com',
      category: 'no_water',
      description: 'No water supply for 3 days in our area',
      location: 'Chelston, Area 5',
      status: 'received',
      createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      unread: 2
    },
    {
      id: 'rpt-4',
      ticket: 'TKT-D6K3M1',
      reporterName: 'Mutale Sakala',
      reporterPhone: '+260966345678',
      category: 'low_pressure',
      description: 'Water pressure very low, can barely fill a bucket',
      location: 'Woodlands, off Kafue Road',
      status: 'resolved',
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      unread: 0
    },
  ])

  // Conversations with messages
  const [conversations, setConversations] = useState<Map<string, Conversation>>(new Map())

  useEffect(() => {
    // Initialize conversations
    const convMap = new Map<string, Conversation>()
    
    teamMembers.forEach(member => {
      convMap.set(member.id, {
        id: member.id,
        type: 'team',
        participant: member,
        messages: generateSampleMessages(member),
        lastMessage: undefined
      })
    })
    
    publicReports.forEach(report => {
      convMap.set(report.id, {
        id: report.id,
        type: 'public',
        participant: report,
        messages: generatePublicMessages(report),
        lastMessage: undefined
      })
    })
    
    // Set last messages
    convMap.forEach((conv, key) => {
      if (conv.messages.length > 0) {
        conv.lastMessage = conv.messages[conv.messages.length - 1]
      }
    })
    
    setConversations(convMap)
    setIsLoading(false)
  }, [])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [selectedConversation?.messages])

  function generateSampleMessages(member: TeamMember): Message[] {
    const now = Date.now()
    const messages: Message[] = []
    
    if (member.role === 'technician') {
      messages.push(
        { id: '1', content: `Good morning ${member.name.split(' ')[0]}, how is the repair at DMA-05 going?`, sender: 'Admin', senderRole: 'admin', timestamp: new Date(now - 3600000).toISOString(), read: true, type: 'text' },
        { id: '2', content: 'Almost done, just replacing the last valve seal', sender: member.name, senderRole: member.role, timestamp: new Date(now - 3400000).toISOString(), read: true, type: 'text' },
        { id: '3', content: 'Great work! Let me know once complete', sender: 'Admin', senderRole: 'admin', timestamp: new Date(now - 3200000).toISOString(), read: true, type: 'text' }
      )
      if (member.unread > 0) {
        messages.push(
          { id: '4', content: 'Completed the repair. Water pressure normalized.', sender: member.name, senderRole: member.role, timestamp: new Date(now - 1800000).toISOString(), read: false, type: 'text' }
        )
      }
    } else if (member.role === 'operator') {
      messages.push(
        { id: '1', content: 'Pressure drop detected in Kabulonga DMA', sender: member.name, senderRole: member.role, timestamp: new Date(now - 7200000).toISOString(), read: true, type: 'text' },
        { id: '2', content: 'Thanks for the alert. Dispatch a team to investigate.', sender: 'Admin', senderRole: 'admin', timestamp: new Date(now - 7000000).toISOString(), read: true, type: 'text' }
      )
      if (member.unread > 0) {
        messages.push(
          { id: '3', content: 'New high-priority alert from DMA-12', sender: member.name, senderRole: member.role, timestamp: new Date(now - 600000).toISOString(), read: false, type: 'text' }
        )
      }
    }
    
    return messages
  }

  function generatePublicMessages(report: PublicReport): Message[] {
    const messages: Message[] = []
    const created = new Date(report.createdAt).getTime()
    
    // Initial report
    messages.push({
      id: '1',
      content: `**New Report Submitted**\n\nCategory: ${report.category}\nLocation: ${report.location}\n\n"${report.description}"`,
      sender: report.reporterName,
      senderRole: 'public',
      timestamp: report.createdAt,
      read: true,
      type: 'text'
    })
    
    // Auto response
    messages.push({
      id: '2',
      content: `Thank you for your report (${report.ticket}). Our team will review this shortly and keep you updated.`,
      sender: 'System',
      senderRole: 'system',
      timestamp: new Date(created + 60000).toISOString(),
      read: true,
      type: 'system'
    })
    
    if (report.status !== 'received') {
      messages.push({
        id: '3',
        content: `Your report is now under review. A technician has been assigned to assess the situation.`,
        sender: 'Control Center',
        senderRole: 'admin',
        timestamp: new Date(created + 1800000).toISOString(),
        read: true,
        type: 'status_update'
      })
    }
    
    if (report.status === 'in_progress' || report.status === 'resolved') {
      messages.push({
        id: '4',
        content: `Our team is now on-site working to fix the issue. Estimated completion: 2-4 hours.`,
        sender: 'Control Center',
        senderRole: 'admin',
        timestamp: new Date(created + 3600000).toISOString(),
        read: true,
        type: 'text'
      })
    }
    
    if (report.status === 'resolved') {
      messages.push({
        id: '5',
        content: `✅ **Issue Resolved**\n\nThe reported ${report.category} has been successfully repaired. Thank you for helping us maintain water services in your community!`,
        sender: 'Control Center',
        senderRole: 'admin',
        timestamp: new Date(created + 14400000).toISOString(),
        read: true,
        type: 'status_update'
      })
    }
    
    // Unread messages from public
    if (report.unread > 0) {
      messages.push({
        id: '6',
        content: `Can you give me an update on when this will be fixed? It's been a while.`,
        sender: report.reporterName,
        senderRole: 'public',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        read: false,
        type: 'text'
      })
    }
    
    return messages
  }

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedConversation) return
    
    const newMessage: Message = {
      id: `msg-${Date.now()}`,
      content: messageInput,
      sender: 'Admin',
      senderRole: 'admin',
      timestamp: new Date().toISOString(),
      read: true,
      type: 'text'
    }
    
    // Update conversation
    const updatedConv = {
      ...selectedConversation,
      messages: [...selectedConversation.messages, newMessage],
      lastMessage: newMessage
    }
    
    setConversations(prev => {
      const newMap = new Map(prev)
      newMap.set(selectedConversation.id, updatedConv)
      return newMap
    })
    
    setSelectedConversation(updatedConv)
    setMessageInput('')
    
    // Mark conversation as read
    if (selectedConversation.type === 'team') {
      setTeamMembers(prev => prev.map(m => 
        m.id === selectedConversation.id ? { ...m, unread: 0 } : m
      ))
    } else {
      setPublicReports(prev => prev.map(r => 
        r.id === selectedConversation.id ? { ...r, unread: 0 } : r
      ))
    }
    
    // TODO: Send to API
    try {
      await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_user: 'admin',
          from_role: 'admin',
          to_user: selectedConversation.id,
          to_role: selectedConversation.type === 'team' 
            ? (selectedConversation.participant as TeamMember).role 
            : 'public',
          content: messageInput
        })
      })
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const selectConversation = (id: string) => {
    const conv = conversations.get(id)
    if (conv) {
      setSelectedConversation(conv)
      
      // Mark as read
      if (conv.type === 'team') {
        setTeamMembers(prev => prev.map(m => 
          m.id === id ? { ...m, unread: 0 } : m
        ))
      } else {
        setPublicReports(prev => prev.map(r => 
          r.id === id ? { ...r, unread: 0 } : r
        ))
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-emerald-400'
      case 'away': return 'bg-amber-400'
      case 'offline': return 'bg-slate-400'
      default: return 'bg-slate-400'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'leak': return '💧'
      case 'burst': return '💦'
      case 'no_water': return '🚫'
      case 'low_pressure': return '📉'
      default: return '📋'
    }
  }

  const getReportStatusColor = (status: string) => {
    switch (status) {
      case 'received': return 'bg-blue-100 text-blue-700'
      case 'under_review': return 'bg-amber-100 text-amber-700'
      case 'in_progress': return 'bg-purple-100 text-purple-700'
      case 'resolved': return 'bg-emerald-100 text-emerald-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  const filteredTeam = teamMembers.filter(m => {
    const matchesSearch = m.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = !filterStatus || m.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const filteredReports = publicReports.filter(r => {
    const matchesSearch = r.reporterName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.ticket.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.location.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = !filterStatus || r.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const totalUnread = teamMembers.reduce((sum, m) => sum + m.unread, 0) + 
    publicReports.reduce((sum, r) => sum + r.unread, 0)

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <MessageSquare className="w-7 h-7 text-blue-600" />
            Communications Center
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Message team members and respond to public reports
          </p>
        </div>
        <div className="flex items-center gap-3">
          {totalUnread > 0 && (
            <span className="px-3 py-1.5 bg-red-100 text-red-700 rounded-full text-sm font-medium flex items-center gap-2">
              <Bell className="w-4 h-4" />
              {totalUnread} unread
            </span>
          )}
          <button className="p-2 hover:bg-slate-100 rounded-lg">
            <RefreshCw className="w-5 h-5 text-slate-600" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        {/* Sidebar */}
        <div className="w-80 border-r border-slate-200 flex flex-col">
          {/* Tabs */}
          <div className="flex border-b border-slate-200">
            <button
              onClick={() => setActiveTab('team')}
              className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'team' 
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' 
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Users className="w-4 h-4" />
              Team
              {teamMembers.reduce((sum, m) => sum + m.unread, 0) > 0 && (
                <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                  {teamMembers.reduce((sum, m) => sum + m.unread, 0)}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('public')}
              className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'public' 
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' 
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Globe className="w-4 h-4" />
              Public
              {publicReports.reduce((sum, r) => sum + r.unread, 0) > 0 && (
                <span className="px-1.5 py-0.5 bg-red-500 text-white text-xs rounded-full">
                  {publicReports.reduce((sum, r) => sum + r.unread, 0)}
                </span>
              )}
            </button>
          </div>

          {/* Search & Filter */}
          <div className="p-3 border-b border-slate-200">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder={activeTab === 'team' ? 'Search team...' : 'Search reports...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
            <div className="flex gap-2 mt-2">
              {activeTab === 'team' ? (
                <>
                  <button
                    onClick={() => setFilterStatus(filterStatus === 'online' ? null : 'online')}
                    className={`px-2 py-1 text-xs rounded-full ${filterStatus === 'online' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}
                  >
                    Online
                  </button>
                  <button
                    onClick={() => setFilterStatus(filterStatus === 'away' ? null : 'away')}
                    className={`px-2 py-1 text-xs rounded-full ${filterStatus === 'away' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}
                  >
                    Away
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setFilterStatus(filterStatus === 'received' ? null : 'received')}
                    className={`px-2 py-1 text-xs rounded-full ${filterStatus === 'received' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}
                  >
                    New
                  </button>
                  <button
                    onClick={() => setFilterStatus(filterStatus === 'in_progress' ? null : 'in_progress')}
                    className={`px-2 py-1 text-xs rounded-full ${filterStatus === 'in_progress' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}
                  >
                    In Progress
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Conversation List */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'team' ? (
              <div className="divide-y divide-slate-100">
                {filteredTeam.map(member => {
                  const conv = conversations.get(member.id)
                  return (
                    <button
                      key={member.id}
                      onClick={() => selectConversation(member.id)}
                      className={`w-full p-3 flex items-start gap-3 hover:bg-slate-50 transition-colors text-left ${
                        selectedConversation?.id === member.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="relative">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                          {member.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${getStatusColor(member.status)}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-slate-900 truncate">{member.name}</span>
                          {member.unread > 0 && (
                            <span className="px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                              {member.unread}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-slate-500">
                          <span className={`capitalize ${member.role === 'technician' ? 'text-orange-600' : member.role === 'operator' ? 'text-blue-600' : 'text-purple-600'}`}>
                            {member.role}
                          </span>
                          <span>•</span>
                          <span>{member.status}</span>
                        </div>
                        {conv?.lastMessage && (
                          <p className="text-xs text-slate-500 truncate mt-1">
                            {conv.lastMessage.sender === 'Admin' ? 'You: ' : ''}{conv.lastMessage.content.substring(0, 40)}...
                          </p>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredReports.map(report => {
                  const conv = conversations.get(report.id)
                  return (
                    <button
                      key={report.id}
                      onClick={() => selectConversation(report.id)}
                      className={`w-full p-3 flex items-start gap-3 hover:bg-slate-50 transition-colors text-left ${
                        selectedConversation?.id === report.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-xl">
                        {getCategoryIcon(report.category)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-slate-900 truncate">{report.reporterName}</span>
                          {report.unread > 0 && (
                            <span className="px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                              {report.unread}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-slate-500">{report.ticket}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${getReportStatusColor(report.status)}`}>
                            {report.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 truncate mt-1">
                          <MapPin className="w-3 h-3 inline mr-1" />
                          {report.location}
                        </p>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center gap-3">
                  {selectedConversation.type === 'team' ? (
                    <>
                      <div className="relative">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium">
                          {(selectedConversation.participant as TeamMember).name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${getStatusColor((selectedConversation.participant as TeamMember).status)}`} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">{(selectedConversation.participant as TeamMember).name}</h3>
                        <p className="text-xs text-slate-500 capitalize">{(selectedConversation.participant as TeamMember).role} • {(selectedConversation.participant as TeamMember).status}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center text-xl">
                        {getCategoryIcon((selectedConversation.participant as PublicReport).category)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">{(selectedConversation.participant as PublicReport).reporterName}</h3>
                        <p className="text-xs text-slate-500">
                          {(selectedConversation.participant as PublicReport).ticket} • {(selectedConversation.participant as PublicReport).location}
                        </p>
                      </div>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {selectedConversation.type === 'public' && (selectedConversation.participant as PublicReport).reporterPhone && (
                    <a
                      href={`tel:${(selectedConversation.participant as PublicReport).reporterPhone}`}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Call"
                    >
                      <Phone className="w-5 h-5 text-slate-600" />
                    </a>
                  )}
                  {selectedConversation.type === 'public' && (selectedConversation.participant as PublicReport).reporterEmail && (
                    <a
                      href={`mailto:${(selectedConversation.participant as PublicReport).reporterEmail}`}
                      className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
                      title="Email"
                    >
                      <Mail className="w-5 h-5 text-slate-600" />
                    </a>
                  )}
                  <button className="p-2 hover:bg-slate-200 rounded-lg transition-colors">
                    <Eye className="w-5 h-5 text-slate-600" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
                {selectedConversation.messages.map((message) => {
                  const isAdmin = message.senderRole === 'admin'
                  const isSystem = message.type === 'system'
                  
                  if (isSystem) {
                    return (
                      <div key={message.id} className="flex justify-center">
                        <div className="px-4 py-2 bg-slate-200 text-slate-600 text-xs rounded-full">
                          {message.content}
                        </div>
                      </div>
                    )
                  }
                  
                  return (
                    <div
                      key={message.id}
                      className={`flex ${isAdmin ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[70%] ${isAdmin ? 'order-2' : ''}`}>
                        <div
                          className={`px-4 py-2.5 rounded-2xl ${
                            isAdmin
                              ? 'bg-blue-600 text-white rounded-br-md'
                              : 'bg-white border border-slate-200 text-slate-900 rounded-bl-md'
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        </div>
                        <div className={`flex items-center gap-1.5 mt-1 text-xs text-slate-400 ${isAdmin ? 'justify-end' : ''}`}>
                          <Clock className="w-3 h-3" />
                          <span>{new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          {isAdmin && (
                            message.read ? <CheckCheck className="w-3 h-3 text-blue-500" /> : <Check className="w-3 h-3" />
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Quick Responses for Public */}
              {selectedConversation.type === 'public' && (
                <div className="px-4 py-2 border-t border-slate-200 bg-slate-50 flex gap-2 overflow-x-auto">
                  <button
                    onClick={() => setMessageInput("Thank you for your report. We are currently reviewing it and will update you shortly.")}
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-slate-100 whitespace-nowrap"
                  >
                    Under Review
                  </button>
                  <button
                    onClick={() => setMessageInput("A technician has been assigned and is on the way to your location.")}
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-slate-100 whitespace-nowrap"
                  >
                    Tech Assigned
                  </button>
                  <button
                    onClick={() => setMessageInput("Our team is currently on-site working to resolve the issue. Thank you for your patience.")}
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-slate-100 whitespace-nowrap"
                  >
                    In Progress
                  </button>
                  <button
                    onClick={() => setMessageInput("✅ The issue has been resolved. Thank you for reporting this - your help keeps our water system running smoothly!")}
                    className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-slate-100 whitespace-nowrap"
                  >
                    Resolved
                  </button>
                </div>
              )}

              {/* Input */}
              <div className="p-4 border-t border-slate-200 bg-white">
                <div className="flex items-center gap-3">
                  <button className="p-2 hover:bg-slate-100 rounded-lg text-slate-400">
                    <Paperclip className="w-5 h-5" />
                  </button>
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    placeholder="Type your message..."
                    className="flex-1 px-4 py-2.5 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!messageInput.trim()}
                    className="p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400">
              <div className="text-center">
                <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium">Select a conversation</p>
                <p className="text-sm">Choose a team member or public report to start messaging</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
