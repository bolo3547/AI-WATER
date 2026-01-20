'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Gauge, Activity, AlertTriangle, Battery, Signal, Droplets,
  TrendingUp, TrendingDown, Clock, MapPin, Wifi, WifiOff,
  Zap, ThermometerSun, Moon, Sun, RefreshCw, Bell,
  Home, Building2, Factory, ArrowUpRight, ArrowDownRight,
  Search, Filter, Download, MoreVertical, Eye, Settings
} from 'lucide-react';

// Meter Types
type MeterType = 'residential' | 'commercial' | 'industrial' | 'dma_inlet' | 'dma_outlet';
type MeterStatus = 'online' | 'offline' | 'warning' | 'critical';

interface SmartMeter {
  id: string;
  serialNumber: string;
  customerName: string;
  address: string;
  type: MeterType;
  dma: string;
  lat: number;
  lng: number;
  status: MeterStatus;
  currentReading: number;
  flowRate: number;
  batteryLevel: number;
  signalStrength: number;
  lastUpdate: Date;
  dailyUsage: number;
  monthlyUsage: number;
  alerts: Alert[];
  hourlyData: number[];
}

interface Alert {
  id: string;
  type: 'high_consumption' | 'night_flow' | 'reverse_flow' | 'tamper' | 'leak' | 'battery_low' | 'offline';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
}

interface DMABalance {
  id: string;
  name: string;
  totalInput: number;
  totalOutput: number;
  billedConsumption: number;
  nrwPercentage: number;
  meterCount: number;
  status: 'good' | 'concern' | 'poor';
}

// Real Lusaka DMAs with smart meter data
const lusakaDMAs: DMABalance[] = [
  { id: 'DMA_CBD', name: 'CBD District', totalInput: 4500, totalOutput: 850, billedConsumption: 2920, nrwPercentage: 20.0, meterCount: 1200, status: 'good' },
  { id: 'DMA_KABULONGA', name: 'Kabulonga', totalInput: 3200, totalOutput: 400, billedConsumption: 2100, nrwPercentage: 25.0, meterCount: 800, status: 'concern' },
  { id: 'DMA_WOODLANDS', name: 'Woodlands', totalInput: 5100, totalOutput: 600, billedConsumption: 3150, nrwPercentage: 30.0, meterCount: 1500, status: 'concern' },
  { id: 'DMA_CHILENJE', name: 'Chilenje', totalInput: 3800, totalOutput: 300, billedConsumption: 2170, nrwPercentage: 38.0, meterCount: 2200, status: 'poor' },
  { id: 'DMA_MATERO', name: 'Matero', totalInput: 6200, totalOutput: 500, billedConsumption: 3420, nrwPercentage: 40.0, meterCount: 3000, status: 'poor' },
  { id: 'DMA_ROMA', name: 'Roma', totalInput: 2100, totalOutput: 200, billedConsumption: 1520, nrwPercentage: 20.0, meterCount: 450, status: 'good' },
];

