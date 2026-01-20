'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Wrench, MapPin, Clock, User, Phone, CheckCircle, XCircle,
  AlertTriangle, Calendar, ChevronRight, Filter, Search, Plus,
  Camera, MessageSquare, Navigation, Truck, Play, Pause, Check,
  FileText, Download, RefreshCw, MoreVertical, ArrowRight, Timer
} from 'lucide-react';

type WorkOrderStatus = 'pending' | 'assigned' | 'in-progress' | 'completed' | 'cancelled';
type Priority = 'critical' | 'high' | 'medium' | 'low';

interface WorkOrder {
  id: string;
  title: string;
  type: 'leak_repair' | 'meter_install' | 'meter_replace' | 'pipe_repair' | 'valve_maintenance' | 'inspection';
  description: string;
  location: string;
  dma: string;
  lat: number;
  lng: number;
  priority: Priority;
  status: WorkOrderStatus;
  createdAt: string;
  scheduledDate: string;
  assignedTo: string | null;
  assignedTeam: string | null;
  estimatedDuration: number; // hours
  actualDuration: number | null;
  materials: { item: string; quantity: number; used: number }[];
  notes: string[];
  photos: string[];
  customerContact: string | null;
  customerPhone: string | null;
  leakId: string | null;
  completedAt: string | null;
}

interface Technician {
  id: string;
  name: string;
  phone: string;
  team: string;
  status: 'available' | 'busy' | 'off-duty';
  currentLocation: string;
  activeOrders: number;
  skills: string[];
}

