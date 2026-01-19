'use client'

import { useState } from 'react'
import { Database, Server, Wifi, Save, RefreshCw, AlertTriangle } from 'lucide-react'

export default function SystemConfigPage() {
  const [config, setConfig] = useState({
    apiEndpoint: 'http://localhost:8000',
    mqttBroker: 'mqtt://192.168.8.100:1883',
    dataRetentionDays: 90,
    alertThreshold: 15,
    nrwTarget: 25,
    autoBackup: true,
    maintenanceMode: false
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">System Configuration</h1>
          <p className="text-sm text-slate-500 mt-1">Configure system settings and integrations</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-500/25">
          <Save className="w-4 h-4" />
          Save Changes
        </button>
      </div>

      {/* Config Sections */}
      <div className="grid grid-cols-2 gap-6">
        {/* API Settings */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Server className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">API Settings</h2>
              <p className="text-xs text-slate-500">Backend API configuration</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">API Endpoint</label>
              <input 
                type="text" 
                value={config.apiEndpoint}
                onChange={(e) => setConfig({...config, apiEndpoint: e.target.value})}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">MQTT Broker</label>
              <input 
                type="text" 
                value={config.mqttBroker}
                onChange={(e) => setConfig({...config, mqttBroker: e.target.value})}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono text-sm"
              />
            </div>
          </div>
        </div>

        {/* Data Settings */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Database className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Data Settings</h2>
              <p className="text-xs text-slate-500">Data retention and backup</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Data Retention (days)</label>
              <input 
                type="number" 
                value={config.dataRetentionDays}
                onChange={(e) => setConfig({...config, dataRetentionDays: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-700">Auto Backup</p>
                <p className="text-xs text-slate-500">Daily automatic backups</p>
              </div>
              <button 
                onClick={() => setConfig({...config, autoBackup: !config.autoBackup})}
                className={`relative w-12 h-6 rounded-full transition-colors ${config.autoBackup ? 'bg-emerald-500' : 'bg-slate-200'}`}
              >
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${config.autoBackup ? 'left-7' : 'left-1'}`} />
              </button>
            </div>
          </div>
        </div>

        {/* Alert Thresholds */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Alert Thresholds</h2>
              <p className="text-xs text-slate-500">Configure alert sensitivity</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Pressure Drop Alert (%)</label>
              <input 
                type="number" 
                value={config.alertThreshold}
                onChange={(e) => setConfig({...config, alertThreshold: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">NRW Target (%)</label>
              <input 
                type="number" 
                value={config.nrwTarget}
                onChange={(e) => setConfig({...config, nrwTarget: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Wifi className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900">System Status</h2>
              <p className="text-xs text-slate-500">Maintenance and diagnostics</p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-slate-700">Maintenance Mode</p>
                <p className="text-xs text-slate-500">Disable public access</p>
              </div>
              <button 
                onClick={() => setConfig({...config, maintenanceMode: !config.maintenanceMode})}
                className={`relative w-12 h-6 rounded-full transition-colors ${config.maintenanceMode ? 'bg-red-500' : 'bg-slate-200'}`}
              >
                <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${config.maintenanceMode ? 'left-7' : 'left-1'}`} />
              </button>
            </div>
            <button className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
              <RefreshCw className="w-4 h-4 text-slate-500" />
              <span className="text-sm text-slate-600">Restart Services</span>
            </button>
          </div>
        </div>
      </div>

      {/* Connected Devices */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Connected ESP32 Devices</h2>
        <div className="grid grid-cols-4 gap-4">
          {['ESP32_001', 'ESP32_002', 'ESP32_003', 'ESP32_004'].map((device, i) => (
            <div key={device} className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-900">{device}</span>
                <span className={`w-2 h-2 rounded-full ${i < 3 ? 'bg-emerald-500' : 'bg-slate-300'}`} />
              </div>
              <p className="text-xs text-slate-500">DMA-{String(i + 1).padStart(3, '0')}</p>
              <p className="text-xs text-slate-400">Last: {i < 3 ? '2 min ago' : 'Offline'}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
