'use client';

/**
 * AquaWatch Smart Meters Dashboard
 * =================================
 * Production AMI Dashboard - NO FAKE DATA
 * Shows real meter data ONLY when connected to AMI Gateway
 */

import React, { useState, useMemo } from 'react';
import { 
  Gauge, Activity, AlertTriangle, Battery, Signal, Droplets,
  TrendingUp, TrendingDown, Clock, MapPin, Wifi, WifiOff,
  Zap, ThermometerSun, Moon, Sun, RefreshCw, Bell,
  Home, Building2, Factory, ArrowUpRight, ArrowDownRight,
  Search, Filter, Download, MoreVertical, Eye, Settings,
  Power, PowerOff, Loader2, AlertCircle, CheckCircle2,
  Radio, X
} from 'lucide-react';
import { useSmartMeters } from '@/hooks/useSmartMeters';
import { 
  SmartMeter, 
  DMABalance, 
  MeterAlert,
  MeterType, 
  MeterStatus,
  getStatusColor, 
  getMeterTypeDisplay,
  formatFlowRate,
  formatReading,
  getConnectionQualityDisplay
} from '@/lib/smart-meters-service';

export default function SmartMetersPage() {
  const {
    isConnected,
    connectionQuality,
    isConnecting,
    meters,
    dmas,
    stats,
    alerts,
    connect,
    disconnect,
    refresh,
    isLoading,
    error,
    lastUpdate
  } = useSmartMeters();
  
  const [selectedMeter, setSelectedMeter] = useState<SmartMeter | null>(null);
  const [selectedDMA, setSelectedDMA] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showMeterModal, setShowMeterModal] = useState(false);
  
  // Filter meters
  const filteredMeters = useMemo(() => {
    return meters.filter(meter => {
      const matchesDMA = selectedDMA === 'all' || meter.dma === selectedDMA;
      const matchesType = selectedType === 'all' || meter.type === selectedType;
      const matchesSearch = searchTerm === '' || 
        meter.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        meter.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        meter.serialNumber.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesDMA && matchesType && matchesSearch;
    });
  }, [meters, selectedDMA, selectedType, searchTerm]);
  
  // Get unique DMAs for filter
  const uniqueDMAs = useMemo(() => {
    return [...new Set(meters.map(m => m.dma))];
  }, [meters]);
  
  const connectionDisplay = getConnectionQualityDisplay(connectionQuality);
  
  const getMeterIcon = (type: MeterType) => {
    switch (type) {
      case 'residential': return <Home className="w-4 h-4" />;
      case 'commercial': return <Building2 className="w-4 h-4" />;
      case 'industrial': return <Factory className="w-4 h-4" />;
      case 'dma_inlet': return <ArrowDownRight className="w-4 h-4" />;
      case 'dma_outlet': return <ArrowUpRight className="w-4 h-4" />;
    }
  };
  
  const getStatusBadge = (status: MeterStatus, connected: boolean) => {
    if (!connected) {
      return (
        <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-gray-600/50 text-gray-400">
          <WifiOff className="w-3 h-3" />
          No Data
        </span>
      );
    }
    
    const colors: Record<MeterStatus, string> = {
      'online': 'bg-green-500/20 text-green-400',
      'warning': 'bg-yellow-500/20 text-yellow-400',
      'critical': 'bg-red-500/20 text-red-400',
      'offline': 'bg-gray-500/20 text-gray-400',
      'disconnected': 'bg-gray-600/20 text-gray-500'
    };
    
    return (
      <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${colors[status]}`}>
        <span className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'high': return 'text-orange-400 bg-orange-500/20 border-orange-500/30';
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-500/30';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/30';
    }
  };
  
  // Render disconnected state
  const renderDisconnectedOverlay = () => (
    <div className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-800 rounded-2xl p-8 max-w-md mx-4 border border-gray-700 text-center">
        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gray-700 flex items-center justify-center">
          <WifiOff className="w-10 h-10 text-gray-400" />
        </div>
        <h2 className="text-2xl font-bold mb-2">AMI Gateway Disconnected</h2>
        <p className="text-gray-400 mb-6">
          Connect to the Advanced Metering Infrastructure gateway to view real-time meter data. 
          No data will be shown until connected.
        </p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}
        
        <button
          onClick={connect}
          disabled={isConnecting}
          className="w-full py-3 px-6 bg-[#198038] hover:bg-[#166a2e] disabled:bg-gray-600 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
        >
          {isConnecting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Connecting to AMI Gateway...
            </>
          ) : (
            <>
              <Power className="w-5 h-5" />
              Connect to AMI Gateway
            </>
          )}
        </button>
        
        <p className="text-xs text-gray-500 mt-4">
          This connects to LWSC's smart meter infrastructure for live data
        </p>
      </div>
    </div>
  );
  
  // Render meter detail modal
  const renderMeterModal = () => {
    if (!showMeterModal || !selectedMeter) return null;
    
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-700">
          <div className="p-6 border-b border-gray-700 flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                {getMeterIcon(selectedMeter.type)}
                {selectedMeter.customerName}
              </h2>
              <p className="text-sm text-gray-400 mt-1">{selectedMeter.address}</p>
            </div>
            <button
              onClick={() => setShowMeterModal(false)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="p-6">
            {!selectedMeter.connected ? (
              <div className="text-center py-8">
                <WifiOff className="w-12 h-12 mx-auto text-gray-500 mb-3" />
                <p className="text-gray-400">Meter not connected</p>
                <p className="text-sm text-gray-500 mt-1">
                  Last seen: {selectedMeter.lastConnected 
                    ? new Date(selectedMeter.lastConnected).toLocaleString() 
                    : 'Never'}
                </p>
              </div>
            ) : (
              <>
                {/* Meter Info Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 mb-1">Current Reading</div>
                    <div className="text-lg font-bold">{formatReading(selectedMeter.currentReading)}</div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 mb-1">Flow Rate</div>
                    <div className="text-lg font-bold text-blue-400">{formatFlowRate(selectedMeter.flowRate)}</div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 mb-1">Battery</div>
                    <div className="text-lg font-bold flex items-center gap-1">
                      <Battery className={`w-4 h-4 ${(selectedMeter.batteryLevel || 0) < 20 ? 'text-red-400' : 'text-green-400'}`} />
                      {selectedMeter.batteryLevel !== null ? `${Math.round(selectedMeter.batteryLevel)}%` : '--'}
                    </div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-3">
                    <div className="text-xs text-gray-400 mb-1">Signal</div>
                    <div className="text-lg font-bold flex items-center gap-1">
                      <Signal className="w-4 h-4" />
                      {selectedMeter.signalStrength !== null ? `${Math.round(selectedMeter.signalStrength)}%` : '--'}
                    </div>
                  </div>
                </div>
                
                {/* Usage Stats */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-400">Daily Usage</span>
                      <TrendingUp className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="text-2xl font-bold">
                      {selectedMeter.dailyUsage !== null ? `${selectedMeter.dailyUsage.toFixed(2)} m³` : '-- m³'}
                    </div>
                  </div>
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-400">Monthly Usage</span>
                      <Activity className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="text-2xl font-bold">
                      {selectedMeter.monthlyUsage !== null ? `${selectedMeter.monthlyUsage.toFixed(1)} m³` : '-- m³'}
                    </div>
                  </div>
                </div>
                
                {/* Hourly Chart */}
                {selectedMeter.hourlyData && (
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <h3 className="text-sm font-semibold mb-3">24-Hour Flow Pattern</h3>
                    <div className="flex items-end gap-1 h-24">
                      {selectedMeter.hourlyData.map((value, i) => {
                        const max = Math.max(...(selectedMeter.hourlyData || [1]));
                        const height = max > 0 ? (value / max) * 100 : 0;
                        return (
                          <div
                            key={i}
                            className="flex-1 bg-[#198038]/60 hover:bg-[#198038] rounded-t transition-colors"
                            style={{ height: `${height}%` }}
                            title={`${i}:00 - ${value} L/h`}
                          />
                        );
                      })}
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>00:00</span>
                      <span>06:00</span>
                      <span>12:00</span>
                      <span>18:00</span>
                      <span>24:00</span>
                    </div>
                  </div>
                )}
                
                {/* Meter Details */}
                <div className="mt-6 pt-6 border-t border-gray-700">
                  <h3 className="text-sm font-semibold mb-3">Meter Details</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-gray-400">Serial Number</div>
                    <div>{selectedMeter.serialNumber}</div>
                    <div className="text-gray-400">Type</div>
                    <div>{getMeterTypeDisplay(selectedMeter.type)}</div>
                    <div className="text-gray-400">DMA</div>
                    <div>{selectedMeter.dma}</div>
                    <div className="text-gray-400">Last Update</div>
                    <div>{selectedMeter.lastUpdate ? new Date(selectedMeter.lastUpdate).toLocaleString() : 'Never'}</div>
                    <div className="text-gray-400">Location</div>
                    <div>{selectedMeter.lat.toFixed(4)}, {selectedMeter.lng.toFixed(4)}</div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Disconnected Overlay */}
      {!isConnected && !isLoading && renderDisconnectedOverlay()}
      
      {/* Meter Modal */}
      {renderMeterModal()}
      
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gauge className="w-8 h-8 text-[#198038]" />
            Smart Meters Dashboard
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Advanced Metering Infrastructure (AMI) Monitoring
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
            isConnected ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'
          }`}>
            {isConnected ? (
              <>
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-sm font-medium">CONNECTED</span>
                <span className={`text-xs ${connectionDisplay.color}`}>({connectionDisplay.label})</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4" />
                <span className="text-sm">Disconnected</span>
              </>
            )}
          </div>
          
          {/* Connect/Disconnect Button */}
          <button
            onClick={isConnected ? disconnect : connect}
            disabled={isConnecting}
            className={`p-2 rounded-lg transition-colors ${
              isConnected 
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' 
                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
            }`}
            title={isConnected ? 'Disconnect from AMI' : 'Connect to AMI'}
          >
            {isConnecting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isConnected ? (
              <PowerOff className="w-5 h-5" />
            ) : (
              <Power className="w-5 h-5" />
            )}
          </button>
          
          {/* Refresh Button */}
          <button
            onClick={refresh}
            disabled={!isConnected || isLoading}
            className="p-2 bg-[#198038] rounded-lg hover:bg-[#166a2e] disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
            title="Refresh data"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          {/* Last Update */}
          {lastUpdate && (
            <div className="text-sm text-gray-400">
              <Clock className="w-4 h-4 inline mr-1" />
              {lastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-xs mb-1">Total Meters</div>
          <div className="text-2xl font-bold">{stats?.totalMeters ?? meters.length}</div>
          <div className="text-[#198038] text-xs">Registered</div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-green-500/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Connected</div>
          <div className="text-2xl font-bold text-green-400">
            {isConnected ? stats?.connectedMeters ?? 0 : '--'}
          </div>
          <div className="text-green-400 text-xs">
            {isConnected && stats ? `${((stats.connectedMeters / stats.totalMeters) * 100).toFixed(0)}% Active` : 'Connect to view'}
          </div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-yellow-500/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Warnings</div>
          <div className="text-2xl font-bold text-yellow-400">
            {isConnected ? stats?.warningMeters ?? 0 : '--'}
          </div>
          <div className="text-yellow-400 text-xs">Need Attention</div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-red-500/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Critical/Offline</div>
          <div className="text-2xl font-bold text-red-400">
            {isConnected ? (stats?.criticalMeters ?? 0) + (stats?.offlineMeters ?? 0) : '--'}
          </div>
          <div className="text-red-400 text-xs">Immediate Action</div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-blue-500/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Total Flow</div>
          <div className="text-2xl font-bold text-blue-400">
            {isConnected && stats?.totalFlow !== null ? (stats.totalFlow / 1000).toFixed(1) : '--'}
          </div>
          <div className="text-blue-400 text-xs">m³/hour</div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-purple-500/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Daily Usage</div>
          <div className="text-2xl font-bold text-purple-400">
            {isConnected && stats?.totalDailyUsage !== null ? stats.totalDailyUsage.toFixed(0) : '--'}
          </div>
          <div className="text-purple-400 text-xs">m³ today</div>
        </div>
        
        <div className={`bg-gray-800 rounded-xl p-4 border ${isConnected ? 'border-[#EF7D00]/30' : 'border-gray-700'}`}>
          <div className="text-gray-400 text-xs mb-1">Avg NRW</div>
          <div className="text-2xl font-bold text-[#EF7D00]">
            {isConnected && stats?.avgNRW !== null ? `${stats.avgNRW.toFixed(1)}%` : '--%'}
          </div>
          <div className="text-[#EF7D00] text-xs">Network Loss</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column - DMA Overview & Alerts */}
        <div className="space-y-6">
          {/* DMA Water Balance */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Droplets className="w-5 h-5 text-[#198038]" />
              DMA Water Balance
            </h2>
            <div className="space-y-3">
              {!isConnected ? (
                <div className="text-center py-8 text-gray-400">
                  <WifiOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Connect to view DMA data</p>
                </div>
              ) : dmas.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No DMA data available</p>
                </div>
              ) : (
                dmas.map(dma => (
                  <div 
                    key={dma.id}
                    className={`p-3 rounded-lg border ${
                      dma.status === 'unknown' ? 'bg-gray-700/50 border-gray-600' :
                      dma.status === 'good' ? 'bg-green-500/10 border-green-500/30' :
                      dma.status === 'concern' ? 'bg-yellow-500/10 border-yellow-500/30' :
                      'bg-red-500/10 border-red-500/30'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-medium">{dma.name}</div>
                        <div className="text-xs text-gray-400">
                          {dma.connectedMeters}/{dma.meterCount} meters connected
                        </div>
                      </div>
                      <div className={`text-lg font-bold ${
                        dma.status === 'unknown' ? 'text-gray-400' :
                        dma.status === 'good' ? 'text-green-400' :
                        dma.status === 'concern' ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {dma.nrwPercentage !== null ? `${dma.nrwPercentage.toFixed(1)}%` : '--%'}
                      </div>
                    </div>
                    {dma.nrwPercentage !== null && (
                      <>
                        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ${
                              dma.status === 'good' ? 'bg-green-500' :
                              dma.status === 'concern' ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(100, dma.nrwPercentage * 2)}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                          <span>Input: {dma.totalInput?.toFixed(0) ?? '--'} m³/day</span>
                          <span>Billed: {dma.billedConsumption?.toFixed(0) ?? '--'} m³/day</span>
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-red-400" />
              Active Alerts
              {isConnected && alerts.length > 0 && (
                <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                  {alerts.length}
                </span>
              )}
            </h2>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {!isConnected ? (
                <div className="text-center text-gray-400 py-4">
                  <WifiOff className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Connect to view alerts</p>
                </div>
              ) : alerts.length === 0 ? (
                <div className="text-center text-gray-400 py-4">
                  <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-green-400 opacity-50" />
                  <p>No active alerts</p>
                </div>
              ) : (
                alerts.slice(0, 10).map((alert) => (
                  <div 
                    key={alert.id}
                    className={`p-3 rounded-lg border ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{alert.message}</div>
                        <div className="text-xs opacity-70 mt-0.5">
                          Meter: {alert.meterId} • {new Date(alert.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column - Meter List */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-xl border border-gray-700">
            {/* Filters */}
            <div className="p-4 border-b border-gray-700">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search meters..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm focus:outline-none focus:border-[#198038]"
                  />
                </div>
                <select
                  value={selectedDMA}
                  onChange={(e) => setSelectedDMA(e.target.value)}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm focus:outline-none focus:border-[#198038]"
                >
                  <option value="all">All DMAs</option>
                  {uniqueDMAs.map(dma => (
                    <option key={dma} value={dma}>{dma.replace('DMA_', '').replace('_', ' ')}</option>
                  ))}
                </select>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm focus:outline-none focus:border-[#198038]"
                >
                  <option value="all">All Types</option>
                  <option value="residential">Residential</option>
                  <option value="commercial">Commercial</option>
                  <option value="industrial">Industrial</option>
                  <option value="dma_inlet">DMA Inlet</option>
                  <option value="dma_outlet">DMA Outlet</option>
                </select>
              </div>
            </div>
            
            {/* Meter List */}
            <div className="divide-y divide-gray-700 max-h-[600px] overflow-y-auto">
              {filteredMeters.length === 0 ? (
                <div className="p-8 text-center text-gray-400">
                  <Gauge className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No meters found</p>
                </div>
              ) : (
                filteredMeters.map(meter => (
                  <div 
                    key={meter.id}
                    onClick={() => {
                      setSelectedMeter(meter);
                      setShowMeterModal(true);
                    }}
                    className="p-4 hover:bg-gray-700/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${
                          meter.connected ? 'bg-[#198038]/20 text-[#198038]' : 'bg-gray-700 text-gray-500'
                        }`}>
                          {getMeterIcon(meter.type)}
                        </div>
                        <div>
                          <div className="font-medium flex items-center gap-2">
                            {meter.customerName}
                            {getStatusBadge(meter.status, meter.connected)}
                          </div>
                          <div className="text-sm text-gray-400">{meter.address}</div>
                          <div className="text-xs text-gray-500 mt-1">
                            {meter.serialNumber} • {meter.dma.replace('DMA_', '')}
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        {meter.connected ? (
                          <>
                            <div className="text-lg font-bold text-blue-400">
                              {formatFlowRate(meter.flowRate)}
                            </div>
                            <div className="flex items-center justify-end gap-3 mt-1 text-xs text-gray-400">
                              <span className="flex items-center gap-1">
                                <Battery className={`w-3 h-3 ${(meter.batteryLevel || 0) < 20 ? 'text-red-400' : ''}`} />
                                {meter.batteryLevel !== null ? `${Math.round(meter.batteryLevel)}%` : '--'}
                              </span>
                              <span className="flex items-center gap-1">
                                <Signal className="w-3 h-3" />
                                {meter.signalStrength !== null ? `${Math.round(meter.signalStrength)}%` : '--'}
                              </span>
                            </div>
                          </>
                        ) : (
                          <div className="text-gray-500 text-sm">
                            <WifiOff className="w-4 h-4 mx-auto mb-1" />
                            No Data
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
