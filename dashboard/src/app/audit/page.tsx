'use client'

import { useState } from 'react'
import { 
  Shield, Clock, User, FileText, Search, Filter, Download,
  Eye, Edit, Trash2, AlertTriangle, CheckCircle, XCircle,
  ChevronDown, ChevronRight, Calendar, Activity, Lock
} from 'lucide-react'

// Sample audit log data
const auditLogs = [
  {
    id: 'AUD-001',
    timestamp: '2025-01-15 14:32:15',
    user: 'admin@lwsc.co.zm',
    userName: 'John Mwansa',
    role: 'Administrator',
    action: 'LOGIN',
    resource: 'System',
    details: 'Successful login from 196.12.45.XXX',
    ip: '196.12.45.XXX',
    status: 'success'
  },
  {
    id: 'AUD-002',
    timestamp: '2025-01-15 14:28:42',
    user: 'operator@lwsc.co.zm',
    userName: 'Mary Banda',
    role: 'Operator',
    action: 'UPDATE',
    resource: 'Leak #LK-047',
    details: 'Status changed from "detected" to "assigned"',
    ip: '196.12.45.XXX',
    status: 'success'
  },
  {
    id: 'AUD-003',
    timestamp: '2025-01-15 14:15:30',
    user: 'admin@lwsc.co.zm',
    userName: 'John Mwansa',
    role: 'Administrator',
    action: 'EXPORT',
    resource: 'Monthly Report',
    details: 'Exported NRW Analysis Report (January 2025)',
    ip: '196.12.45.XXX',
    status: 'success'
  },
  {
    id: 'AUD-004',
    timestamp: '2025-01-15 13:45:18',
    user: 'field@lwsc.co.zm',
    userName: 'Peter Chanda',
    role: 'Field Technician',
    action: 'CREATE',
    resource: 'Work Order #WO-128',
    details: 'Created work order for leak repair at Great East Rd',
    ip: '196.12.48.XXX',
    status: 'success'
  },
  {
    id: 'AUD-005',
    timestamp: '2025-01-15 12:30:00',
    user: 'unknown',
    userName: 'Unknown',
    role: 'N/A',
    action: 'LOGIN',
    resource: 'System',
    details: 'Failed login attempt - invalid password (3rd attempt)',
    ip: '41.72.XXX.XXX',
    status: 'failed'
  },
  {
    id: 'AUD-006',
    timestamp: '2025-01-15 11:20:45',
    user: 'admin@lwsc.co.zm',
    userName: 'John Mwansa',
    role: 'Administrator',
    action: 'UPDATE',
    resource: 'System Settings',
    details: 'Updated NRW alert threshold from 35% to 32%',
    ip: '196.12.45.XXX',
    status: 'success'
  },
  {
    id: 'AUD-007',
    timestamp: '2025-01-15 10:15:22',
    user: 'api-service',
    userName: 'API Service',
    role: 'System',
    action: 'CREATE',
    resource: 'Alert #ALT-892',
    details: 'Automated alert created for high NRW in Matero DMA',
    ip: 'Internal',
    status: 'success'
  },
]

// Compliance checklist
const complianceItems = [
  {
    category: 'Data Protection',
    items: [
      { id: 'dp1', name: 'Data Encryption at Rest', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'dp2', name: 'Data Encryption in Transit (TLS)', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'dp3', name: 'Personal Data Access Logs', status: 'compliant', lastChecked: '2025-01-14' },
      { id: 'dp4', name: 'Data Retention Policy', status: 'compliant', lastChecked: '2025-01-10' },
    ]
  },
  {
    category: 'Access Control',
    items: [
      { id: 'ac1', name: 'Role-Based Access Control (RBAC)', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'ac2', name: 'Multi-Factor Authentication', status: 'partial', lastChecked: '2025-01-12' },
      { id: 'ac3', name: 'Password Policy Enforcement', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'ac4', name: 'Session Timeout Configuration', status: 'compliant', lastChecked: '2025-01-14' },
    ]
  },
  {
    category: 'System Integrity',
    items: [
      { id: 'si1', name: 'Automated Backups', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'si2', name: 'Backup Recovery Testing', status: 'partial', lastChecked: '2024-12-15' },
      { id: 'si3', name: 'System Monitoring', status: 'compliant', lastChecked: '2025-01-15' },
      { id: 'si4', name: 'Incident Response Plan', status: 'compliant', lastChecked: '2025-01-08' },
    ]
  },
  {
    category: 'Regulatory Compliance',
    items: [
      { id: 'rc1', name: 'NWASCO Reporting Standards', status: 'compliant', lastChecked: '2025-01-10' },
      { id: 'rc2', name: 'IWA Water Balance Guidelines', status: 'compliant', lastChecked: '2025-01-05' },
      { id: 'rc3', name: 'Environmental Compliance', status: 'compliant', lastChecked: '2025-01-01' },
      { id: 'rc4', name: 'Financial Audit Readiness', status: 'compliant', lastChecked: '2025-01-14' },
    ]
  },
]

