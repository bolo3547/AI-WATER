'use client';

import React, { useState, useEffect } from 'react';
import useSWR from 'swr';
import { 
  FileText, Clock, User, Users, CheckCircle, AlertTriangle,
  ChevronRight, Calendar, MapPin, Droplets, Wrench, AlertCircle,
  MessageSquare, Send, Download, Plus, CheckSquare, Square, Edit,
  Loader2
} from 'lucide-react';

const fetcher = (url: string) => fetch(url).then(res => res.json());

interface ShiftHandover {
  id: string;
  shiftType: 'day' | 'night';
  date: string;
  startTime: string;
  endTime: string;
  outgoingOperator: string;
  incomingOperator: string | null;
  status: 'in-progress' | 'pending-review' | 'completed';
  systemStatus: {
    pumpsOperational: number;
    pumpsTotal: number;
    reservoirLevels: { name: string; level: number }[];
    activeAlerts: number;
    activeLeaks: number;
    ongoingWorks: number;
  };
  checklist: { item: string; checked: boolean; notes: string }[];
  incidents: { time: string; description: string; action: string; resolved: boolean }[];
  notes: string;
  criticalItems: string[];
  pendingTasks: { task: string; priority: 'high' | 'medium' | 'low' }[];
  submittedAt: string | null;
  acknowledgedAt: string | null;
}

const shiftChecklist = [
  'All pump stations operational and remote monitored',
  'Reservoir levels within normal range (60-85%)',
  'SCADA system functioning normally',
  'All DMA meters transmitting data',
  'Control room equipment functional',
  'Emergency contact list updated',
  'Vehicle inspection completed',
  'Safety equipment checked',
  'Logbook entries up to date',
  'Chemical stock levels adequate',
];

