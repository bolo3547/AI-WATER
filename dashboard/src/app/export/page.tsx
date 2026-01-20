'use client'

import { useState } from 'react'
import { 
  Download, FileText, FileSpreadsheet, Database, Calendar,
  Filter, Check, ChevronDown, Loader2, Clock, FolderDown,
  Table, BarChart3, MapPin, AlertTriangle, Droplets
} from 'lucide-react'

// Available data types for export
const dataTypes = [
  {
    id: 'nrw-summary',
    name: 'NRW Summary Data',
    description: 'Daily/weekly/monthly NRW rates and trends',
    icon: Droplets,
    fields: ['Date', 'System Input', 'Billed Consumption', 'NRW Volume', 'NRW Rate', 'Revenue Lost'],
    category: 'analytics'
  },
  {
    id: 'leak-records',
    name: 'Leak Detection Records',
    description: 'All detected leaks with locations and status',
    icon: AlertTriangle,
    fields: ['Leak ID', 'Detection Date', 'Location', 'DMA', 'Severity', 'Flow Rate', 'Status', 'Repair Date'],
    category: 'operations'
  },
  {
    id: 'dma-performance',
    name: 'DMA Performance',
    description: 'District Metered Area performance metrics',
    icon: MapPin,
    fields: ['DMA Name', 'NRW Rate', 'Active Leaks', 'Sensors', 'MNF', 'Water Loss'],
    category: 'analytics'
  },
  {
    id: 'sensor-data',
    name: 'Sensor Readings',
    description: 'Raw sensor data with timestamps',
    icon: Database,
    fields: ['Timestamp', 'Sensor ID', 'Flow Rate', 'Pressure', 'Temperature', 'Battery'],
    category: 'technical'
  },
  {
    id: 'financial',
    name: 'Financial Impact Data',
    description: 'Revenue loss and recovery metrics',
    icon: BarChart3,
    fields: ['Period', 'Water Lost (m³)', 'Revenue Lost (ZMW)', 'Revenue Recovered', 'Net Impact'],
    category: 'financial'
  },
  {
    id: 'work-orders',
    name: 'Work Orders',
    description: 'Field crew work orders and repairs',
    icon: Table,
    fields: ['WO Number', 'Created', 'Type', 'Location', 'Assigned To', 'Status', 'Completed'],
    category: 'operations'
  },
]

// Recent exports history
const recentExports = [
  { name: 'NRW_Summary_Jan2025.xlsx', date: '2025-01-15 14:30', size: '2.4 MB', status: 'completed' },
  { name: 'Leak_Records_Q4_2024.csv', date: '2025-01-14 09:15', size: '1.8 MB', status: 'completed' },
  { name: 'DMA_Performance_2024.pdf', date: '2025-01-12 16:45', size: '3.2 MB', status: 'completed' },
  { name: 'Sensor_Data_Dec2024.json', date: '2025-01-10 11:20', size: '15.6 MB', status: 'completed' },
]