// Sample work orders
const initialWorkOrders: WorkOrder[] = [
  {
    id: 'WO-2847',
    title: 'Major Pipe Leak Repair',
    type: 'leak_repair',
    description: 'Large leak detected at intersection, water pooling on road. Estimated 45 L/min loss.',
    location: 'Great East Rd & Lumumba Rd, Matero',
    dma: 'Matero',
    lat: -15.360,
    lng: 28.275,
    priority: 'critical',
    status: 'in-progress',
    createdAt: '2026-01-18T08:30:00',
    scheduledDate: '2026-01-18',
    assignedTo: 'John Mwale',
    assignedTeam: 'Team Alpha',
    estimatedDuration: 4,
    actualDuration: null,
    materials: [
      { item: 'PVC Pipe 110mm', quantity: 2, used: 1 },
      { item: 'Coupling 110mm', quantity: 4, used: 2 },
      { item: 'Repair Clamp', quantity: 2, used: 1 },
    ],
    notes: ['Crew on site, excavation started', 'Traffic control in place'],
    photos: [],
    customerContact: 'Reported by public',
    customerPhone: null,
    leakId: 'LK-001',
    completedAt: null
  },
  {
    id: 'WO-2848',
    title: 'Smart Meter Installation',
    type: 'meter_install',
    description: 'New smart meter installation for residential customer. Replace old mechanical meter.',
    location: 'Plot 45, Leopards Hill Road, Kabulonga',
    dma: 'Kabulonga',
    lat: -15.401,
    lng: 28.325,
    priority: 'medium',
    status: 'assigned',
    createdAt: '2026-01-19T10:00:00',
    scheduledDate: '2026-01-20',
    assignedTo: 'Grace Banda',
    assignedTeam: 'Team Beta',
    estimatedDuration: 2,
    actualDuration: null,
    materials: [
      { item: 'Smart Meter ZM-R-Series', quantity: 1, used: 0 },
      { item: 'Meter Box', quantity: 1, used: 0 },
      { item: 'Stop Cock 15mm', quantity: 1, used: 0 },
    ],
    notes: ['Customer confirmed availability'],
    photos: [],
    customerContact: 'Peter Tembo',
    customerPhone: '+260 97 123 4567',
    leakId: null,
    completedAt: null
  },
  {
    id: 'WO-2849',
    title: 'Valve Replacement',
    type: 'valve_maintenance',
    description: 'Replace faulty isolation valve at DMA boundary.',
    location: 'Cairo Rd Junction, Garden',
    dma: 'Garden',
    lat: -15.402,
    lng: 28.282,
    priority: 'high',
    status: 'pending',
    createdAt: '2026-01-19T14:00:00',
    scheduledDate: '2026-01-21',
    assignedTo: null,
    assignedTeam: null,
    estimatedDuration: 3,
    actualDuration: null,
    materials: [
      { item: 'Gate Valve 150mm', quantity: 1, used: 0 },
      { item: 'Flange Set', quantity: 2, used: 0 },
      { item: 'Gaskets', quantity: 4, used: 0 },
    ],
    notes: [],
    photos: [],
    customerContact: null,
    customerPhone: null,
    leakId: null,
    completedAt: null
  },
  {
    id: 'WO-2850',
    title: 'Pipe Burst Emergency',
    type: 'pipe_repair',
    description: 'Main transmission pipe burst causing major flooding. Urgent repair needed.',
    location: 'Kafue Road, Near Chilenje Market',
    dma: 'Chilenje',
    lat: -15.448,
    lng: 28.265,
    priority: 'critical',
    status: 'assigned',
    createdAt: '2026-01-20T06:15:00',
    scheduledDate: '2026-01-20',
    assignedTo: 'Moses Phiri',
    assignedTeam: 'Team Alpha',
    estimatedDuration: 6,
    actualDuration: null,
    materials: [
      { item: 'HDPE Pipe 200mm', quantity: 3, used: 0 },
      { item: 'Electrofusion Coupling', quantity: 2, used: 0 },
      { item: 'Repair Sleeve', quantity: 1, used: 0 },
    ],
    notes: ['Emergency crew dispatched', 'Water supply isolated'],
    photos: [],
    customerContact: null,
    customerPhone: null,
    leakId: 'LK-004',
    completedAt: null
  },
  {
    id: 'WO-2846',
    title: 'Meter Reading Inspection',
    type: 'inspection',
    description: 'Customer complaint about high bill. Verify meter accuracy and check for leaks.',
    location: 'House 78, Twin Palm Road, Kabulonga',
    dma: 'Kabulonga',
    lat: -15.398,
    lng: 28.317,
    priority: 'low',
    status: 'completed',
    createdAt: '2026-01-17T09:00:00',
    scheduledDate: '2026-01-18',
    assignedTo: 'Grace Banda',
    assignedTeam: 'Team Beta',
    estimatedDuration: 1,
    actualDuration: 1.5,
    materials: [],
    notes: ['Meter tested - accurate', 'Found small leak in customer pipe', 'Customer advised to repair'],
    photos: [],
    customerContact: 'Joseph Mumba',
    customerPhone: '+260 96 789 0123',
    leakId: null,
    completedAt: '2026-01-18T11:30:00'
  },
];

const technicians: Technician[] = [
  { id: 'T001', name: 'John Mwale', phone: '+260 97 111 2222', team: 'Team Alpha', status: 'busy', currentLocation: 'Matero', activeOrders: 1, skills: ['Pipe Repair', 'Leak Detection', 'Welding'] },
  { id: 'T002', name: 'Grace Banda', phone: '+260 96 333 4444', team: 'Team Beta', status: 'busy', currentLocation: 'Kabulonga', activeOrders: 1, skills: ['Meter Installation', 'Inspection', 'Customer Service'] },
  { id: 'T003', name: 'Moses Phiri', phone: '+260 95 555 6666', team: 'Team Alpha', status: 'busy', currentLocation: 'Chilenje', activeOrders: 1, skills: ['Emergency Repair', 'Heavy Machinery', 'HDPE Welding'] },
  { id: 'T004', name: 'Mary Tembo', phone: '+260 97 777 8888', team: 'Team Beta', status: 'available', currentLocation: 'Depot', activeOrders: 0, skills: ['Valve Maintenance', 'Inspection', 'Water Quality'] },
  { id: 'T005', name: 'David Sakala', phone: '+260 96 999 0000', team: 'Team Charlie', status: 'available', currentLocation: 'Depot', activeOrders: 0, skills: ['Pipe Repair', 'Meter Installation', 'GIS Mapping'] },
];