export default function ShiftHandoverPage() {
  // Fetch real data from API
  const { data: handoverData, error, isLoading, mutate } = useSWR('/api/shift-handover', fetcher, {
    refreshInterval: 30000
  });

  const [selectedHandover, setSelectedHandover] = useState<ShiftHandover | null>(null);
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current');

  // Extract data from API
  const handovers: ShiftHandover[] = handoverData?.data?.handovers || [];
  const currentSystemStatus = handoverData?.data?.currentSystemStatus;

  // Set initial selection when data loads
  useEffect(() => {
    if (handovers.length > 0 && !selectedHandover) {
      const current = handovers.find(h => h.status === 'in-progress') || handovers[0];
      setSelectedHandover(current);
    }
  }, [handovers, selectedHandover]);

  const currentShift = handovers.find(h => h.status === 'in-progress');

  // API action helper
  const handleApiAction = async (action: string, data?: any) => {
    try {
      const response = await fetch('/api/shift-handover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...data })
      });
      if (response.ok) {
        mutate(); // Refresh data
      }
    } catch (error) {
      console.error('Action failed:', error);
    }
  };

  const updateChecklist = async (index: number, checked: boolean) => {
    if (!selectedHandover || selectedHandover.status !== 'in-progress') return;
    
    const newChecklist = [...selectedHandover.checklist];
    newChecklist[index] = { ...newChecklist[index], checked };
    
    await handleApiAction('update', {
      handoverId: selectedHandover.id,
      updates: { checklist: newChecklist }
    });
    
    setSelectedHandover(prev => prev ? { ...prev, checklist: newChecklist } : prev);
  };

  const updateNotes = async (notes: string) => {
    if (!selectedHandover || selectedHandover.status !== 'in-progress') return;
    
    await handleApiAction('update', {
      handoverId: selectedHandover.id,
      updates: { notes }
    });
    
    setSelectedHandover(prev => prev ? { ...prev, notes } : prev);
  };

  const addIncident = async () => {
    if (!selectedHandover || selectedHandover.status !== 'in-progress') return;
    
    const newIncident = {
      time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
      description: '',
      action: '',
      resolved: false
    };
    
    await handleApiAction('add_incident', {
      handoverId: selectedHandover.id,
      incident: newIncident
    });
    
    setSelectedHandover(prev => 
      prev ? { ...prev, incidents: [...prev.incidents, newIncident] } : prev
    );
  };

  const submitHandover = async () => {
    if (!selectedHandover) return;
    
    await handleApiAction('submit', {
      handoverId: selectedHandover.id
    });
    
    setSelectedHandover(prev => 
      prev ? { ...prev, status: 'pending-review', submittedAt: new Date().toISOString() } : prev
    );
  };

  const completedCount = selectedHandover?.checklist.filter(c => c.checked).length || 0;
  const totalCount = selectedHandover?.checklist.length || 0;

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[#198038] mx-auto mb-4" />
          <p className="text-gray-600">Loading shift handover data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
          <p className="text-gray-800 font-medium">Failed to load shift data</p>
          <button 
            onClick={() => mutate()}
            className="mt-4 px-4 py-2 bg-[#198038] text-white rounded-lg text-sm hover:bg-[#166a2e]"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4 lg:p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <FileText className="w-7 h-7 text-[#198038]" />
              Shift Handover
            </h1>
            <p className="text-sm text-gray-500 mt-1">Digital shift reports and handover documentation</p>
          </div>
          {currentShift && (
            <div className="flex items-center gap-3">
              <div className="bg-green-100 text-green-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                {currentShift.shiftType === 'day' ? 'Day' : 'Night'} Shift Active
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('current')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'current' ? 'bg-[#198038] text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          Current Shift
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'history' ? 'bg-[#198038] text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
        >
          Shift History
        </button>
      </div>

      {activeTab === 'current' && selectedHandover && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-4">
            {/* Shift Info Card */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    selectedHandover.shiftType === 'day' 
                      ? 'bg-amber-100 text-amber-700' 
                      : 'bg-indigo-100 text-indigo-700'
                  }`}>
                    {selectedHandover.shiftType === 'day' ? '☀️ Day Shift' : '🌙 Night Shift'}
                  </span>
                  <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium ${
                    selectedHandover.status === 'in-progress' ? 'bg-green-100 text-green-700' :
                    selectedHandover.status === 'pending-review' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {selectedHandover.status.replace('-', ' ')}
                  </span>
                </div>
                <span className="text-sm text-gray-500">{selectedHandover.id}</span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Date</p>
                  <p className="font-medium text-gray-900">{selectedHandover.date}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Shift Time</p>
                  <p className="font-medium text-gray-900">{selectedHandover.startTime} - {selectedHandover.endTime}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Outgoing Operator</p>
                  <p className="font-medium text-gray-900">{selectedHandover.outgoingOperator}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Incoming Operator</p>
                  <p className="font-medium text-gray-900">{selectedHandover.incomingOperator || 'TBD'}</p>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <h2 className="font-semibold text-gray-900 mb-4">System Status at Handover</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Wrench className="w-4 h-4" />
                    Pumps
                  </div>
                  <p className="text-xl font-bold text-gray-900">
                    {selectedHandover.systemStatus.pumpsOperational}/{selectedHandover.systemStatus.pumpsTotal}
                    <span className="text-sm font-normal text-gray-500 ml-1">operational</span>
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <AlertTriangle className="w-4 h-4" />
                    Active Alerts
                  </div>
                  <p className="text-xl font-bold text-amber-600">{selectedHandover.systemStatus.activeAlerts}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Droplets className="w-4 h-4" />
                    Active Leaks
                  </div>
                  <p className="text-xl font-bold text-red-600">{selectedHandover.systemStatus.activeLeaks}</p>
                </div>
              </div>

              {/* Reservoir Levels */}
              <div className="mt-4">
                <p className="text-sm text-gray-500 mb-2">Reservoir Levels</p>
                <div className="space-y-2">
                  {selectedHandover.systemStatus.reservoirLevels.map((res, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-sm text-gray-700 w-24">{res.name}</span>
                      <div className="flex-1 h-4 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${res.level > 70 ? 'bg-green-500' : res.level > 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                          style={{ width: `${res.level}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-900 w-12">{res.level}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Handover Checklist */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">Handover Checklist</h2>
                <span className="text-sm text-gray-500">{completedCount}/{totalCount} completed</span>
              </div>
              <div className="space-y-2">
                {selectedHandover.checklist.map((item, i) => (
                  <div 
                    key={i}
                    onClick={() => updateChecklist(i, !item.checked)}
                    className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      item.checked ? 'bg-green-50' : 'bg-gray-50 hover:bg-gray-100'
                    } ${selectedHandover.status !== 'in-progress' ? 'cursor-default' : ''}`}
                  >
                    {item.checked ? (
                      <CheckSquare className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <Square className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={`text-sm ${item.checked ? 'text-green-800' : 'text-gray-700'}`}>{item.item}</p>
                      {item.notes && (
                        <p className="text-xs text-gray-500 mt-1">Note: {item.notes}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Incidents */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900">Incidents & Events</h2>
                {selectedHandover.status === 'in-progress' && (
                  <button 
                    onClick={addIncident}
                    className="text-sm text-[#198038] font-medium hover:underline flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    Add Incident
                  </button>
                )}
              </div>
              {selectedHandover.incidents.length > 0 ? (
                <div className="space-y-3">
                  {selectedHandover.incidents.map((incident, i) => (
                    <div key={i} className={`p-3 rounded-lg border ${incident.resolved ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs font-medium text-gray-500">{incident.time}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          incident.resolved ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {incident.resolved ? 'Resolved' : 'Open'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 font-medium">{incident.description || 'New incident...'}</p>
                      {incident.action && (
                        <p className="text-sm text-gray-600 mt-1">Action: {incident.action}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">No incidents reported this shift</p>
              )}
            </div>

            {/* Notes */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <h2 className="font-semibold text-gray-900 mb-4">General Notes</h2>
              <textarea
                value={selectedHandover.notes}
                onChange={(e) => updateNotes(e.target.value)}
                placeholder="Add shift notes, observations, and important information for incoming operator..."
                disabled={selectedHandover.status !== 'in-progress'}
                rows={4}
                className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#198038] disabled:bg-gray-50"
              />
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Actions */}
            {selectedHandover.status === 'in-progress' && (
              <div className="bg-white rounded-xl p-5 shadow-sm border">
                <h3 className="font-semibold text-gray-900 mb-4">Actions</h3>
                <div className="space-y-2">
                  <button 
                    onClick={submitHandover}
                    disabled={completedCount < totalCount}
                    className="w-full py-2.5 bg-[#198038] text-white rounded-lg text-sm font-medium hover:bg-[#166a2e] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Submit Handover
                  </button>
                  <button className="w-full py-2.5 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center justify-center gap-2">
                    <Download className="w-4 h-4" />
                    Export PDF
                  </button>
                </div>
                {completedCount < totalCount && (
                  <p className="text-xs text-amber-600 mt-2 text-center">
                    Complete all checklist items before submitting
                  </p>
                )}
              </div>
            )}

            {/* Critical Items */}
            {selectedHandover.criticalItems.length > 0 && (
              <div className="bg-red-50 rounded-xl p-5 border border-red-200">
                <h3 className="font-semibold text-red-800 flex items-center gap-2 mb-3">
                  <AlertCircle className="w-4 h-4" />
                  Critical Items
                </h3>
                <ul className="space-y-2">
                  {selectedHandover.criticalItems.map((item, i) => (
                    <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                      <span className="text-red-400">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Pending Tasks */}
            {selectedHandover.pendingTasks.length > 0 && (
              <div className="bg-white rounded-xl p-5 shadow-sm border">
                <h3 className="font-semibold text-gray-900 mb-3">Pending Tasks</h3>
                <ul className="space-y-2">
                  {selectedHandover.pendingTasks.map((task, i) => (
                    <li key={i} className="flex items-start gap-2 p-2 bg-gray-50 rounded-lg">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        task.priority === 'high' ? 'bg-red-100 text-red-700' :
                        task.priority === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {task.priority}
                      </span>
                      <span className="text-sm text-gray-700">{task.task}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quick Stats */}
            <div className="bg-white rounded-xl p-5 shadow-sm border">
              <h3 className="font-semibold text-gray-900 mb-3">Today's Summary</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Work Orders Completed</span>
                  <span className="font-medium text-gray-900">3</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Leaks Repaired</span>
                  <span className="font-medium text-gray-900">1</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Customer Complaints</span>
                  <span className="font-medium text-gray-900">2</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Meters Installed</span>
                  <span className="font-medium text-gray-900">5</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="divide-y">
            {handovers.filter(h => h.status === 'completed').map((handover) => (
              <div 
                key={handover.id}
                onClick={() => { setSelectedHandover(handover); setActiveTab('current'); }}
                className="p-4 hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      handover.shiftType === 'day' ? 'bg-amber-100' : 'bg-indigo-100'
                    }`}>
                      <span className="text-lg">{handover.shiftType === 'day' ? '☀️' : '🌙'}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{handover.date} - {handover.shiftType === 'day' ? 'Day' : 'Night'} Shift</p>
                      <p className="text-sm text-gray-500">{handover.outgoingOperator} → {handover.incomingOperator}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">Completed</span>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
                {handover.incidents.length > 0 && (
                  <p className="text-sm text-gray-500 mt-2 ml-14">
                    {handover.incidents.length} incident(s) reported
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