export default function ExportPage() {
  const [selectedData, setSelectedData] = useState<string[]>([])
  const [format, setFormat] = useState<'csv' | 'xlsx' | 'json' | 'pdf'>('xlsx')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [selectedDMAs, setSelectedDMAs] = useState<string[]>([])
  const [isExporting, setIsExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  const toggleDataSelection = (id: string) => {
    setSelectedData(prev =>
      prev.includes(id)
        ? prev.filter(d => d !== id)
        : [...prev, id]
    )
  }

  const handleExport = () => {
    if (selectedData.length === 0) return
    
    setIsExporting(true)
    setExportProgress(0)
    
    const interval = setInterval(() => {
      setExportProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsExporting(false)
          return 100
        }
        return prev + 15
      })
    }, 200)
  }

  const filteredDataTypes = dataTypes.filter(
    dt => categoryFilter === 'all' || dt.category === categoryFilter
  )

  const formatOptions = [
    { id: 'xlsx', name: 'Excel (.xlsx)', icon: FileSpreadsheet, color: 'text-green-600' },
    { id: 'csv', name: 'CSV (.csv)', icon: FileText, color: 'text-blue-600' },
    { id: 'json', name: 'JSON (.json)', icon: Database, color: 'text-amber-600' },
    { id: 'pdf', name: 'PDF (.pdf)', icon: FileText, color: 'text-red-600' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-3 sm:p-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-xl sm:text-3xl font-bold text-slate-900">Data Export</h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-0.5">Export system data in multiple formats</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Data Selection */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <h2 className="text-sm sm:text-base font-semibold text-slate-900">Select Data to Export</h2>
              
              {/* Category Filter */}
              <div className="flex gap-2">
                {['all', 'analytics', 'operations', 'financial', 'technical'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategoryFilter(cat)}
                    className={`px-2 sm:px-3 py-1 text-[10px] sm:text-xs font-medium rounded-lg transition-colors capitalize ${
                      categoryFilter === cat
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filteredDataTypes.map((dataType) => {
                const Icon = dataType.icon
                const isSelected = selectedData.includes(dataType.id)
                
                return (
                  <button
                    key={dataType.id}
                    onClick={() => toggleDataSelection(dataType.id)}
                    className={`w-full text-left p-3 sm:p-4 rounded-xl border-2 transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {isSelected ? (
                          <Check className="w-4 h-4 sm:w-5 sm:h-5" />
                        ) : (
                          <Icon className="w-4 h-4 sm:w-5 sm:h-5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-xs sm:text-sm font-semibold text-slate-900">{dataType.name}</h3>
                          <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded text-[9px] capitalize">
                            {dataType.category}
                          </span>
                        </div>
                        <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">{dataType.description}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {dataType.fields.slice(0, 4).map((field, i) => (
                            <span key={i} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px]">
                              {field}
                            </span>
                          ))}
                          {dataType.fields.length > 4 && (
                            <span className="px-1.5 py-0.5 bg-slate-100 text-slate-400 rounded text-[9px]">
                              +{dataType.fields.length - 4} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div className="space-y-4">
          {/* Format Selection */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Export Format</h3>
            <div className="grid grid-cols-2 gap-2">
              {formatOptions.map((fmt) => {
                const Icon = fmt.icon
                return (
                  <button
                    key={fmt.id}
                    onClick={() => setFormat(fmt.id as typeof format)}
                    className={`flex items-center gap-2 p-3 rounded-xl border-2 transition-all ${
                      format === fmt.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <Icon className={`w-5 h-5 ${format === fmt.id ? 'text-blue-600' : fmt.color}`} />
                    <span className="text-xs font-medium text-slate-700">{fmt.name}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Date Range */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Date Range</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-slate-500 mb-1">From</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                    className="w-full pl-10 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">To</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                    className="w-full pl-10 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              {/* Quick presets */}
              <div className="flex flex-wrap gap-1.5 pt-2">
                {['Today', 'Last 7 Days', 'This Month', 'Last Month', 'This Year'].map((preset) => (
                  <button
                    key={preset}
                    className="px-2 py-1 text-[10px] font-medium text-slate-600 bg-slate-100 rounded hover:bg-slate-200 transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* DMA Filter */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Filter by DMA</h3>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <select 
                className="w-full pl-10 pr-8 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
              >
                <option value="">All DMAs</option>
                <option value="woodlands">Woodlands</option>
                <option value="kabulonga">Kabulonga</option>
                <option value="roma">Roma</option>
                <option value="matero">Matero</option>
                <option value="chilenje">Chilenje</option>
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {/* Export Button */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            {isExporting ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    Preparing export...
                  </span>
                  <span className="font-semibold text-blue-600">{exportProgress}%</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress}%` }}
                  />
                </div>
              </div>
            ) : exportProgress === 100 ? (
              <div className="text-center">
                <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Check className="w-6 h-6 text-emerald-600" />
                </div>
                <p className="text-sm font-medium text-emerald-600 mb-3">Export Complete!</p>
                <button className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors">
                  <FolderDown className="w-5 h-5" />
                  Download File
                </button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between text-sm text-slate-600 mb-3">
                  <span>{selectedData.length} dataset(s) selected</span>
                  <span className="font-medium">{format.toUpperCase()}</span>
                </div>
                <button
                  onClick={handleExport}
                  disabled={selectedData.length === 0}
                  className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-medium transition-all ${
                    selectedData.length > 0
                      ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-600/25'
                      : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  <Download className="w-5 h-5" />
                  Export Data
                </button>
              </>
            )}
          </div>

          {/* Recent Exports */}
          <div className="bg-white rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100">
            <h3 className="text-sm sm:text-base font-semibold text-slate-900 mb-4">Recent Exports</h3>
            <div className="space-y-2">
              {recentExports.map((exp, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-2 sm:p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-slate-900 truncate">{exp.name}</p>
                      <p className="text-[10px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {exp.date}
                      </p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs text-slate-600">{exp.size}</p>
                    <button className="text-[10px] text-blue-600 hover:underline">
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
