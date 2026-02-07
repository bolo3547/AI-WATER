'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Droplets, Activity, AlertTriangle, CheckCircle, Clock,
  Thermometer, Beaker, TestTube, MapPin, RefreshCw, TrendingUp,
  TrendingDown, ChevronRight, Download, Filter, Calendar, Waves
} from 'lucide-react';

interface WaterQualitySensor {
  id: string;
  name: string;
  location: string;
  dma: string;
  lat: number;
  lng: number;
  status: 'online' | 'offline' | 'warning';
  lastReading: string;
  parameters: {
    ph: number;
    chlorine: number; // mg/L
    turbidity: number; // NTU
    temperature: number; // °C
    conductivity: number; // μS/cm
    tds: number; // mg/L (Total Dissolved Solids)
    dissolvedOxygen: number; // mg/L
  };
  alerts: string[];
}

interface QualityAlert {
  id: string;
  sensorId: string;
  sensorName: string;
  parameter: string;
  value: number;
  threshold: number;
  level: 'warning' | 'critical';
  timestamp: string;
  acknowledged: boolean;
}

// Zambian/WHO water quality standards
const standards = {
  ph: { min: 6.5, max: 8.5, unit: '' },
  chlorine: { min: 0.2, max: 0.5, unit: 'mg/L' },
  turbidity: { max: 5, unit: 'NTU' },
  temperature: { max: 25, unit: '°C' },
  conductivity: { max: 2500, unit: 'μS/cm' },
  tds: { max: 1000, unit: 'mg/L' },
  dissolvedOxygen: { min: 4, unit: 'mg/L' },
};

// Initial sensor data
const initialSensors: WaterQualitySensor[] = [
  {
    id: 'WQ-001',
    name: 'Kafue Intake Station',
    location: 'Kafue River Intake, Chilanga',
    dma: 'Source',
    lat: -15.530,
    lng: 28.185,
    status: 'online',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.2,
      chlorine: 0.0,
      turbidity: 8.5,
      temperature: 24.2,
      conductivity: 245,
      tds: 122,
      dissolvedOxygen: 7.8,
    },
    alerts: ['Raw water - pre-treatment']
  },
  {
    id: 'WQ-002',
    name: 'Iolanda Treatment Plant',
    location: 'Post-Treatment Outlet',
    dma: 'Treatment',
    lat: -15.515,
    lng: 28.190,
    status: 'online',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.4,
      chlorine: 0.45,
      turbidity: 0.3,
      temperature: 23.8,
      conductivity: 238,
      tds: 119,
      dissolvedOxygen: 8.2,
    },
    alerts: []
  },
  {
    id: 'WQ-003',
    name: 'Matero Reservoir',
    location: 'Matero Service Reservoir',
    dma: 'Matero',
    lat: -15.360,
    lng: 28.270,
    status: 'online',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.3,
      chlorine: 0.35,
      turbidity: 0.5,
      temperature: 25.1,
      conductivity: 242,
      tds: 121,
      dissolvedOxygen: 7.6,
    },
    alerts: []
  },
  {
    id: 'WQ-004',
    name: 'Kabulonga Booster',
    location: 'Kabulonga Pump Station',
    dma: 'Kabulonga',
    lat: -15.400,
    lng: 28.320,
    status: 'online',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.1,
      chlorine: 0.28,
      turbidity: 0.8,
      temperature: 26.3,
      conductivity: 255,
      tds: 127,
      dissolvedOxygen: 6.9,
    },
    alerts: []
  },
  {
    id: 'WQ-005',
    name: 'Garden Distribution',
    location: 'Garden DMA Entry Point',
    dma: 'Garden',
    lat: -15.403,
    lng: 28.283,
    status: 'warning',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.0,
      chlorine: 0.18,
      turbidity: 1.2,
      temperature: 27.5,
      conductivity: 268,
      tds: 134,
      dissolvedOxygen: 6.2,
    },
    alerts: ['Low chlorine residual']
  },
  {
    id: 'WQ-006',
    name: 'Chilenje Main',
    location: 'Chilenje Distribution Main',
    dma: 'Chilenje',
    lat: -15.450,
    lng: 28.268,
    status: 'online',
    lastReading: new Date().toISOString(),
    parameters: {
      ph: 7.2,
      chlorine: 0.32,
      turbidity: 0.6,
      temperature: 25.8,
      conductivity: 249,
      tds: 124,
      dissolvedOxygen: 7.1,
    },
    alerts: []
  },
  {
    id: 'WQ-007',
    name: 'Roma End Point',
    location: 'Roma Township Edge',
    dma: 'Roma',
    lat: -15.413,
    lng: 28.298,
    status: 'offline',
    lastReading: new Date(Date.now() - 3600000).toISOString(),
    parameters: {
      ph: 6.9,
      chlorine: 0.15,
      turbidity: 2.1,
      temperature: 28.2,
      conductivity: 285,
      tds: 142,
      dissolvedOxygen: 5.8,
    },
    alerts: ['Sensor offline', 'Low chlorine residual']
  },
];