// Generate realistic meter data
const generateMeters = (): SmartMeter[] => {
  const meters: SmartMeter[] = [
    // DMA Inlet Meters
    { id: 'DMA_IN_CBD', serialNumber: 'ZM-IN-001', customerName: 'LWSC CBD Inlet', address: 'Cairo Road Main Supply', type: 'dma_inlet', dma: 'DMA_CBD', lat: -15.4167, lng: 28.2833, status: 'online', currentReading: 458230, flowRate: 4500, batteryLevel: 100, signalStrength: 95, lastUpdate: new Date(), dailyUsage: 4500, monthlyUsage: 135000, alerts: [], hourlyData: [] },
    { id: 'DMA_IN_KAB', serialNumber: 'ZM-IN-002', customerName: 'LWSC Kabulonga Inlet', address: 'Great East Road Supply', type: 'dma_inlet', dma: 'DMA_KABULONGA', lat: -15.3958, lng: 28.3208, status: 'online', currentReading: 325680, flowRate: 3200, batteryLevel: 100, signalStrength: 92, lastUpdate: new Date(), dailyUsage: 3200, monthlyUsage: 96000, alerts: [], hourlyData: [] },
    { id: 'DMA_IN_WOOD', serialNumber: 'ZM-IN-003', customerName: 'LWSC Woodlands Inlet', address: 'Woodlands Main Supply', type: 'dma_inlet', dma: 'DMA_WOODLANDS', lat: -15.4250, lng: 28.3083, status: 'online', currentReading: 512340, flowRate: 5100, batteryLevel: 100, signalStrength: 88, lastUpdate: new Date(), dailyUsage: 5100, monthlyUsage: 153000, alerts: [], hourlyData: [] },
    { id: 'DMA_IN_MAT', serialNumber: 'ZM-IN-004', customerName: 'LWSC Matero Inlet', address: 'Matero Main Road Supply', type: 'dma_inlet', dma: 'DMA_MATERO', lat: -15.3750, lng: 28.2500, status: 'warning', currentReading: 623450, flowRate: 6200, batteryLevel: 100, signalStrength: 75, lastUpdate: new Date(), dailyUsage: 6200, monthlyUsage: 186000, alerts: [{ id: 'a1', type: 'high_consumption', severity: 'medium', message: 'Flow 15% above normal', timestamp: new Date() }], hourlyData: [] },
    
    // Residential Meters - Kabulonga
    { id: 'MTR_R001', serialNumber: 'ZM-R-10234', customerName: 'Mwansa Chisanga', address: 'Plot 123, Kabulonga Road', type: 'residential', dma: 'DMA_KABULONGA', lat: -15.3970, lng: 28.3190, status: 'online', currentReading: 1245.6, flowRate: 45, batteryLevel: 87, signalStrength: 82, lastUpdate: new Date(), dailyUsage: 0.42, monthlyUsage: 12.5, alerts: [], hourlyData: [] },
    { id: 'MTR_R002', serialNumber: 'ZM-R-10235', customerName: 'Grace Banda', address: 'Plot 45, Leopards Hill Road', type: 'residential', dma: 'DMA_KABULONGA', lat: -15.4010, lng: 28.3250, status: 'online', currentReading: 892.3, flowRate: 0, batteryLevel: 92, signalStrength: 88, lastUpdate: new Date(), dailyUsage: 0.35, monthlyUsage: 10.8, alerts: [], hourlyData: [] },
    { id: 'MTR_R003', serialNumber: 'ZM-R-10236', customerName: 'Joseph Mumba', address: 'Plot 78, Twin Palm Road', type: 'residential', dma: 'DMA_KABULONGA', lat: -15.3985, lng: 28.3175, status: 'warning', currentReading: 2156.8, flowRate: 120, batteryLevel: 45, signalStrength: 65, lastUpdate: new Date(), dailyUsage: 0.95, monthlyUsage: 28.5, alerts: [{ id: 'a2', type: 'night_flow', severity: 'high', message: 'Continuous flow detected 2-4 AM', timestamp: new Date() }], hourlyData: [] },
    
    // Residential Meters - Woodlands
    { id: 'MTR_R004', serialNumber: 'ZM-R-20156', customerName: 'Mary Phiri', address: 'House 234, Woodlands Extension', type: 'residential', dma: 'DMA_WOODLANDS', lat: -15.4260, lng: 28.3070, status: 'online', currentReading: 678.2, flowRate: 28, batteryLevel: 78, signalStrength: 85, lastUpdate: new Date(), dailyUsage: 0.38, monthlyUsage: 11.4, alerts: [], hourlyData: [] },
    { id: 'MTR_R005', serialNumber: 'ZM-R-20157', customerName: 'Peter Tembo', address: 'Plot 56, Makishi Road', type: 'residential', dma: 'DMA_WOODLANDS', lat: -15.4280, lng: 28.3100, status: 'critical', currentReading: 3421.5, flowRate: 250, batteryLevel: 15, signalStrength: 45, lastUpdate: new Date(Date.now() - 3600000), dailyUsage: 2.8, monthlyUsage: 84.0, alerts: [{ id: 'a3', type: 'leak', severity: 'critical', message: 'Suspected leak - usage 8x normal', timestamp: new Date() }, { id: 'a4', type: 'battery_low', severity: 'medium', message: 'Battery at 15%', timestamp: new Date() }], hourlyData: [] },
    
    // Residential Meters - Matero
    { id: 'MTR_R006', serialNumber: 'ZM-R-30089', customerName: 'Agnes Mulenga', address: 'Stand 456, Matero West', type: 'residential', dma: 'DMA_MATERO', lat: -15.3840, lng: 28.2550, status: 'online', currentReading: 456.7, flowRate: 15, batteryLevel: 95, signalStrength: 78, lastUpdate: new Date(), dailyUsage: 0.28, monthlyUsage: 8.4, alerts: [], hourlyData: [] },
    { id: 'MTR_R007', serialNumber: 'ZM-R-30090', customerName: 'John Sakala', address: 'Plot 789, Chipata Road', type: 'residential', dma: 'DMA_MATERO', lat: -15.3820, lng: 28.2580, status: 'offline', currentReading: 234.5, flowRate: 0, batteryLevel: 0, signalStrength: 0, lastUpdate: new Date(Date.now() - 86400000), dailyUsage: 0, monthlyUsage: 5.2, alerts: [{ id: 'a5', type: 'offline', severity: 'high', message: 'No signal for 24 hours', timestamp: new Date() }], hourlyData: [] },
    
    // Commercial Meters
    { id: 'MTR_C001', serialNumber: 'ZM-C-50012', customerName: 'Manda Hill Shopping Centre', address: 'Great East Road, Kabulonga', type: 'commercial', dma: 'DMA_KABULONGA', lat: -15.4000, lng: 28.3150, status: 'online', currentReading: 89560.2, flowRate: 850, batteryLevel: 100, signalStrength: 95, lastUpdate: new Date(), dailyUsage: 45.5, monthlyUsage: 1365, alerts: [], hourlyData: [] },
    { id: 'MTR_C002', serialNumber: 'ZM-C-50013', customerName: 'Levy Junction Mall', address: 'Church Road, CBD', type: 'commercial', dma: 'DMA_CBD', lat: -15.4150, lng: 28.2850, status: 'online', currentReading: 156230.8, flowRate: 920, batteryLevel: 100, signalStrength: 92, lastUpdate: new Date(), dailyUsage: 52.3, monthlyUsage: 1569, alerts: [], hourlyData: [] },
    { id: 'MTR_C003', serialNumber: 'ZM-C-50014', customerName: 'EastPark Mall', address: 'Great East Road, CBD', type: 'commercial', dma: 'DMA_CBD', lat: -15.4100, lng: 28.2900, status: 'warning', currentReading: 234567.3, flowRate: 1200, batteryLevel: 100, signalStrength: 88, lastUpdate: new Date(), dailyUsage: 68.2, monthlyUsage: 2046, alerts: [{ id: 'a6', type: 'high_consumption', severity: 'medium', message: 'Weekend consumption 25% higher than average', timestamp: new Date() }], hourlyData: [] },
    { id: 'MTR_C004', serialNumber: 'ZM-C-50015', customerName: 'Intercontinental Hotel', address: 'Haile Selassie Avenue', type: 'commercial', dma: 'DMA_CBD', lat: -15.4180, lng: 28.2870, status: 'online', currentReading: 345678.9, flowRate: 680, batteryLevel: 100, signalStrength: 94, lastUpdate: new Date(), dailyUsage: 38.5, monthlyUsage: 1155, alerts: [], hourlyData: [] },
    
    // Industrial Meters
    { id: 'MTR_I001', serialNumber: 'ZM-I-70001', customerName: 'Zambia Breweries', address: 'Industrial Area, Chinika', type: 'industrial', dma: 'DMA_MATERO', lat: -15.4400, lng: 28.2620, status: 'online', currentReading: 2345670.5, flowRate: 8500, batteryLevel: 100, signalStrength: 90, lastUpdate: new Date(), dailyUsage: 450.0, monthlyUsage: 13500, alerts: [], hourlyData: [] },
    { id: 'MTR_I002', serialNumber: 'ZM-I-70002', customerName: 'Trade Kings Limited', address: 'Plot 2374, Industrial Area', type: 'industrial', dma: 'DMA_MATERO', lat: -15.4420, lng: 28.2640, status: 'online', currentReading: 1876543.2, flowRate: 6200, batteryLevel: 100, signalStrength: 88, lastUpdate: new Date(), dailyUsage: 320.0, monthlyUsage: 9600, alerts: [], hourlyData: [] },
    { id: 'MTR_I003', serialNumber: 'ZM-I-70003', customerName: 'Chilanga Cement', address: 'Kafue Road, Chilanga', type: 'industrial', dma: 'DMA_CHILENJE', lat: -15.5500, lng: 28.2800, status: 'warning', currentReading: 3456789.1, flowRate: 12000, batteryLevel: 100, signalStrength: 72, lastUpdate: new Date(), dailyUsage: 580.0, monthlyUsage: 17400, alerts: [{ id: 'a7', type: 'high_consumption', severity: 'low', message: 'Production increase - expected', timestamp: new Date() }], hourlyData: [] },
  ];
  
  // Generate hourly data for each meter
  meters.forEach(meter => {
    const baseUsage = meter.type === 'residential' ? 20 : meter.type === 'commercial' ? 50 : 200;
    meter.hourlyData = Array.from({ length: 24 }, (_, i) => {
      const hourFactor = i >= 6 && i <= 9 ? 1.5 : i >= 18 && i <= 21 ? 1.3 : i >= 0 && i <= 5 ? 0.3 : 1;
      return Math.round(baseUsage * hourFactor * (0.8 + Math.random() * 0.4));
    });
  });
  
  return meters;
};