export default function WorkOrdersPage() {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>(initialWorkOrders);
  const [selectedOrder, setSelectedOrder] = useState<WorkOrder | null>(null);
  const [filter, setFilter] = useState<WorkOrderStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Real-time updates simulation
  const updateRealTime = useCallback(() => {
    setWorkOrders(prev => prev.map(wo => {
      if (wo.status === 'in-progress' && wo.actualDuration === null) {
        // Simulate progress
        const startTime = new Date(wo.createdAt).getTime();
        const elapsed = (Date.now() - startTime) / (1000 * 60 * 60);
        return { ...wo, notes: [...wo.notes.slice(0, 2), `Progress: ${Math.min(100, Math.round(elapsed / wo.estimatedDuration * 100))}%`] };
      }
      return wo;
    }));
    setLastUpdate(new Date());
  }, []);

  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(updateRealTime, 10000);
    return () => clearInterval(interval);
  }, [isLive, updateRealTime]);

  const filteredOrders = workOrders
    .filter(wo => filter === 'all' || wo.status === filter)
    .filter(wo => 
      wo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wo.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wo.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

  const stats = {
    total: workOrders.length,
    pending: workOrders.filter(wo => wo.status === 'pending').length,
    assigned: workOrders.filter(wo => wo.status === 'assigned').length,
    inProgress: workOrders.filter(wo => wo.status === 'in-progress').length,
    completed: workOrders.filter(wo => wo.status === 'completed').length,
    critical: workOrders.filter(wo => wo.priority === 'critical' && wo.status !== 'completed').length,
  };

  const getStatusColor = (status: WorkOrderStatus) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-700';
      case 'assigned': return 'bg-blue-100 text-blue-700';
      case 'in-progress': return 'bg-amber-100 text-amber-700';
      case 'completed': return 'bg-green-100 text-green-700';
      case 'cancelled': return 'bg-red-100 text-red-700';
    }
  };

  const getPriorityColor = (priority: Priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-amber-500 text-white';
      case 'low': return 'bg-blue-500 text-white';
    }
  };

  const getTypeIcon = (type: WorkOrder['type']) => {
    switch (type) {
      case 'leak_repair': return AlertTriangle;
      case 'meter_install': case 'meter_replace': return Plus;
      case 'pipe_repair': return Wrench;
      case 'valve_maintenance': return Wrench;
      case 'inspection': return FileText;
    }
  };

  const updateOrderStatus = (orderId: string, newStatus: WorkOrderStatus) => {
    setWorkOrders(prev => prev.map(wo => 
      wo.id === orderId 
        ? { ...wo, status: newStatus, completedAt: newStatus === 'completed' ? new Date().toISOString() : wo.completedAt }
        : wo
    ));
    if (selectedOrder?.id === orderId) {
      setSelectedOrder(prev => prev ? { ...prev, status: newStatus } : null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 lg:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Wrench className="w-7 h-7 text-[#198038]" />
              Work Order Management
            </h1>
            <p className="text-sm text-gray-500 mt-1">Manage field operations and maintenance tasks</p>
          </div>
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${isLive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
              {isLive ? (
                <>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                  <span className="text-xs font-medium">LIVE</span>
                </>
              ) : (
                <span className="text-xs font-medium">Paused</span>
              )}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e]"
            >
              <Plus className="w-4 h-4" />
              New Work Order
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {[
          { label: 'Total Orders', value: stats.total, color: 'bg-gray-500' },
          { label: 'Pending', value: stats.pending, color: 'bg-gray-400' },
          { label: 'Assigned', value: stats.assigned, color: 'bg-blue-500' },
          { label: 'In Progress', value: stats.inProgress, color: 'bg-amber-500' },
          { label: 'Completed', value: stats.completed, color: 'bg-green-500' },
          { label: 'Critical', value: stats.critical, color: 'bg-red-500' },
        ].map((stat, i) => (
          <div key={i} className="bg-white rounded-xl p-4 shadow-sm border">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-3 h-3 rounded-full ${stat.color}`} />
              <span className="text-xs text-gray-500">{stat.label}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Work Orders List */}
        <div className="lg:col-span-2 space-y-4">
          {/* Filters */}
          <div className="bg-white rounded-xl p-4 shadow-sm border">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search work orders..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038]"
                />
              </div>
              <div className="flex gap-2 overflow-x-auto">
                {['all', 'pending', 'assigned', 'in-progress', 'completed'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setFilter(status as any)}
                    className={`px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                      filter === status ? 'bg-[#198038] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {status === 'all' ? 'All' : status.replace('-', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Orders List */}
          <div className="space-y-3">
            {filteredOrders.map((order) => {
              const TypeIcon = getTypeIcon(order.type);
              return (
                <div
                  key={order.id}
                  onClick={() => setSelectedOrder(order)}
                  className={`bg-white rounded-xl p-4 shadow-sm border cursor-pointer transition-all hover:shadow-md ${
                    selectedOrder?.id === order.id ? 'ring-2 ring-[#198038]' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        order.priority === 'critical' ? 'bg-red-100' :
                        order.priority === 'high' ? 'bg-orange-100' :
                        order.priority === 'medium' ? 'bg-amber-100' : 'bg-blue-100'
                      }`}>
                        <TypeIcon className={`w-5 h-5 ${
                          order.priority === 'critical' ? 'text-red-600' :
                          order.priority === 'high' ? 'text-orange-600' :
                          order.priority === 'medium' ? 'text-amber-600' : 'text-blue-600'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-gray-500">{order.id}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getPriorityColor(order.priority)}`}>
                            {order.priority.toUpperCase()}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getStatusColor(order.status)}`}>
                            {order.status.replace('-', ' ')}
                          </span>
                        </div>
                        <h3 className="font-semibold text-gray-900 mt-1">{order.title}</h3>
                        <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                          <MapPin className="w-3 h-3" />
                          {order.location}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </div>
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    {order.assignedTo && (
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {order.assignedTo}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {order.scheduledDate}
                    </span>
                    <span className="flex items-center gap-1">
                      <Timer className="w-3 h-3" />
                      {order.estimatedDuration}h est.
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selectedOrder ? (
            <>
              <div className="bg-white rounded-xl p-5 shadow-sm border">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-mono text-gray-500">{selectedOrder.id}</span>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(selectedOrder.priority)}`}>
                      {selectedOrder.priority}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedOrder.status)}`}>
                      {selectedOrder.status.replace('-', ' ')}
                    </span>
                  </div>
                </div>
                
                <h2 className="text-lg font-bold text-gray-900">{selectedOrder.title}</h2>
                <p className="text-sm text-gray-600 mt-2">{selectedOrder.description}</p>

                <div className="mt-4 space-y-3">
                  <div className="flex items-start gap-2">
                    <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-900">{selectedOrder.location}</p>
                      <p className="text-xs text-gray-500">DMA: {selectedOrder.dma}</p>
                    </div>
                  </div>
                  
                  {selectedOrder.assignedTo && (
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-900">{selectedOrder.assignedTo}</p>
                        <p className="text-xs text-gray-500">{selectedOrder.assignedTeam}</p>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <p className="text-sm text-gray-900">Scheduled: {selectedOrder.scheduledDate}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Timer className="w-4 h-4 text-gray-400" />
                    <p className="text-sm text-gray-900">
                      Est. Duration: {selectedOrder.estimatedDuration}h
                      {selectedOrder.actualDuration && ` (Actual: ${selectedOrder.actualDuration}h)`}
                    </p>
                  </div>

                  {selectedOrder.customerContact && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm text-gray-900">{selectedOrder.customerContact}</p>
                        {selectedOrder.customerPhone && (
                          <p className="text-xs text-gray-500">{selectedOrder.customerPhone}</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 mt-5">
                  {selectedOrder.status === 'pending' && (
                    <button
                      onClick={() => setShowAssignModal(true)}
                      className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
                    >
                      Assign Crew
                    </button>
                  )}
                  {selectedOrder.status === 'assigned' && (
                    <button
                      onClick={() => updateOrderStatus(selectedOrder.id, 'in-progress')}
                      className="flex-1 py-2 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 flex items-center justify-center gap-1"
                    >
                      <Play className="w-4 h-4" />
                      Start Work
                    </button>
                  )}
                  {selectedOrder.status === 'in-progress' && (
                    <button
                      onClick={() => updateOrderStatus(selectedOrder.id, 'completed')}
                      className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 flex items-center justify-center gap-1"
                    >
                      <Check className="w-4 h-4" />
                      Complete
                    </button>
                  )}
                  <button className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50">
                    <Navigation className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Materials */}
              {selectedOrder.materials.length > 0 && (
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <h3 className="font-semibold text-gray-900 mb-3">Materials Required</h3>
                  <div className="space-y-2">
                    {selectedOrder.materials.map((mat, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                        <span className="text-sm text-gray-700">{mat.item}</span>
                        <span className="text-sm font-medium text-gray-900">
                          {mat.used}/{mat.quantity}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {selectedOrder.notes.length > 0 && (
                <div className="bg-white rounded-xl p-5 shadow-sm border">
                  <h3 className="font-semibold text-gray-900 mb-3">Progress Notes</h3>
                  <div className="space-y-2">
                    {selectedOrder.notes.map((note, i) => (
                      <div key={i} className="p-2 bg-blue-50 rounded-lg text-sm text-blue-700">
                        {note}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-xl p-8 shadow-sm border text-center">
              <Wrench className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">Select a work order to view details</p>
            </div>
          )}

          {/* Available Technicians */}
          <div className="bg-white rounded-xl p-5 shadow-sm border">
            <h3 className="font-semibold text-gray-900 mb-3">Field Technicians</h3>
            <div className="space-y-2">
              {technicians.map((tech) => (
                <div key={tech.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      tech.status === 'available' ? 'bg-green-500' :
                      tech.status === 'busy' ? 'bg-amber-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{tech.name}</p>
                      <p className="text-xs text-gray-500">{tech.team}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    tech.status === 'available' ? 'bg-green-100 text-green-700' :
                    tech.status === 'busy' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {tech.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Create Work Order Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Work Order</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input type="text" className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]">
                  <option>Leak Repair</option>
                  <option>Meter Installation</option>
                  <option>Meter Replacement</option>
                  <option>Pipe Repair</option>
                  <option>Valve Maintenance</option>
                  <option>Inspection</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                <select className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]">
                  <option>Critical</option>
                  <option>High</option>
                  <option>Medium</option>
                  <option>Low</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input type="text" className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea rows={3} className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Date</label>
                <input type="date" className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#198038]" />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCreateModal(false)} className="flex-1 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">
                Cancel
              </button>
              <button onClick={() => setShowCreateModal(false)} className="flex-1 py-2 bg-[#198038] text-white rounded-lg font-medium hover:bg-[#166a2e]">
                Create Order
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Modal */}
      {showAssignModal && selectedOrder && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Assign Crew</h2>
            <p className="text-sm text-gray-600 mb-4">Select a technician for {selectedOrder.id}</p>
            <div className="space-y-2">
              {technicians.filter(t => t.status === 'available').map((tech) => (
                <button
                  key={tech.id}
                  onClick={() => {
                    updateOrderStatus(selectedOrder.id, 'assigned');
                    setShowAssignModal(false);
                  }}
                  className="w-full flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div>
                    <p className="font-medium text-gray-900">{tech.name}</p>
                    <p className="text-xs text-gray-500">{tech.skills.join(', ')}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </button>
              ))}
            </div>
            <button onClick={() => setShowAssignModal(false)} className="w-full mt-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
