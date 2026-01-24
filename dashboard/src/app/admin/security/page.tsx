'use client'

import { useState, useEffect } from 'react'
import { 
  Shield, Key, Lock, Eye, EyeOff, AlertTriangle, CheckCircle, Clock,
  Copy, RefreshCw, Trash2, Plus, User, MapPin, Monitor, Smartphone,
  Globe, Activity, Ban, Unlock, Settings, Download, Filter, Search,
  ChevronDown, MoreVertical, XCircle, ShieldCheck, ShieldAlert,
  Fingerprint, Mail, Bell, Save, RotateCcw
} from 'lucide-react'

interface ApiKey {
  id: string
  name: string
  key: string
  status: 'active' | 'revoked' | 'expired'
  createdAt: string
  lastUsed: string | null
  permissions: string[]
  usageCount: number
}

interface AuditLog {
  id: string
  user: string
  role: string
  action: string
  resource: string
  ip: string
  location: string
  device: string
  timestamp: string
  status: 'success' | 'failed' | 'warning'
  details?: string
}

interface ActiveSession {
  id: string
  user: string
  role: string
  device: string
  browser: string
  ip: string
  location: string
  loginTime: string
  lastActivity: string
  current: boolean
}

interface SecuritySettings {
  sessionTimeout: number
  maxFailedAttempts: number
  lockoutDuration: number
  requireTwoFactor: boolean
  passwordMinLength: number
  requireUppercase: boolean
  requireNumbers: boolean
  requireSpecialChars: boolean
  passwordExpiry: number
  ipWhitelist: string[]
  alertOnFailedLogin: boolean
  alertOnNewDevice: boolean
}

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'apikeys' | 'sessions' | 'audit' | 'settings'>('overview')
  const [showApiKey, setShowApiKey] = useState<string | null>(null)
  const [isGeneratingKey, setIsGeneratingKey] = useState(false)
  const [showNewKeyModal, setShowNewKeyModal] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyPermissions, setNewKeyPermissions] = useState<string[]>(['read'])
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // API Keys
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: 'key-1',
      name: 'Production API',
      key: 'aqw_sk_live_7x8k2m9n4p5q6r3s1t0u',
      status: 'active',
      createdAt: '2026-01-01T08:00:00Z',
      lastUsed: new Date().toISOString(),
      permissions: ['read', 'write', 'admin'],
      usageCount: 15420
    },
    {
      id: 'key-2',
      name: 'Dashboard Integration',
      key: 'aqw_sk_live_3a4b5c6d7e8f9g0h1i2j',
      status: 'active',
      createdAt: '2026-01-10T10:30:00Z',
      lastUsed: new Date(Date.now() - 3600000).toISOString(),
      permissions: ['read'],
      usageCount: 8934
    },
    {
      id: 'key-3',
      name: 'Mobile App (Legacy)',
      key: 'aqw_sk_live_9z8y7x6w5v4u3t2s1r0q',
      status: 'revoked',
      createdAt: '2025-06-15T14:20:00Z',
      lastUsed: '2025-12-01T09:15:00Z',
      permissions: ['read', 'write'],
      usageCount: 45231
    }
  ])

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([
    { id: '1', user: 'admin', role: 'Administrator', action: 'Login', resource: 'Auth', ip: '192.168.8.100', location: 'Lusaka, ZM', device: 'Chrome/Windows', timestamp: new Date().toISOString(), status: 'success' },
    { id: '2', user: 'operator', role: 'Operator', action: 'View Dashboard', resource: 'Dashboard', ip: '192.168.8.101', location: 'Lusaka, ZM', device: 'Firefox/Linux', timestamp: new Date(Date.now() - 300000).toISOString(), status: 'success' },
    { id: '3', user: 'unknown', role: 'Unknown', action: 'Login Attempt', resource: 'Auth', ip: '45.33.12.99', location: 'Unknown', device: 'Bot/Unknown', timestamp: new Date(Date.now() - 900000).toISOString(), status: 'failed', details: 'Invalid credentials (attempt 3/5)' },
    { id: '4', user: 'admin', role: 'Administrator', action: 'API Key Generated', resource: 'Security', ip: '192.168.8.100', location: 'Lusaka, ZM', device: 'Chrome/Windows', timestamp: new Date(Date.now() - 1800000).toISOString(), status: 'success' },
    { id: '5', user: 'technician', role: 'Technician', action: 'Work Order Updated', resource: 'Work Orders', ip: '192.168.8.105', location: 'Kabulonga, ZM', device: 'Safari/iOS', timestamp: new Date(Date.now() - 3600000).toISOString(), status: 'success' },
    { id: '6', user: 'system', role: 'System', action: 'Backup Completed', resource: 'Database', ip: '127.0.0.1', location: 'Local', device: 'System', timestamp: new Date(Date.now() - 7200000).toISOString(), status: 'success' },
    { id: '7', user: 'unknown', role: 'Unknown', action: 'Brute Force Detected', resource: 'Auth', ip: '185.220.101.45', location: 'Russia', device: 'Unknown', timestamp: new Date(Date.now() - 10800000).toISOString(), status: 'failed', details: 'IP blocked for 24 hours' },
    { id: '8', user: 'operator', role: 'Operator', action: 'Export Data', resource: 'Reports', ip: '192.168.8.101', location: 'Lusaka, ZM', device: 'Firefox/Linux', timestamp: new Date(Date.now() - 14400000).toISOString(), status: 'warning', details: 'Large data export (>100MB)' },
  ])

  // Active Sessions
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([
    { id: 'sess-1', user: 'admin', role: 'Administrator', device: 'Desktop', browser: 'Chrome 120', ip: '192.168.8.100', location: 'Lusaka, ZM', loginTime: new Date(Date.now() - 3600000).toISOString(), lastActivity: new Date().toISOString(), current: true },
    { id: 'sess-2', user: 'admin', role: 'Administrator', device: 'Mobile', browser: 'Safari iOS', ip: '192.168.8.150', location: 'Lusaka, ZM', loginTime: new Date(Date.now() - 86400000).toISOString(), lastActivity: new Date(Date.now() - 1800000).toISOString(), current: false },
    { id: 'sess-3', user: 'operator', role: 'Operator', device: 'Desktop', browser: 'Firefox 121', ip: '192.168.8.101', location: 'Lusaka, ZM', loginTime: new Date(Date.now() - 7200000).toISOString(), lastActivity: new Date(Date.now() - 300000).toISOString(), current: false },
  ])

  // Security Settings
  const [settings, setSettings] = useState<SecuritySettings>({
    sessionTimeout: 30,
    maxFailedAttempts: 5,
    lockoutDuration: 15,
    requireTwoFactor: true,
    passwordMinLength: 8,
    requireUppercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    passwordExpiry: 90,
    ipWhitelist: ['192.168.8.0/24'],
    alertOnFailedLogin: true,
    alertOnNewDevice: true
  })

  // Stats
  const securityStats = {
    status: 'secure',
    activeKeys: apiKeys.filter(k => k.status === 'active').length,
    failedLogins24h: auditLogs.filter(l => l.status === 'failed' && l.action.includes('Login')).length,
    activeSessions: activeSessions.length,
    blockedIPs: 3,
    lastScan: new Date(Date.now() - 1800000).toISOString()
  }

  const generateApiKey = () => {
    if (!newKeyName.trim()) return
    
    setIsGeneratingKey(true)
    
    // Simulate API call
    setTimeout(() => {
      const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
      let keyPart = ''
      for (let i = 0; i < 20; i++) {
        keyPart += chars.charAt(Math.floor(Math.random() * chars.length))
      }
      
      const newKey: ApiKey = {
        id: `key-${Date.now()}`,
        name: newKeyName,
        key: `aqw_sk_live_${keyPart}`,
        status: 'active',
        createdAt: new Date().toISOString(),
        lastUsed: null,
        permissions: newKeyPermissions,
        usageCount: 0
      }
      
      setApiKeys(prev => [newKey, ...prev])
      setIsGeneratingKey(false)
      setShowNewKeyModal(false)
      setNewKeyName('')
      setNewKeyPermissions(['read'])
      
      // Show the new key
      setShowApiKey(newKey.id)
    }, 1500)
  }

  const revokeApiKey = (keyId: string) => {
    setApiKeys(prev => prev.map(k => 
      k.id === keyId ? { ...k, status: 'revoked' as const } : k
    ))
  }

  const terminateSession = (sessionId: string) => {
    setActiveSessions(prev => prev.filter(s => s.id !== sessionId))
  }

  const copyToClipboard = (text: string, keyId: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(keyId)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const saveSettings = () => {
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }, 1000)
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-emerald-600 bg-emerald-50'
      case 'failed': return 'text-red-600 bg-red-50'
      case 'warning': return 'text-amber-600 bg-amber-50'
      case 'active': return 'text-emerald-600 bg-emerald-100'
      case 'revoked': return 'text-red-600 bg-red-100'
      case 'expired': return 'text-slate-600 bg-slate-100'
      default: return 'text-slate-600 bg-slate-100'
    }
  }

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = log.user.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.ip.includes(searchQuery)
    const matchesFilter = !filterStatus || log.status === filterStatus
    return matchesSearch && matchesFilter
  })

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-6 h-6 sm:w-7 sm:h-7 text-blue-600" />
            Security Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 sm:mt-1">
            Manage API keys, sessions, audit logs, and security policies
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2 ${
            securityStats.status === 'secure' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
          }`}>
            {securityStats.status === 'secure' ? (
              <><ShieldCheck className="w-4 h-4" /> System Secure</>
            ) : (
              <><ShieldAlert className="w-4 h-4" /> Security Alert</>
            )}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-100 rounded-xl overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview', icon: Shield },
          { id: 'apikeys', label: 'API Keys', icon: Key },
          { id: 'sessions', label: 'Sessions', icon: Monitor },
          { id: 'audit', label: 'Audit Log', icon: Activity },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Security Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
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
                  <p className="text-2xl font-bold text-slate-900">{securityStats.activeKeys}</p>
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
                  <p className="text-2xl font-bold text-slate-900">{securityStats.failedLogins24h}</p>
                  <p className="text-xs text-slate-500">Failed Logins (24h)</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Monitor className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{securityStats.activeSessions}</p>
                  <p className="text-xs text-slate-500">Active Sessions</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                  <Ban className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{securityStats.blockedIPs}</p>
                  <p className="text-xs text-slate-500">Blocked IPs</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Security Checklist */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Security Checklist</h2>
              <div className="space-y-3">
                {[
                  { label: 'Two-Factor Authentication', enabled: settings.requireTwoFactor, description: 'Required for admins' },
                  { label: 'Strong Password Policy', enabled: settings.requireSpecialChars, description: 'Min 8 chars with special characters' },
                  { label: 'Session Timeout', enabled: settings.sessionTimeout <= 30, description: `${settings.sessionTimeout} minutes` },
                  { label: 'Failed Login Alerts', enabled: settings.alertOnFailedLogin, description: 'Email notifications enabled' },
                  { label: 'IP Whitelist', enabled: settings.ipWhitelist.length > 0, description: `${settings.ipWhitelist.length} IP ranges` },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {item.enabled ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium text-slate-900">{item.label}</p>
                        <p className="text-xs text-slate-500">{item.description}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      item.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {item.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Security Events */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Recent Security Events</h2>
              <div className="space-y-3">
                {auditLogs.slice(0, 5).map(log => (
                  <div key={log.id} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getStatusColor(log.status)}`}>
                      {log.status === 'success' ? <CheckCircle className="w-4 h-4" /> :
                       log.status === 'failed' ? <XCircle className="w-4 h-4" /> :
                       <AlertTriangle className="w-4 h-4" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-900">{log.action}</p>
                        <span className="text-xs text-slate-500">{formatTime(log.timestamp)}</span>
                      </div>
                      <p className="text-xs text-slate-500">{log.user} • {log.ip}</p>
                      {log.details && (
                        <p className="text-xs text-amber-600 mt-1">{log.details}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <button 
                onClick={() => setActiveTab('audit')}
                className="w-full mt-4 px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                View All Activity →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'apikeys' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">Manage API keys for external integrations</p>
            <button
              onClick={() => setShowNewKeyModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              Generate New Key
            </button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {apiKeys.map(key => (
              <div key={key.id} className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-slate-900">{key.name}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(key.status)}`}>
                        {key.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Created {new Date(key.createdAt).toLocaleDateString()} • 
                      {key.lastUsed ? ` Last used ${formatTime(key.lastUsed)}` : ' Never used'} • 
                      {key.usageCount.toLocaleString()} requests
                    </p>
                  </div>
                  {key.status === 'active' && (
                    <button
                      onClick={() => revokeApiKey(key.id)}
                      className="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition-colors"
                    >
                      Revoke
                    </button>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  <code className="flex-1 px-3 py-2 bg-slate-100 rounded-lg text-sm font-mono text-slate-600 overflow-hidden">
                    {showApiKey === key.id ? key.key : '•'.repeat(32)}
                  </code>
                  <button 
                    onClick={() => setShowApiKey(showApiKey === key.id ? null : key.id)}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    title={showApiKey === key.id ? 'Hide' : 'Show'}
                  >
                    {showApiKey === key.id ? <EyeOff className="w-4 h-4 text-slate-500" /> : <Eye className="w-4 h-4 text-slate-500" />}
                  </button>
                  <button 
                    onClick={() => copyToClipboard(key.key, key.id)}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Copy"
                  >
                    {copiedKey === key.id ? <CheckCircle className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4 text-slate-500" />}
                  </button>
                </div>

                <div className="flex gap-2 mt-3">
                  {key.permissions.map(perm => (
                    <span key={perm} className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs capitalize">
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sessions Tab */}
      {activeTab === 'sessions' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">{activeSessions.length} active sessions</p>
            <button
              onClick={() => setActiveSessions(prev => prev.filter(s => s.current))}
              className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm font-medium"
            >
              <Ban className="w-4 h-4" />
              Terminate All Other Sessions
            </button>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
            {activeSessions.map(session => (
              <div key={session.id} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    session.device === 'Desktop' ? 'bg-blue-100' : 'bg-purple-100'
                  }`}>
                    {session.device === 'Desktop' ? (
                      <Monitor className={`w-5 h-5 ${session.device === 'Desktop' ? 'text-blue-600' : 'text-purple-600'}`} />
                    ) : (
                      <Smartphone className="w-5 h-5 text-purple-600" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-slate-900">{session.browser}</p>
                      {session.current && (
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded-full">Current</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500">
                      {session.user} ({session.role}) • {session.ip} • {session.location}
                    </p>
                    <p className="text-xs text-slate-400">
                      Login: {new Date(session.loginTime).toLocaleString()} • Last active: {formatTime(session.lastActivity)}
                    </p>
                  </div>
                </div>
                {!session.current && (
                  <button
                    onClick={() => terminateSession(session.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Terminate session"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Log Tab */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search by user, action, or IP..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-sm"
              />
            </div>
            <div className="flex gap-2">
              {['success', 'failed', 'warning'].map(status => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(filterStatus === status ? null : status)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                    filterStatus === status
                      ? status === 'success' ? 'bg-emerald-100 text-emerald-700' :
                        status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-amber-100 text-amber-700'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
            <button className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>

          {/* Log Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Time</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">User</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Action</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">IP / Location</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLogs.map(log => (
                    <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-2 text-sm text-slate-500">
                          <Clock className="w-3 h-3" />
                          {formatTime(log.timestamp)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{log.user}</p>
                          <p className="text-xs text-slate-500">{log.role}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm text-slate-900">{log.action}</p>
                          <p className="text-xs text-slate-500">{log.resource}</p>
                          {log.details && (
                            <p className="text-xs text-amber-600 mt-1">{log.details}</p>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <code className="text-xs font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded">{log.ip}</code>
                          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {log.location}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                          {log.status === 'success' ? <CheckCircle className="w-3 h-3" /> :
                           log.status === 'failed' ? <XCircle className="w-3 h-3" /> :
                           <AlertTriangle className="w-3 h-3" />}
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Session Settings */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                Session Settings
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Session Timeout (minutes)</label>
                  <input 
                    type="number" 
                    value={settings.sessionTimeout}
                    onChange={(e) => setSettings(prev => ({ ...prev, sessionTimeout: parseInt(e.target.value) || 30 }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  <p className="text-xs text-slate-500 mt-1">Inactive users will be logged out after this time</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Max Failed Login Attempts</label>
                  <input 
                    type="number" 
                    value={settings.maxFailedAttempts}
                    onChange={(e) => setSettings(prev => ({ ...prev, maxFailedAttempts: parseInt(e.target.value) || 5 }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Lockout Duration (minutes)</label>
                  <input 
                    type="number" 
                    value={settings.lockoutDuration}
                    onChange={(e) => setSettings(prev => ({ ...prev, lockoutDuration: parseInt(e.target.value) || 15 }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Password Policy */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Lock className="w-5 h-5 text-purple-600" />
                Password Policy
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Minimum Password Length</label>
                  <input 
                    type="number" 
                    value={settings.passwordMinLength}
                    onChange={(e) => setSettings(prev => ({ ...prev, passwordMinLength: parseInt(e.target.value) || 8 }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Password Expiry (days)</label>
                  <input 
                    type="number" 
                    value={settings.passwordExpiry}
                    onChange={(e) => setSettings(prev => ({ ...prev, passwordExpiry: parseInt(e.target.value) || 90 }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                  <p className="text-xs text-slate-500 mt-1">Set to 0 for no expiry</p>
                </div>
                <div className="space-y-2">
                  {[
                    { key: 'requireUppercase', label: 'Require uppercase letters' },
                    { key: 'requireNumbers', label: 'Require numbers' },
                    { key: 'requireSpecialChars', label: 'Require special characters' },
                  ].map(item => (
                    <label key={item.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg cursor-pointer">
                      <span className="text-sm text-slate-700">{item.label}</span>
                      <button
                        onClick={() => setSettings(prev => ({ ...prev, [item.key]: !prev[item.key as keyof SecuritySettings] }))}
                        className={`relative w-10 h-5 rounded-full transition-colors ${
                          settings[item.key as keyof SecuritySettings] ? 'bg-blue-600' : 'bg-slate-300'
                        }`}
                      >
                        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          settings[item.key as keyof SecuritySettings] ? 'left-5' : 'left-0.5'
                        }`} />
                      </button>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Two-Factor Authentication */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Fingerprint className="w-5 h-5 text-emerald-600" />
                Two-Factor Authentication
              </h2>
              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 bg-slate-50 rounded-lg cursor-pointer">
                  <div>
                    <p className="font-medium text-slate-900">Require 2FA for Admins</p>
                    <p className="text-xs text-slate-500">All admin accounts must use 2FA</p>
                  </div>
                  <button
                    onClick={() => setSettings(prev => ({ ...prev, requireTwoFactor: !prev.requireTwoFactor }))}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      settings.requireTwoFactor ? 'bg-emerald-500' : 'bg-slate-300'
                    }`}
                  >
                    <span className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                      settings.requireTwoFactor ? 'left-7' : 'left-1'
                    }`} />
                  </button>
                </label>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <p className="text-sm text-blue-800">
                    <strong>Supported methods:</strong> Authenticator apps (Google, Microsoft), SMS codes, Email verification
                  </p>
                </div>
              </div>
            </div>

            {/* Alerts & Notifications */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5 text-amber-600" />
                Security Alerts
              </h2>
              <div className="space-y-3">
                {[
                  { key: 'alertOnFailedLogin', label: 'Alert on failed login attempts', desc: 'Get notified after 3+ failed attempts' },
                  { key: 'alertOnNewDevice', label: 'Alert on new device login', desc: 'Get notified when logging in from a new device' },
                ].map(item => (
                  <label key={item.key} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg cursor-pointer">
                    <div>
                      <p className="font-medium text-slate-900">{item.label}</p>
                      <p className="text-xs text-slate-500">{item.desc}</p>
                    </div>
                    <button
                      onClick={() => setSettings(prev => ({ ...prev, [item.key]: !prev[item.key as keyof SecuritySettings] }))}
                      className={`relative w-10 h-5 rounded-full transition-colors ${
                        settings[item.key as keyof SecuritySettings] ? 'bg-blue-600' : 'bg-slate-300'
                      }`}
                    >
                      <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                        settings[item.key as keyof SecuritySettings] ? 'left-5' : 'left-0.5'
                      }`} />
                    </button>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-2">
              {saveSuccess && (
                <span className="flex items-center gap-2 text-sm text-emerald-600">
                  <CheckCircle className="w-4 h-4" />
                  Settings saved successfully
                </span>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setSettings({
                  sessionTimeout: 30,
                  maxFailedAttempts: 5,
                  lockoutDuration: 15,
                  requireTwoFactor: true,
                  passwordMinLength: 8,
                  requireUppercase: true,
                  requireNumbers: true,
                  requireSpecialChars: true,
                  passwordExpiry: 90,
                  ipWhitelist: ['192.168.8.0/24'],
                  alertOnFailedLogin: true,
                  alertOnNewDevice: true
                })}
                className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg hover:bg-white text-sm font-medium text-slate-600"
              >
                <RotateCcw className="w-4 h-4" />
                Reset to Defaults
              </button>
              <button
                onClick={saveSettings}
                disabled={isSaving}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {isSaving ? (
                  <><RefreshCw className="w-4 h-4 animate-spin" /> Saving...</>
                ) : (
                  <><Save className="w-4 h-4" /> Save Settings</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New API Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Generate New API Key</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Key Name</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Mobile App Integration"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Permissions</label>
                <div className="space-y-2">
                  {['read', 'write', 'admin'].map(perm => (
                    <label key={perm} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newKeyPermissions.includes(perm)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewKeyPermissions(prev => [...prev, perm])
                          } else {
                            setNewKeyPermissions(prev => prev.filter(p => p !== perm))
                          }
                        }}
                        className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-900 capitalize">{perm}</p>
                        <p className="text-xs text-slate-500">
                          {perm === 'read' && 'View data and metrics'}
                          {perm === 'write' && 'Create and update records'}
                          {perm === 'admin' && 'Full administrative access'}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowNewKeyModal(false)}
                className="flex-1 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm font-medium text-slate-600"
              >
                Cancel
              </button>
              <button
                onClick={generateApiKey}
                disabled={!newKeyName.trim() || isGeneratingKey}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50"
              >
                {isGeneratingKey ? (
                  <><RefreshCw className="w-4 h-4 animate-spin" /> Generating...</>
                ) : (
                  <><Key className="w-4 h-4" /> Generate Key</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
