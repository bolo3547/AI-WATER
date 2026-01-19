'use client'

import { useState, useEffect, useRef } from 'react'
import { 
  Users, MapPin, Phone, Radio, Clock, CheckCircle, 
  AlertTriangle, Navigation, Truck, Wrench, Camera,
  MessageCircle, Send, ChevronRight, RefreshCw,
  Target, Activity, Battery, Signal, Star,
  Map, List, Filter, Download, Bell, User
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface FieldCrew {
  id: string
  name: string
  role: string
  phone: string
  status: 'available' | 'en_route' | 'on_site' | 'offline' | 'break'
  currentTask: string | null
  location: { lat: number; lng: number; address: string }
  lastUpdate: string
  completedToday: number
  rating: number
  battery: number
  signal: number
  vehicle: string | null
  skills: string[]
}

interface Task {
  id: string
  type: 'repair' | 'inspection' | 'installation' | 'emergency'
  priority: 'critical' | 'high' | 'medium' | 'low'
  location: string
  dma: string
  description: string
  assignedTo: string | null
  status: 'pending' | 'assigned' | 'in_progress' | 'completed'
  estimatedTime: number
  createdAt: string
}

interface Message {
  id: string
  from: string
  to: string
  message: string
  timestamp: string
  read: boolean
}

export default function FieldCrewPage() {
  const [activeTab, setActiveTab] = useState('map')
  const [crews, setCrews] = useState<FieldCrew[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [selectedCrew, setSelectedCrew] = useState<FieldCrew | null>(null)
  const [filterStatus, setFilterStatus] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [showDispatch, setShowDispatch] = useState(false)
  const mapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadCrews()
    loadTasks()
    loadMessages()
    
    // Simulate real-time updates
    const interval = setInterval(() => {
      updateCrewLocations()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadCrews = () => {
    setCrews([
      {
        id: 'CREW-001',
        name: 'Bwalya Mwamba',
        role: 'Senior Technician',
        phone: '+260 97 123 4567',
        status: 'on_site',
        currentTask: 'WO-2851 Pipe Repair',
        location: { lat: -15.4192, lng: 28.3225, address: 'Kabulonga Rd, Near Junction' },
        lastUpdate: '2 min ago',
        completedToday: 4,
        rating: 4.8,
        battery: 78,
        signal: 4,
        vehicle: 'LSK-4521-B',
        skills: ['Pipe Repair', 'Welding', 'Valve Maintenance']
      },
      {
        id: 'CREW-002',
        name: 'Grace Tembo',
        role: 'Field Inspector',
        phone: '+260 95 234 5678',
        status: 'en_route',
        currentTask: 'WO-2853 Inspection',
        location: { lat: -15.3958, lng: 28.3108, address: 'Roma Township Main' },
        lastUpdate: '1 min ago',
        completedToday: 6,
        rating: 4.9,
        battery: 92,
        signal: 5,
        vehicle: 'LSK-7832-A',
        skills: ['Inspection', 'Meter Reading', 'Leak Detection']
      },
      {
        id: 'CREW-003',
        name: 'Joseph Phiri',
        role: 'Emergency Response',
        phone: '+260 96 345 6789',
        status: 'available',
        currentTask: null,
        location: { lat: -15.4089, lng: 28.2953, address: 'LWSC Depot, Olympia' },
        lastUpdate: '5 min ago',
        completedToday: 3,
        rating: 4.7,
        battery: 100,
        signal: 5,
        vehicle: 'LSK-1234-E',
        skills: ['Emergency Repair', 'Heavy Equipment', 'Excavation']
      },
      {
        id: 'CREW-004',
        name: 'Mary Zulu',
        role: 'Meter Technician',
        phone: '+260 97 456 7890',
        status: 'on_site',
        currentTask: 'WO-2849 Meter Installation',
        location: { lat: -15.3605, lng: 28.3517, address: 'Chelstone Shopping Area' },
        lastUpdate: '8 min ago',
        completedToday: 8,
        rating: 4.6,
        battery: 45,
        signal: 3,
        vehicle: null,
        skills: ['Meter Installation', 'AMR Setup', 'Customer Service']
      },
      {
        id: 'CREW-005',
        name: 'Peter Banda',
        role: 'Pipe Layer',
        phone: '+260 95 567 8901',
        status: 'break',
        currentTask: null,
        location: { lat: -15.3747, lng: 28.2633, address: 'Matero Industrial Zone' },
        lastUpdate: '30 min ago',
        completedToday: 2,
        rating: 4.5,
        battery: 67,
        signal: 4,
        vehicle: 'LSK-9087-B',
        skills: ['Pipe Installation', 'Excavation', 'Backfilling']
      },
      {
        id: 'CREW-006',
        name: 'Sarah Mulenga',
        role: 'Field Supervisor',
        phone: '+260 96 678 9012',
        status: 'offline',
        currentTask: null,
        location: { lat: -15.4134, lng: 28.3064, address: 'Woodlands Office' },
        lastUpdate: '2 hours ago',
        completedToday: 0,
        rating: 4.9,
        battery: 0,
        signal: 0,
        vehicle: 'LSK-5555-S',
        skills: ['Supervision', 'Planning', 'Quality Control']
      }
    ])
  }

  const loadTasks = () => {
    setTasks([
      {
        id: 'WO-2854',
        type: 'emergency',
        priority: 'critical',
        location: 'Matero Industrial Zone',
        dma: 'Matero',
        description: 'Major pipe burst - Water gushing onto road',
        assignedTo: null,
        status: 'pending',
        estimatedTime: 120,
        createdAt: '10 min ago'
      },
      {
        id: 'WO-2853',
        type: 'inspection',
        priority: 'medium',
        location: 'Roma Township Block 4',
        dma: 'Roma',
        description: 'Routine pipeline inspection',
        assignedTo: 'CREW-002',
        status: 'assigned',
        estimatedTime: 45,
        createdAt: '1 hour ago'
      },
      {
        id: 'WO-2851',
        type: 'repair',
        priority: 'high',
        location: 'Kabulonga Rd Junction',
        dma: 'Kabulonga',
        description: 'Leaking joint repair',
        assignedTo: 'CREW-001',
        status: 'in_progress',
        estimatedTime: 90,
        createdAt: '2 hours ago'
      }
    ])
  }

  const loadMessages = () => {
    setMessages([
      {
        id: 'MSG-001',
        from: 'Control Center',
        to: 'CREW-001',
        message: 'Please prioritize the Kabulonga leak. Customer complaints increasing.',
        timestamp: '10:30 AM',
        read: true
      },
      {
        id: 'MSG-002',
        from: 'CREW-001',
        to: 'Control Center',
        message: 'Copy that. ETA 45 minutes to complete.',
        timestamp: '10:35 AM',
        read: true
      },
      {
        id: 'MSG-003',
        from: 'CREW-003',
        to: 'Control Center',
        message: 'Available for emergency dispatch. Standing by at depot.',
        timestamp: '10:45 AM',
        read: false
      }
    ])
  }

  const updateCrewLocations = () => {
    // Simulate GPS updates
    setCrews(prev => prev.map(crew => ({
      ...crew,
      lastUpdate: crew.status !== 'offline' ? 'Just now' : crew.lastUpdate
    })))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-500'
      case 'en_route': return 'bg-blue-500 animate-pulse'
      case 'on_site': return 'bg-orange-500'
      case 'break': return 'bg-yellow-500'
      case 'offline': return 'bg-gray-400'
      default: return 'bg-gray-500'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-700'
      case 'en_route': return 'bg-blue-100 text-blue-700'
      case 'on_site': return 'bg-orange-100 text-orange-700'
      case 'break': return 'bg-yellow-100 text-yellow-700'
      case 'offline': return 'bg-gray-100 text-gray-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-700 border-green-200'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const filteredCrews = filterStatus 
    ? crews.filter(c => c.status === filterStatus)
    : crews

  const stats = {
    available: crews.filter(c => c.status === 'available').length,
    active: crews.filter(c => ['en_route', 'on_site'].includes(c.status)).length,
    offline: crews.filter(c => c.status === 'offline').length,
    pendingTasks: tasks.filter(t => t.status === 'pending').length,
    completedToday: crews.reduce((sum, c) => sum + c.completedToday, 0)
  }

  const sendMessage = () => {
    if (!newMessage.trim() || !selectedCrew) return
    
    const msg: Message = {
      id: `MSG-${Date.now()}`,
      from: 'Control Center',
      to: selectedCrew.id,
      message: newMessage,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      read: false
    }
    setMessages(prev => [...prev, msg])
    setNewMessage('')
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />
            Field Crew Tracking
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time GPS tracking and task management
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => loadCrews()}>
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
          <Button variant="primary" onClick={() => setShowDispatch(true)}>
            <Send className="w-4 h-4" />
            Dispatch
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{stats.available}</p>
              <p className="text-xs text-slate-500">Available</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
              <Activity className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{stats.active}</p>
              <p className="text-xs text-slate-500">Active</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
              <Signal className="w-4 h-4 text-gray-600" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{stats.offline}</p>
              <p className="text-xs text-slate-500">Offline</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-red-600" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{stats.pendingTasks}</p>
              <p className="text-xs text-slate-500">Pending</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4 col-span-2 sm:col-span-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center">
              <Target className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-900">{stats.completedToday}</p>
              <p className="text-xs text-slate-500">Done Today</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'map', label: 'Map View' },
          { id: 'list', label: 'Crew List' },
          { id: 'tasks', label: 'Tasks' }
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'map' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Map */}
          <div className="lg:col-span-2 bg-gradient-to-br from-slate-200 to-slate-300 rounded-xl h-[500px] relative overflow-hidden">
            {/* Simulated map with markers */}
            <div className="absolute inset-0 flex items-center justify-center">
              <Map className="w-24 h-24 text-slate-400" />
            </div>
            
            {/* Crew markers */}
            {crews.filter(c => c.status !== 'offline').map((crew, idx) => (
              <div
                key={crew.id}
                className="absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2 transition-all hover:scale-110"
                style={{
                  left: `${20 + idx * 12}%`,
                  top: `${25 + idx * 10}%`
                }}
                onClick={() => setSelectedCrew(crew)}
              >
                <div className="relative">
                  <div className={`w-10 h-10 rounded-full ${getStatusColor(crew.status)} flex items-center justify-center text-white shadow-lg`}>
                    <User className="w-5 h-5" />
                  </div>
                  <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-full flex items-center justify-center text-[10px] font-bold shadow">
                    {crew.completedToday}
                  </span>
                </div>
                <div className="mt-1 px-2 py-0.5 bg-black/70 text-white text-xs rounded whitespace-nowrap">
                  {crew.name.split(' ')[0]}
                </div>
              </div>
            ))}

            {/* Map Legend */}
            <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3">
              <p className="text-xs font-semibold text-slate-700 mb-2">Legend</p>
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-green-500" />
                  <span>Available</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-blue-500" />
                  <span>En Route</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-orange-500" />
                  <span>On Site</span>
                </div>
              </div>
            </div>
          </div>

          {/* Crew Details Panel */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            {selectedCrew ? (
              <div>
                <div className={`p-4 ${
                  selectedCrew.status === 'available' ? 'bg-green-600' :
                  selectedCrew.status === 'en_route' ? 'bg-blue-600' :
                  selectedCrew.status === 'on_site' ? 'bg-orange-600' : 'bg-gray-600'
                } text-white`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                        <User className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="font-bold">{selectedCrew.name}</p>
                        <p className="text-sm opacity-80">{selectedCrew.role}</p>
                      </div>
                    </div>
                    <button onClick={() => setSelectedCrew(null)} className="p-1 hover:bg-white/20 rounded">✕</button>
                  </div>
                </div>
                <div className="p-4 space-y-4">
                  {/* Status & Location */}
                  <div className="flex items-center justify-between">
                    <span className={`px-3 py-1 rounded-full text-sm ${getStatusBadge(selectedCrew.status)}`}>
                      {selectedCrew.status.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-500">{selectedCrew.lastUpdate}</span>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-3">
                    <p className="text-xs text-slate-500">Current Location</p>
                    <p className="font-medium text-slate-900">{selectedCrew.location.address}</p>
                  </div>

                  {selectedCrew.currentTask && (
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-xs text-blue-500">Current Task</p>
                      <p className="font-medium text-blue-900">{selectedCrew.currentTask}</p>
                    </div>
                  )}

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-slate-50 rounded-lg p-2">
                      <p className="text-lg font-bold text-slate-900">{selectedCrew.completedToday}</p>
                      <p className="text-xs text-slate-500">Today</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <p className="text-lg font-bold text-slate-900 flex items-center justify-center gap-0.5">
                        {selectedCrew.rating}<Star className="w-3 h-3 text-yellow-500" />
                      </p>
                      <p className="text-xs text-slate-500">Rating</p>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-2">
                      <p className="text-lg font-bold text-slate-900 flex items-center justify-center gap-0.5">
                        <Battery className={`w-4 h-4 ${selectedCrew.battery > 50 ? 'text-green-500' : selectedCrew.battery > 20 ? 'text-yellow-500' : 'text-red-500'}`} />
                        {selectedCrew.battery}%
                      </p>
                      <p className="text-xs text-slate-500">Battery</p>
                    </div>
                  </div>

                  {/* Skills */}
                  <div>
                    <p className="text-xs text-slate-500 mb-2">Skills</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedCrew.skills.map((skill, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button variant="primary" className="flex-1">
                      <Phone className="w-4 h-4" />
                      Call
                    </Button>
                    <Button variant="secondary" className="flex-1">
                      <MessageCircle className="w-4 h-4" />
                      Message
                    </Button>
                  </div>

                  {/* Quick Message */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="Send quick message..."
                      className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    />
                    <Button variant="primary" onClick={sendMessage}>
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4">
                <h3 className="font-semibold text-slate-900 mb-3">Select a crew member</h3>
                <p className="text-sm text-slate-500">Click on a marker on the map to view crew details</p>
                
                {/* Quick List */}
                <div className="mt-4 space-y-2">
                  {crews.slice(0, 4).map((crew) => (
                    <div 
                      key={crew.id}
                      className="flex items-center gap-3 p-2 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100"
                      onClick={() => setSelectedCrew(crew)}
                    >
                      <span className={`w-2 h-2 rounded-full ${getStatusColor(crew.status)}`} />
                      <span className="text-sm font-medium text-slate-900">{crew.name}</span>
                      <span className="text-xs text-slate-500 ml-auto">{crew.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'list' && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <Select
              value={filterStatus}
              options={[
                { value: '', label: 'All Status' },
                { value: 'available', label: '🟢 Available' },
                { value: 'en_route', label: '🔵 En Route' },
                { value: 'on_site', label: '🟠 On Site' },
                { value: 'break', label: '🟡 On Break' },
                { value: 'offline', label: '⚫ Offline' }
              ]}
              onChange={setFilterStatus}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCrews.map((crew) => (
              <div 
                key={crew.id}
                className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-lg transition-all cursor-pointer"
                onClick={() => setSelectedCrew(crew)}
              >
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <div className={`w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center`}>
                      <User className="w-6 h-6 text-slate-600" />
                    </div>
                    <span className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-white ${getStatusColor(crew.status)}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-900">{crew.name}</p>
                    <p className="text-sm text-slate-500">{crew.role}</p>
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs mt-1 ${getStatusBadge(crew.status)}`}>
                      {crew.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="mt-3 text-sm text-slate-600">
                  <p className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {crew.location.address}
                  </p>
                  {crew.currentTask && (
                    <p className="flex items-center gap-1 text-blue-600 mt-1">
                      <Wrench className="w-3 h-3" />
                      {crew.currentTask}
                    </p>
                  )}
                </div>

                <div className="mt-3 flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1 text-slate-500">
                    <Clock className="w-3 h-3" />
                    {crew.lastUpdate}
                  </span>
                  <span className="flex items-center gap-1">
                    <Target className="w-3 h-3 text-green-500" />
                    {crew.completedToday} done
                  </span>
                  <span className="flex items-center gap-1">
                    <Star className="w-3 h-3 text-yellow-500" />
                    {crew.rating}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeTab === 'tasks' && (
        <SectionCard title="Pending Tasks" subtitle="Unassigned and in-progress work orders">
          <div className="space-y-3">
            {tasks.map((task) => (
              <div key={task.id} className="bg-slate-50 rounded-xl p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      task.type === 'emergency' ? 'bg-red-100' :
                      task.type === 'repair' ? 'bg-orange-100' :
                      task.type === 'inspection' ? 'bg-blue-100' : 'bg-green-100'
                    }`}>
                      {task.type === 'emergency' && <AlertTriangle className="w-5 h-5 text-red-600" />}
                      {task.type === 'repair' && <Wrench className="w-5 h-5 text-orange-600" />}
                      {task.type === 'inspection' && <Camera className="w-5 h-5 text-blue-600" />}
                      {task.type === 'installation' && <CheckCircle className="w-5 h-5 text-green-600" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-slate-400">{task.id}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs border ${getPriorityColor(task.priority)}`}>
                          {task.priority}
                        </span>
                      </div>
                      <p className="font-semibold text-slate-900 mt-1">{task.description}</p>
                      <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                        <MapPin className="w-3 h-3" />
                        {task.location} • {task.dma}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right text-sm">
                      <p className="text-slate-500">{task.createdAt}</p>
                      <p className="text-slate-700">~{task.estimatedTime} min</p>
                    </div>
                    {task.status === 'pending' ? (
                      <Button variant="primary" size="sm">
                        Assign
                      </Button>
                    ) : (
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        task.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Dispatch Modal */}
      {showDispatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-900">Dispatch Crew</h2>
              <p className="text-slate-500 text-sm">Assign available crew to pending task</p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Select Task</label>
                <Select
                  value=""
                  options={[
                    { value: '', label: 'Choose a task...' },
                    ...tasks.filter(t => t.status === 'pending').map(t => ({
                      value: t.id,
                      label: `${t.id} - ${t.description.substring(0, 30)}...`
                    }))
                  ]}
                  onChange={() => {}}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Select Crew</label>
                <Select
                  value=""
                  options={[
                    { value: '', label: 'Choose crew member...' },
                    ...crews.filter(c => c.status === 'available').map(c => ({
                      value: c.id,
                      label: `${c.name} - ${c.role}`
                    }))
                  ]}
                  onChange={() => {}}
                />
              </div>
              <div className="flex gap-2 pt-4">
                <Button variant="secondary" className="flex-1" onClick={() => setShowDispatch(false)}>
                  Cancel
                </Button>
                <Button variant="primary" className="flex-1">
                  <Send className="w-4 h-4" />
                  Dispatch
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