const initialAlerts: QualityAlert[] = [
  {
    id: 'QA-001',
    sensorId: 'WQ-005',
    sensorName: 'Garden Distribution',
    parameter: 'Chlorine',
    value: 0.18,
    threshold: 0.2,
    level: 'warning',
    timestamp: new Date().toISOString(),
    acknowledged: false
  },
  {
    id: 'QA-002',
    sensorId: 'WQ-007',
    sensorName: 'Roma End Point',
    parameter: 'Chlorine',
    value: 0.15,
    threshold: 0.2,
    level: 'critical',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    acknowledged: false
  },
];

export default function WaterQualityPage() {
  const [sensors, setSensors] = useState<WaterQualitySensor[]>(initialSensors);
  const [alerts, setAlerts] = useState<QualityAlert[]>(initialAlerts);
  const [selectedSensor, setSelectedSensor] = useState<WaterQualitySensor | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Simulate real-time updates
  const updateReadings = useCallback(() => {
    setSensors(prev => prev.map(sensor => {
      if (sensor.status === 'offline') return sensor;
      
      // Simulate small variations
      const vary = (val: number, range: number) => val + (Math.random() - 0.5) * range;
      
      return {
        ...sensor,
        lastReading: new Date().toISOString(),
        parameters: {
          ph: Math.round(vary(sensor.parameters.ph, 0.1) * 100) / 100,
          chlorine: Math.round(vary(sensor.parameters.chlorine, 0.02) * 100) / 100,
          turbidity: Math.round(vary(sensor.parameters.turbidity, 0.2) * 100) / 100,
          temperature: Math.round(vary(sensor.parameters.temperature, 0.3) * 10) / 10,
          conductivity: Math.round(vary(sensor.parameters.conductivity, 5)),
          tds: Math.round(vary(sensor.parameters.tds, 3)),
          dissolvedOxygen: Math.round(vary(sensor.parameters.dissolvedOxygen, 0.2) * 10) / 10,
        }
      };
    }));
    setLastUpdate(new Date());
  }, []);

  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(updateReadings, 5000);
    return () => clearInterval(interval);
  }, [isLive, updateReadings]);

  const getParameterStatus = (param: string, value: number) => {
    const std = standards[param as keyof typeof standards];
    if (!std) return 'normal';
    
    if ('min' in std && value < std.min) return 'low';
    if ('max' in std && value > std.max) return 'high';
    if ('min' in std && 'max' in std) {
      if (value >= std.min && value <= std.max) return 'normal';
    }
    return 'normal';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'text-green-600 bg-green-100';
      case 'low': return 'text-amber-600 bg-amber-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const stats = {
    online: sensors.filter(s => s.status === 'online').length,
    warning: sensors.filter(s => s.status === 'warning').length,
    offline: sensors.filter(s => s.status === 'offline').length,
    activeAlerts: alerts.filter(a => !a.acknowledged).length,
    avgPh: (sensors.reduce((sum, s) => sum + s.parameters.ph, 0) / sensors.length).toFixed(2),
    avgChlorine: (sensors.reduce((sum, s) => sum + s.parameters.chlorine, 0) / sensors.length).toFixed(2),
    avgTurbidity: (sensors.reduce((sum, s) => sum + s.parameters.turbidity, 0) / sensors.length).toFixed(1),
  };

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, acknowledged: true } : a));
  };

  return (
    <div className="bg-gray-100">
      {/* Header */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Beaker className="w-7 h-7 text-[#198038]" />
              Water Quality Monitoring
            </h1>
            <p className="text-sm text-gray-500 mt-1">Real-time water quality analysis across the distribution network</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsLive(!isLive)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${isLive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}
            >
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
            </button>
            <span className="text-xs text-gray-500">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-500">Online</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.online}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-gray-500">Warning</span>
          </div>
          <p className="text-2xl font-bold text-amber-600">{stats.warning}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 rounded-full bg-gray-300" />
            <span className="text-xs text-gray-500">Offline</span>
          </div>
          <p className="text-2xl font-bold text-gray-600">{stats.offline}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span className="text-xs text-gray-500">Alerts</span>
          </div>
          <p className="text-2xl font-bold text-red-600">{stats.activeAlerts}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <TestTube className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-500">Avg pH</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.avgPh}</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <Droplets className="w-4 h-4 text-cyan-500" />
            <span className="text-xs text-gray-500">Avg Cl₂</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.avgChlorine} <span className="text-xs font-normal">mg/L</span></p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-2 mb-2">
            <Waves className="w-4 h-4 text-amber-500" />
            <span className="text-xs text-gray-500">Avg Turb.</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{stats.avgTurbidity} <span className="text-xs font-normal">NTU</span></p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sensors List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">Quality Monitoring Stations</h2>
            </div>
            <div className="divide-y">
              {sensors.map((sensor) => (
                <div
                  key={sensor.id}
                  onClick={() => setSelectedSensor(sensor)}
                  className={`p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedSensor?.id === sensor.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        sensor.status === 'online' ? 'bg-green-100' :
                        sensor.status === 'warning' ? 'bg-amber-100' : 'bg-gray-100'
                      }`}>
                        <Beaker className={`w-5 h-5 ${
                          sensor.status === 'online' ? 'text-green-600' :
                          sensor.status === 'warning' ? 'text-amber-600' : 'text-gray-400'
                        }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{sensor.name}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                            sensor.status === 'online' ? 'bg-green-100 text-green-700' :
                            sensor.status === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {sensor.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {sensor.location}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                  
                  {/* Quick Parameters */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mt-3">
                    <div className="text-center p-2 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500">pH</p>
                      <p className={`text-sm font-semibold ${
                        getParameterStatus('ph', sensor.parameters.ph) === 'normal' ? 'text-green-600' : 'text-amber-600'
                      }`}>
                        {sensor.parameters.ph}
                      </p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500">Cl₂</p>
                      <p className={`text-sm font-semibold ${
                        getParameterStatus('chlorine', sensor.parameters.chlorine) === 'normal' ? 'text-green-600' : 'text-amber-600'
                      }`}>
                        {sensor.parameters.chlorine}
                      </p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500">Turb.</p>
                      <p className={`text-sm font-semibold ${
                        getParameterStatus('turbidity', sensor.parameters.turbidity) === 'normal' ? 'text-green-600' : 'text-amber-600'
                      }`}>
                        {sensor.parameters.turbidity}
                      </p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-500">Temp</p>
                      <p className={`text-sm font-semibold ${
                        getParameterStatus('temperature', sensor.parameters.temperature) === 'normal' ? 'text-green-600' : 'text-amber-600'
                      }`}>
                        {sensor.parameters.temperature}°
                      </p>
                    </div>
                  </div>

                  {sensor.alerts.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {sensor.alerts.map((alert, i) => (
                        <span key={i} className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                          {alert}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Detail Panel & Alerts */}
        <div className="space-y-4">
          {/* Active Alerts */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                Quality Alerts
              </h2>
            </div>
            <div className="divide-y">
              {alerts.filter(a => !a.acknowledged).map((alert) => (
                <div key={alert.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          alert.level === 'critical' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {alert.level}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{alert.parameter}</span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{alert.sensorName}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Value: {alert.value} (Threshold: {alert.threshold})
                      </p>
                    </div>
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200"
                    >
                      ACK
                    </button>
                  </div>
                </div>
              ))}
              {alerts.filter(a => !a.acknowledged).length === 0 && (
                <div className="p-4 text-center text-sm text-gray-500">
                  <CheckCircle className="w-8 h-8 mx-auto text-green-400 mb-2" />
                  No active alerts
                </div>
              )}
            </div>
          </div>

          {/* Selected Sensor Details */}
          {selectedSensor && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold text-gray-900 mb-4">{selectedSensor.name}</h2>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'pH Level', value: selectedSensor.parameters.ph, param: 'ph', icon: TestTube },
                  { label: 'Chlorine', value: `${selectedSensor.parameters.chlorine} mg/L`, param: 'chlorine', icon: Droplets },
                  { label: 'Turbidity', value: `${selectedSensor.parameters.turbidity} NTU`, param: 'turbidity', icon: Waves },
                  { label: 'Temperature', value: `${selectedSensor.parameters.temperature}°C`, param: 'temperature', icon: Thermometer },
                  { label: 'Conductivity', value: `${selectedSensor.parameters.conductivity} μS/cm`, param: 'conductivity', icon: Activity },
                  { label: 'TDS', value: `${selectedSensor.parameters.tds} mg/L`, param: 'tds', icon: Beaker },
                  { label: 'Dissolved O₂', value: `${selectedSensor.parameters.dissolvedOxygen} mg/L`, param: 'dissolvedOxygen', icon: Activity },
                ].map((item, i) => {
                  const status = getParameterStatus(item.param, parseFloat(item.value.toString()));
                  const Icon = item.icon;
                  return (
                    <div key={i} className={`p-3 rounded-lg ${getStatusColor(status)}`}>
                      <div className="flex items-center gap-1 text-xs opacity-75">
                        <Icon className="w-3 h-3" />
                        {item.label}
                      </div>
                      <p className="text-lg font-semibold mt-1">{item.value}</p>
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <p className="text-xs text-gray-500">
                  <Clock className="w-3 h-3 inline mr-1" />
                  Last reading: {new Date(selectedSensor.lastReading).toLocaleTimeString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  <MapPin className="w-3 h-3 inline mr-1" />
                  DMA: {selectedSensor.dma}
                </p>
              </div>
            </div>
          )}

          {/* Quality Standards */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <h2 className="font-semibold text-gray-900 mb-3">ZABS/WHO Standards</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">pH</span>
                <span className="text-gray-900">6.5 - 8.5</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Chlorine Residual</span>
                <span className="text-gray-900">0.2 - 0.5 mg/L</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Turbidity</span>
                <span className="text-gray-900">&lt; 5 NTU</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Temperature</span>
                <span className="text-gray-900">&lt; 25°C</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">TDS</span>
                <span className="text-gray-900">&lt; 1000 mg/L</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
