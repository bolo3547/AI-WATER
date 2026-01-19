'use client'

import { useState } from 'react'
import { Shield, Key, Lock, Eye, EyeOff, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

export default function SecurityPage() {
  const [showApiKey, setShowApiKey] = useState(false)
  const apiKey = 'aqw_sk_live_1234567890abcdef'

  const auditLogs = [
    { id: 1, user: 'admin', action: 'Login', ip: '192.168.8.100', time: '08:30:15', status: 'success' },
    { id: 2, user: 'operator', action: 'View DMA', ip: '192.168.8.101', time: '08:28:42', status: 'success' },
    { id: 3, user: 'unknown', action: 'Login attempt', ip: '45.33.12.99', time: '08:15:00', status: 'failed' },
    { id: 4, user: 'admin', action: 'Config change', ip: '192.168.8.100', time: '07:45:30', status: 'success' },
    { id: 5, user: 'technician', action: 'Login', ip: '192.168.8.105', time: '07:30:00', status: 'success' },
  ]

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Security Center</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5 sm:mt-1">Manage API keys, audit logs, and security settings</p>
      </div>

      {/* Security Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-600">Secure</p>
              <p className="text-xs text-slate-500">System Status</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Key className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">3</p>
              <p className="text-xs text-slate-500">Active API Keys</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">2</p>
              <p className="text-xs text-slate-500">Failed Logins (24h)</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Lock className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">TLS 1.3</p>
              <p className="text-xs text-slate-500">Encryption</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        {/* API Keys */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">API Keys</h2>
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-900">Production Key</span>
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded-full">Active</span>
              </div>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 bg-slate-100 rounded-lg text-sm font-mono text-slate-600 overflow-hidden">
                  {showApiKey ? apiKey : '•'.repeat(32)}
                </code>
                <button 
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4 text-slate-500" /> : <Eye className="w-4 h-4 text-slate-500" />}
                </button>
              </div>
              <p className="text-xs text-slate-400 mt-2">Created: Jan 1, 2026 • Last used: Just now</p>
            </div>
            <button className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-dashed border-slate-300 rounded-xl hover:bg-slate-50 transition-colors text-sm text-slate-600">
              <Key className="w-4 h-4" />
              Generate New API Key
            </button>
          </div>
        </div>

        {/* Session Settings */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Session Settings</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Session Timeout (minutes)</label>
              <input 
                type="number" 
                defaultValue={30}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Failed Login Attempts</label>
              <input 
                type="number" 
                defaultValue={5}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-slate-700">Two-Factor Authentication</p>
                <p className="text-xs text-slate-500">Require 2FA for all admins</p>
              </div>
              <button className="relative w-12 h-6 rounded-full bg-emerald-500 transition-colors">
                <span className="absolute top-1 left-7 w-4 h-4 bg-white rounded-full shadow" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">Recent Activity</h2>
        </div>
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Time</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Action</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">IP Address</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {auditLogs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-3">
                  <span className="flex items-center gap-2 text-sm text-slate-500">
                    <Clock className="w-3 h-3" />
                    {log.time}
                  </span>
                </td>
                <td className="px-6 py-3">
                  <span className="text-sm font-medium text-slate-900">{log.user}</span>
                </td>
                <td className="px-6 py-3">
                  <span className="text-sm text-slate-600">{log.action}</span>
                </td>
                <td className="px-6 py-3">
                  <code className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-1 rounded">{log.ip}</code>
                </td>
                <td className="px-6 py-3">
                  {log.status === 'success' ? (
                    <span className="flex items-center gap-1 text-xs text-emerald-600">
                      <CheckCircle className="w-3 h-3" />
                      Success
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-red-600">
                      <AlertTriangle className="w-3 h-3" />
                      Failed
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