export default function AuditPage() {
  const [activeTab, setActiveTab] = useState<'logs' | 'compliance'>('logs')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterAction, setFilterAction] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['Data Protection'])

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = 
      log.user.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resource.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.details.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesAction = filterAction === 'all' || log.action === filterAction
    const matchesStatus = filterStatus === 'all' || log.status === filterStatus
    
    return matchesSearch && matchesAction && matchesStatus
  })

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'LOGIN': return <User className="w-4 h-4" />
      case 'CREATE': return <FileText className="w-4 h-4" />
      case 'UPDATE': return <Edit className="w-4 h-4" />
      case 'DELETE': return <Trash2 className="w-4 h-4" />
      case 'EXPORT': return <Download className="w-4 h-4" />
      case 'VIEW': return <Eye className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getActionColor = (action: string) => {
    switch (action) {
      case 'LOGIN': return 'bg-blue-100 text-blue-700'
      case 'CREATE': return 'bg-emerald-100 text-emerald-700'
      case 'UPDATE': return 'bg-amber-100 text-amber-700'
      case 'DELETE': return 'bg-red-100 text-red-700'
      case 'EXPORT': return 'bg-purple-100 text-purple-700'
      case 'VIEW': return 'bg-slate-100 text-slate-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  const getComplianceStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'bg-emerald-100 text-emerald-700'
      case 'partial': return 'bg-amber-100 text-amber-700'
      case 'non-compliant': return 'bg-red-100 text-red-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    )
  }

  // Calculate compliance summary
  const totalItems = complianceItems.reduce((sum, cat) => sum + cat.items.length, 0)
  const compliantItems = complianceItems.reduce(
    (sum, cat) => sum + cat.items.filter(i => i.status === 'compliant').length, 0
  )
  const partialItems = complianceItems.reduce(
    (sum, cat) => sum + cat.items.filter(i => i.status === 'partial').length, 0
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-3 sm:p-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-3xl font-bold text-slate-900">Audit & Compliance</h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-0.5">System audit trail and compliance monitoring</p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs sm:text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
              <Download className="w-4 h-4" />
              Export Logs
            </button>
          </div>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex bg-white rounded-xl shadow-sm p-1 mb-4 sm:mb-6">
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'logs'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Clock className="w-4 h-4" />
          Audit Logs
        </button>
        <button
          onClick={() => setActiveTab('compliance')}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'compliance'
              ? 'bg-blue-600 text-white'
              : 'text-slate-600 hover:bg-slate-50'
          }`}
        >
          <Shield className="w-4 h-4" />
          Compliance
        </button>
      </div>

      {activeTab === 'logs' ? (
        <div className="space-y-4">
          {/* Filters */}
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
            <div className="flex flex-col sm:flex-row gap-3">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search logs..."
                  className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              {/* Action Filter */}
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <select
                  value={filterAction}
                  onChange={(e) => setFilterAction(e.target.value)}
                  className="pl-10 pr-8 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
                >
                  <option value="all">All Actions</option>
                  <option value="LOGIN">Login</option>
                  <option value="CREATE">Create</option>
                  <option value="UPDATE">Update</option>
                  <option value="DELETE">Delete</option>
                  <option value="EXPORT">Export</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>

              {/* Status Filter */}
              <div className="relative">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white pr-8"
                >
                  <option value="all">All Status</option>
                  <option value="success">Success</option>
                  <option value="failed">Failed</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* Logs Table */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3">Timestamp</th>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3">User</th>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3">Action</th>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3">Resource</th>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3 hidden lg:table-cell">Details</th>
                    <th className="text-left text-xs font-semibold text-slate-600 px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-xs sm:text-sm text-slate-600 whitespace-nowrap">{log.timestamp}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-xs sm:text-sm font-medium text-slate-900">{log.userName}</p>
                          <p className="text-[10px] text-slate-500">{log.role}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] sm:text-xs font-medium ${getActionColor(log.action)}`}>
                          {getActionIcon(log.action)}
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs sm:text-sm text-slate-700">{log.resource}</span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-xs text-slate-500 line-clamp-1">{log.details}</span>
                      </td>
                      <td className="px-4 py-3">
                        {log.status === 'success' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600">
                            <CheckCircle className="w-4 h-4" />
                            <span className="text-xs hidden sm:inline">Success</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-600">
                            <XCircle className="w-4 h-4" />
                            <span className="text-xs hidden sm:inline">Failed</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <p className="text-xs text-slate-500">Showing {filteredLogs.length} of {auditLogs.length} logs</p>
              <div className="flex gap-1">
                <button className="px-3 py-1 text-xs font-medium text-slate-600 bg-slate-100 rounded hover:bg-slate-200">Previous</button>
                <button className="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded">1</button>
                <button className="px-3 py-1 text-xs font-medium text-slate-600 bg-slate-100 rounded hover:bg-slate-200">2</button>
                <button className="px-3 py-1 text-xs font-medium text-slate-600 bg-slate-100 rounded hover:bg-slate-200">Next</button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Compliance Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Compliant</p>
                  <p className="text-xl font-bold text-emerald-600">{compliantItems}/{totalItems}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Partial</p>
                  <p className="text-xl font-bold text-amber-600">{partialItems}/{totalItems}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Overall Score</p>
                  <p className="text-xl font-bold text-blue-600">{Math.round((compliantItems / totalItems) * 100)}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Compliance Checklist */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            {complianceItems.map((category, categoryIndex) => (
              <div key={category.category} className={categoryIndex > 0 ? 'border-t border-slate-100' : ''}>
                <button
                  onClick={() => toggleCategory(category.category)}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Lock className="w-5 h-5 text-slate-400" />
                    <span className="text-sm font-semibold text-slate-900">{category.category}</span>
                    <span className="text-xs text-slate-400">
                      ({category.items.filter(i => i.status === 'compliant').length}/{category.items.length} compliant)
                    </span>
                  </div>
                  <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${
                    expandedCategories.includes(category.category) ? 'rotate-90' : ''
                  }`} />
                </button>
                
                {expandedCategories.includes(category.category) && (
                  <div className="px-4 pb-4">
                    <div className="space-y-2">
                      {category.items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            {item.status === 'compliant' ? (
                              <CheckCircle className="w-5 h-5 text-emerald-500" />
                            ) : item.status === 'partial' ? (
                              <AlertTriangle className="w-5 h-5 text-amber-500" />
                            ) : (
                              <XCircle className="w-5 h-5 text-red-500" />
                            )}
                            <span className="text-sm text-slate-700">{item.name}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] text-slate-400">
                              Checked: {item.lastChecked}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-[10px] font-medium capitalize ${getComplianceStatusColor(item.status)}`}>
                              {item.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Certifications */}
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-4 sm:p-6 text-white">
            <h3 className="text-sm sm:text-base font-semibold mb-4">System Certifications</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { name: 'ISO 27001', status: 'Certified', year: '2024' },
                { name: 'GDPR', status: 'Compliant', year: '2024' },
                { name: 'NWASCO', status: 'Approved', year: '2025' },
                { name: 'IWA', status: 'Aligned', year: '2024' },
              ].map((cert) => (
                <div key={cert.name} className="bg-white/10 rounded-lg p-3 text-center">
                  <p className="text-xs opacity-80">{cert.status}</p>
                  <p className="text-sm font-bold">{cert.name}</p>
                  <p className="text-[10px] opacity-60">{cert.year}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