export default function SmartMetersPage() {
  const [meters, setMeters] = useState<SmartMeter[]>([]);
  const [dmaBalances, setDmaBalances] = useState<DMABalance[]>(lusakaDMAs);
  const [selectedMeter, setSelectedMeter] = useState<SmartMeter | null>(null);
  const [selectedDMA, setSelectedDMA] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);

  // Initialize meters
  useEffect(() => {
    setMeters(generateMeters());
  }, []);

  // Collect all active alerts
  useEffect(() => {
    const alerts = meters.flatMap(m => m.alerts.map(a => ({ ...a, meterId: m.id, meterName: m.customerName })));
    setActiveAlerts(alerts as any);
  }, [meters]);

  // Real-time data simulation
  const updateRealTimeData = useCallback(() => {
    setMeters(prev => prev.map(meter => {
      if (meter.status === 'offline') return meter;
      
      // Simulate flow rate changes
      const baseFlow = meter.type === 'residential' ? 30 : meter.type === 'commercial' ? 500 : 5000;
      const hour = new Date().getHours();
      const timeFactor = hour >= 6 && hour <= 9 ? 1.5 : hour >= 18 && hour <= 21 ? 1.3 : hour >= 0 && hour <= 5 ? 0.2 : 1;
      const randomFactor = 0.8 + Math.random() * 0.4;
      
      const newFlowRate = Math.round(baseFlow * timeFactor * randomFactor);
      const consumptionIncrement = newFlowRate / 60000; // m³ per second
      
      return {
        ...meter,
        flowRate: newFlowRate,
        currentReading: meter.currentReading + consumptionIncrement,
        lastUpdate: new Date(),
        batteryLevel: meter.batteryLevel > 10 ? meter.batteryLevel - (Math.random() > 0.99 ? 0.1 : 0) : meter.batteryLevel,
        signalStrength: Math.min(100, Math.max(40, meter.signalStrength + (Math.random() - 0.5) * 5))
      };
    }));

    // Update DMA balances
    setDmaBalances(prev => prev.map(dma => ({
      ...dma,
      totalInput: dma.totalInput + (Math.random() - 0.3) * 50,
      billedConsumption: dma.billedConsumption + (Math.random() - 0.4) * 30,
      nrwPercentage: Math.max(15, Math.min(50, dma.nrwPercentage + (Math.random() - 0.5) * 0.5))
    })));

    setLastUpdate(new Date());
  }, []);

  // Real-time update interval
  useEffect(() => {
    if (!isLive) return;
    
    const interval = setInterval(updateRealTimeData, 3000);
    return () => clearInterval(interval);
  }, [isLive, updateRealTimeData]);

  // Filter meters
  const filteredMeters = meters.filter(meter => {
    const matchesDMA = selectedDMA === 'all' || meter.dma === selectedDMA;
    const matchesType = selectedType === 'all' || meter.type === selectedType;
    const matchesSearch = searchTerm === '' || 
      meter.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      meter.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      meter.serialNumber.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesDMA && matchesType && matchesSearch;
  });

  // Statistics
  const stats = {
    totalMeters: meters.length,
    onlineMeters: meters.filter(m => m.status === 'online').length,
    warningMeters: meters.filter(m => m.status === 'warning').length,
    criticalMeters: meters.filter(m => m.status === 'critical' || m.status === 'offline').length,
    totalFlow: meters.reduce((sum, m) => sum + m.flowRate, 0),
    totalDailyUsage: meters.reduce((sum, m) => sum + m.dailyUsage, 0),
    avgNRW: dmaBalances.reduce((sum, d) => sum + d.nrwPercentage, 0) / dmaBalances.length
  };

  const getMeterIcon = (type: MeterType) => {
    switch (type) {
      case 'residential': return <Home className="w-4 h-4" />;
      case 'commercial': return <Building2 className="w-4 h-4" />;
      case 'industrial': return <Factory className="w-4 h-4" />;
      case 'dma_inlet': return <ArrowDownRight className="w-4 h-4" />;
      case 'dma_outlet': return <ArrowUpRight className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: MeterStatus) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'critical': return 'bg-red-500';
      case 'offline': return 'bg-gray-500';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-blue-400 bg-blue-500/20';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20';
      case 'high': return 'text-orange-400 bg-orange-500/20';
      case 'critical': return 'text-red-400 bg-red-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gauge className="w-8 h-8 text-[#198038]" />
            Smart Meters Dashboard
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Real-time Advanced Metering Infrastructure (AMI) Monitoring
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Live Status */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${isLive ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
            {isLive ? (
              <>
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
                <span className="text-sm font-medium">LIVE</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4" />
                <span className="text-sm">Paused</span>
              </>
            )}
          </div>
          
          <button
            onClick={() => setIsLive(!isLive)}
            className={`p-2 rounded-lg transition-colors ${isLive ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'}`}
          >
            {isLive ? <WifiOff className="w-5 h-5" /> : <Wifi className="w-5 h-5" />}
          </button>
          
          <button
            onClick={updateRealTimeData}
            className="p-2 bg-[#198038] rounded-lg hover:bg-[#166a2e] transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
          
          <div className="text-sm text-gray-400">
            <Clock className="w-4 h-4 inline mr-1" />
            {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <div className="text-gray-400 text-xs mb-1">Total Meters</div>
          <div className="text-2xl font-bold">{stats.totalMeters}</div>
          <div className="text-[#198038] text-xs">AMI Connected</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-green-500/30">
          <div className="text-gray-400 text-xs mb-1">Online</div>
          <div className="text-2xl font-bold text-green-400">{stats.onlineMeters}</div>
          <div className="text-green-400 text-xs">{((stats.onlineMeters / stats.totalMeters) * 100).toFixed(0)}% Active</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-yellow-500/30">
          <div className="text-gray-400 text-xs mb-1">Warnings</div>
          <div className="text-2xl font-bold text-yellow-400">{stats.warningMeters}</div>
          <div className="text-yellow-400 text-xs">Need Attention</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-red-500/30">
          <div className="text-gray-400 text-xs mb-1">Critical/Offline</div>
          <div className="text-2xl font-bold text-red-400">{stats.criticalMeters}</div>
          <div className="text-red-400 text-xs">Immediate Action</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-blue-500/30">
          <div className="text-gray-400 text-xs mb-1">Total Flow</div>
          <div className="text-2xl font-bold text-blue-400">{(stats.totalFlow / 1000).toFixed(1)}</div>
          <div className="text-blue-400 text-xs">m³/hour</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-purple-500/30">
          <div className="text-gray-400 text-xs mb-1">Daily Usage</div>
          <div className="text-2xl font-bold text-purple-400">{stats.totalDailyUsage.toFixed(0)}</div>
          <div className="text-purple-400 text-xs">m³ today</div>
        </div>
        
        <div className="bg-gray-800 rounded-xl p-4 border border-[#EF7D00]/30">
          <div className="text-gray-400 text-xs mb-1">Avg NRW</div>
          <div className="text-2xl font-bold text-[#EF7D00]">{stats.avgNRW.toFixed(1)}%</div>
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
              {dmaBalances.map(dma => (
                <div 
                  key={dma.id}
                  className={`p-3 rounded-lg border ${
                    dma.status === 'good' ? 'bg-green-500/10 border-green-500/30' :
                    dma.status === 'concern' ? 'bg-yellow-500/10 border-yellow-500/30' :
                    'bg-red-500/10 border-red-500/30'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium">{dma.name}</div>
                      <div className="text-xs text-gray-400">{dma.meterCount} meters</div>
                    </div>
                    <div className={`text-lg font-bold ${
                      dma.status === 'good' ? 'text-green-400' :
                      dma.status === 'concern' ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {dma.nrwPercentage.toFixed(1)}%
                    </div>
                  </div>
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
                    <span>Input: {dma.totalInput.toFixed(0)} m³/day</span>
                    <span>Billed: {dma.billedConsumption.toFixed(0)} m³/day</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5 text-red-400" />
              Active Alerts
              <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {activeAlerts.length}
              </span>
            </h2>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {activeAlerts.length === 0 ? (
                <div className="text-center text-gray-400 py-4">
                  <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No active alerts</p>
                </div>
              ) : (
                activeAlerts.map((alert: any, idx) => (
                  <div 
                    key={idx}
                    className={`p-3 rounded-lg ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      <div>
                        <div className="font-medium text-sm">{alert.meterName}</div>
                        <div className="text-xs opacity-75">{alert.message}</div>
                        <div className="text-xs opacity-50 mt-1">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Middle & Right Columns - Meter List */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl border border-gray-700">
          {/* Filters */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search meters by name, address, or serial..."
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
                {dmaBalances.map(dma => (
                  <option key={dma.id} value={dma.id}>{dma.name}</option>
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

          {/* Meter Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700/50 text-xs text-gray-400 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Meter / Customer</th>
                  <th className="px-4 py-3 text-left">Type</th>
                  <th className="px-4 py-3 text-right">Flow Rate</th>
                  <th className="px-4 py-3 text-right">Reading</th>
                  <th className="px-4 py-3 text-center">Battery</th>
                  <th className="px-4 py-3 text-center">Signal</th>
                  <th className="px-4 py-3 text-center">Status</th>
                  <th className="px-4 py-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredMeters.map(meter => (
                  <tr 
                    key={meter.id}
                    className="hover:bg-gray-700/50 transition-colors cursor-pointer"
                    onClick={() => setSelectedMeter(meter)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(meter.status)} ${meter.status === 'online' ? 'animate-pulse' : ''}`} />
                        <div>
                          <div className="font-medium text-sm">{meter.customerName}</div>
                          <div className="text-xs text-gray-400">{meter.serialNumber}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-sm">
                        {getMeterIcon(meter.type)}
                        <span className="capitalize">{meter.type.replace('_', ' ')}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="text-sm font-mono">
                        {meter.flowRate.toLocaleString()} <span className="text-gray-400 text-xs">L/hr</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="text-sm font-mono">
                        {meter.currentReading.toLocaleString(undefined, { maximumFractionDigits: 1 })} <span className="text-gray-400 text-xs">m³</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <Battery className={`w-4 h-4 ${
                          meter.batteryLevel > 50 ? 'text-green-400' :
                          meter.batteryLevel > 20 ? 'text-yellow-400' :
                          'text-red-400'
                        }`} />
                        <span className="text-xs">{meter.batteryLevel}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        <Signal className={`w-4 h-4 ${
                          meter.signalStrength > 70 ? 'text-green-400' :
                          meter.signalStrength > 40 ? 'text-yellow-400' :
                          'text-red-400'
                        }`} />
                        <span className="text-xs">{meter.signalStrength}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center">
                        <span className={`px-2 py-1 rounded-full text-xs capitalize ${
                          meter.status === 'online' ? 'bg-green-500/20 text-green-400' :
                          meter.status === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                          meter.status === 'critical' ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {meter.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-center gap-2">
                        <button className="p-1.5 hover:bg-gray-600 rounded transition-colors">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 hover:bg-gray-600 rounded transition-colors">
                          <Settings className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="p-4 border-t border-gray-700 text-sm text-gray-400">
            Showing {filteredMeters.length} of {meters.length} meters
          </div>
        </div>
      </div>

      {/* Meter Detail Modal */}
      {selectedMeter && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedMeter(null)}>
          <div className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full border border-gray-700" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold">{selectedMeter.customerName}</h3>
                <p className="text-gray-400 text-sm">{selectedMeter.address}</p>
              </div>
              <button onClick={() => setSelectedMeter(null)} className="text-gray-400 hover:text-white">✕</button>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-700/50 p-3 rounded-lg">
                <div className="text-xs text-gray-400">Serial Number</div>
                <div className="font-mono">{selectedMeter.serialNumber}</div>
              </div>
              <div className="bg-gray-700/50 p-3 rounded-lg">
                <div className="text-xs text-gray-400">Current Reading</div>
                <div className="font-mono">{selectedMeter.currentReading.toLocaleString()} m³</div>
              </div>
              <div className="bg-gray-700/50 p-3 rounded-lg">
                <div className="text-xs text-gray-400">Flow Rate</div>
                <div className="font-mono text-blue-400">{selectedMeter.flowRate.toLocaleString()} L/hr</div>
              </div>
              <div className="bg-gray-700/50 p-3 rounded-lg">
                <div className="text-xs text-gray-400">Daily Usage</div>
                <div className="font-mono">{selectedMeter.dailyUsage.toFixed(2)} m³</div>
              </div>
            </div>
            
            {/* Hourly Usage Chart */}
            <div className="bg-gray-700/50 p-4 rounded-lg mb-4">
              <div className="text-sm text-gray-400 mb-2">24-Hour Usage Pattern</div>
              <div className="flex items-end gap-1 h-24">
                {selectedMeter.hourlyData.map((value, i) => {
                  const max = Math.max(...selectedMeter.hourlyData);
                  const height = (value / max) * 100;
                  const isNow = new Date().getHours() === i;
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div 
                        className={`w-full rounded-t transition-all ${isNow ? 'bg-[#198038]' : 'bg-blue-500/50'}`}
                        style={{ height: `${height}%` }}
                      />
                      {i % 4 === 0 && <div className="text-xs text-gray-500 mt-1">{i}h</div>}
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* Alerts */}
            {selectedMeter.alerts.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <div className="text-sm font-medium text-red-400 mb-2">Active Alerts</div>
                {selectedMeter.alerts.map((alert, i) => (
                  <div key={i} className="text-sm text-red-300">{alert.message}</div>
                ))}
              </div>
            )}
            
            <div className="flex gap-2 mt-4">
              <button className="flex-1 bg-[#198038] hover:bg-[#166a2e] py-2 rounded-lg transition-colors">
                View Full History
              </button>
              <button className="flex-1 bg-gray-700 hover:bg-gray-600 py-2 rounded-lg transition-colors">
                Generate Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
