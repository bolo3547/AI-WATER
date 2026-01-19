'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  FileText, 
  Download,
  Calendar,
  Filter,
  Eye,
  Clock,
  CheckCircle,
  BarChart3,
  PieChart,
  TrendingDown,
  Loader2,
  RefreshCw,
  Trash2,
  AlertCircle,
  FileCheck,
  Sparkles,
  X,
  Share2,
  Mail,
  MessageCircle,
  Copy,
  Printer,
  ExternalLink
} from 'lucide-react'
import { SectionCard } from '@/components/ui/Cards'
import { Button, Tabs, Select } from '@/components/ui/Controls'

interface Report {
  id: string
  title: string
  type: string
  status: 'completed' | 'generating' | 'failed'
  generated: string | null
  size: string | null
  format: string
  content?: string
}

interface ReportTemplate {
  id: string
  name: string
  description: string
  icon: any
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  { id: 'monthly', name: 'Monthly NRW Report', description: 'Comprehensive monthly analysis of network performance', icon: BarChart3 },
  { id: 'weekly', name: 'Weekly Summary', description: 'Weekly overview of leak detections and actions', icon: Calendar },
  { id: 'dma', name: 'DMA Deep Dive', description: 'Detailed analysis for a specific DMA', icon: PieChart },
  { id: 'financial', name: 'Revenue Recovery', description: 'Financial impact and recovery metrics', icon: TrendingDown },
]

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('templates')
  const [typeFilter, setTypeFilter] = useState('')
  const [reports, setReports] = useState<Report[]>([])
  const [generating, setGenerating] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<any>(null)
  const [dmas, setDMAs] = useState<any[]>([])
  const [leaks, setLeaks] = useState<any[]>([])
  const [selectedDMA, setSelectedDMA] = useState('')
  const [viewingReport, setViewingReport] = useState<Report | null>(null)
  const [copied, setCopied] = useState(false)
  
  // Fetch data for report generation
  const fetchData = useCallback(async () => {
    try {
      const [metricsRes, dmasRes, leaksRes] = await Promise.all([
        fetch('/api/realtime?type=metrics'),
        fetch('/api/realtime?type=dmas'),
        fetch('/api/leaks')
      ])
      
      const [metricsData, dmasData, leaksData] = await Promise.all([
        metricsRes.json(),
        dmasRes.json(),
        leaksRes.json()
      ])
      
      if (metricsData.metrics) setMetrics(metricsData.metrics)
      if (dmasData.dmas) setDMAs(dmasData.dmas)
      if (leaksData.data) setLeaks(leaksData.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }, [])
  
  // Load saved reports from localStorage
  useEffect(() => {
    fetchData()
    
    const savedReports = localStorage.getItem('lwsc_reports')
    if (savedReports) {
      try {
        setReports(JSON.parse(savedReports))
      } catch (e) {
        setReports([])
      }
    }
  }, [fetchData])
  
  // Save reports to localStorage
  const saveReports = (newReports: Report[]) => {
    setReports(newReports)
    localStorage.setItem('lwsc_reports', JSON.stringify(newReports))
  }
  
  // Generate report using AI
  const generateReport = async (templateId: string) => {
    setGenerating(templateId)
    
    const template = REPORT_TEMPLATES.find(t => t.id === templateId)
    if (!template) return
    
    const now = new Date()
    const reportId = `RPT-${now.getFullYear()}-${String(reports.length + 1).padStart(3, '0')}`
    
    // Create generating placeholder
    const placeholderReport: Report = {
      id: reportId,
      title: `${template.name} - ${now.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}`,
      type: templateId,
      status: 'generating',
      generated: null,
      size: null,
      format: 'PDF'
    }
    
    const updatedReports = [placeholderReport, ...reports]
    saveReports(updatedReports)
    
    try {
      // Use AI to generate report content
      const prompt = generatePromptForReport(templateId, template.name)
      
      const response = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'report_generation',
          prompt: prompt,
          data: {
            metrics,
            dmas,
            leaks,
            selectedDMA,
            reportType: templateId,
            reportName: template.name,
            generatedAt: now.toISOString()
          }
        })
      })
      
      const data = await response.json()
      
      if (data.success || data.analysis) {
        const content = data.analysis || data.message || generateFallbackReport(templateId, template.name)
        
        // Update report with content
        const completedReport: Report = {
          ...placeholderReport,
          status: 'completed',
          generated: now.toISOString(),
          size: `${Math.round(content.length / 1024)} KB`,
          content: content
        }
        
        const finalReports = updatedReports.map(r => 
          r.id === reportId ? completedReport : r
        )
        saveReports(finalReports)
      } else {
        throw new Error('Failed to generate report')
      }
    } catch (error) {
      console.error('Report generation failed:', error)
      
      // Generate fallback report
      const fallbackContent = generateFallbackReport(templateId, template.name)
      
      const fallbackReport: Report = {
        ...placeholderReport,
        status: 'completed',
        generated: now.toISOString(),
        size: `${Math.round(fallbackContent.length / 1024)} KB`,
        content: fallbackContent
      }
      
      const finalReports = updatedReports.map(r => 
        r.id === reportId ? fallbackReport : r
      )
      saveReports(finalReports)
    } finally {
      setGenerating(null)
    }
  }
  
  const generatePromptForReport = (templateId: string, templateName: string): string => {
    const now = new Date()
    const monthName = now.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
    
    const baseData = `
Current System Metrics:
- Total NRW: ${metrics?.total_nrw_percent?.toFixed(1) || 'N/A'}%
- Active Sensors: ${metrics?.sensor_count || 0}
- DMAs Monitored: ${metrics?.dma_count || 0}
- Active Leaks: ${leaks.length}
- AI Confidence: ${metrics?.ai_confidence?.toFixed(0) || 94}%

DMA Performance:
${dmas.map(d => `- ${d.name}: NRW ${d.nrw_percent}%, Status: ${d.status}`).join('\n') || 'No DMA data available'}

Active Leak Alerts:
${leaks.length > 0 ? leaks.map(l => `- ${l.location}: ${l.estimated_loss} m³/day, ${l.confidence}% confidence, Status: ${l.status}`).join('\n') : 'No active leaks detected'}
`
    
    switch (templateId) {
      case 'monthly':
        return `Generate a comprehensive Monthly NRW Performance Report for ${monthName} for Lusaka Water Supply Company (LWSC).

${baseData}

Include these sections:
1. Executive Summary
2. Key Performance Indicators
3. NRW Trend Analysis
4. Leak Detection Summary
5. DMA Performance Rankings
6. Recommendations for Next Month
7. Financial Impact Summary

Format the report professionally with clear headers and bullet points.`
        
      case 'weekly':
        return `Generate a Weekly Summary Report for Lusaka Water Supply Company (LWSC).

${baseData}

Include these sections:
1. Week Overview
2. Leak Detections This Week
3. Work Orders Completed
4. Sensor Network Status
5. Priority Actions for Next Week

Keep it concise and actionable.`
        
      case 'dma':
        const selectedDMAData = dmas.find(d => d.dma_id === selectedDMA) || dmas[0]
        return `Generate a DMA Deep Dive Analysis Report for ${selectedDMAData?.name || 'the selected DMA'}.

${baseData}

Focus on:
1. DMA Overview & Statistics
2. NRW Performance vs Target
3. Sensor Readings Analysis
4. Leak History & Patterns
5. Infrastructure Condition Assessment
6. Improvement Recommendations
7. Projected Savings Potential`
        
      case 'financial':
        return `Generate a Revenue Recovery Report for Lusaka Water Supply Company (LWSC).

${baseData}

Calculate and include:
1. Executive Financial Summary
2. Water Loss Cost Analysis (assume $0.50/m³)
3. Revenue Recovery from Leak Repairs
4. Investment vs Returns Analysis
5. DMA-wise Financial Performance
6. Projected Annual Savings
7. ROI on Detection System`
        
      default:
        return `Generate a ${templateName} for LWSC.\n\n${baseData}`
    }
  }
  
  const generateFallbackReport = (templateId: string, templateName: string): string => {
    const now = new Date()
    
    const header = `
================================================================================
                    LUSAKA WATER SUPPLY COMPANY (LWSC)
                    ${templateName.toUpperCase()}
                    Generated: ${now.toLocaleString()}
================================================================================

`
    
    const nrwValue = metrics?.total_nrw_percent?.toFixed(1) || '32.5'
    const sensorCount = metrics?.sensor_count || 0
    const dmaCount = dmas.length || 0
    const leakCount = leaks.length
    
    switch (templateId) {
      case 'monthly':
        return header + `
EXECUTIVE SUMMARY
-----------------
This report provides a comprehensive analysis of Non-Revenue Water (NRW) 
performance for the current period.

KEY PERFORMANCE INDICATORS
--------------------------
• Current NRW Rate: ${nrwValue}%
• Target NRW Rate: 25%
• Active Sensors: ${sensorCount}
• DMAs Monitored: ${dmaCount}
• Active Leak Alerts: ${leakCount}

NRW TREND ANALYSIS
------------------
The network is currently operating at ${nrwValue}% NRW, which is 
${parseFloat(nrwValue) > 25 ? 'above' : 'at or below'} the target of 25%.

${leakCount > 0 ? `
ACTIVE LEAK ALERTS
------------------
${leaks.map(l => `• ${l.location}
  - Estimated Loss: ${l.estimated_loss} m³/day
  - Confidence: ${l.confidence}%
  - Status: ${l.status}
`).join('\n')}` : `
LEAK STATUS
-----------
No active leaks detected. System monitoring is active.
`}

DMA PERFORMANCE
---------------
${dmas.length > 0 ? dmas.map(d => `• ${d.name}: ${d.nrw_percent}% NRW (${d.status})`).join('\n') : 'No DMA data available'}

RECOMMENDATIONS
---------------
1. Continue monitoring high-priority DMAs
2. Maintain sensor network health
3. Investigate any pressure anomalies promptly
4. Review and update leak detection thresholds monthly

================================================================================
                         END OF REPORT
================================================================================
`
        
      case 'weekly':
        return header + `
WEEK OVERVIEW
-------------
• NRW Rate: ${nrwValue}%
• Active Sensors: ${sensorCount}
• Leak Alerts: ${leakCount}

${leakCount > 0 ? `
LEAK DETECTIONS
---------------
${leaks.map(l => `• ${l.location}: ${l.estimated_loss} m³/day (${l.status})`).join('\n')}
` : `
LEAK STATUS
-----------
No leaks detected this week. System operating normally.
`}

PRIORITY ACTIONS
----------------
1. Review sensor readings for anomalies
2. Complete scheduled maintenance
3. Follow up on any unresolved alerts

================================================================================
`
        
      case 'financial':
        const waterCost = 0.50
        const totalDailyLoss = leaks.reduce((sum, l) => sum + (l.estimated_loss || 0), 0)
        const dailyCost = totalDailyLoss * waterCost
        const monthlyCost = dailyCost * 30
        const annualCost = dailyCost * 365
        
        return header + `
FINANCIAL SUMMARY
-----------------
Water Cost Rate: $${waterCost.toFixed(2)} per m³

CURRENT LOSSES
--------------
• Daily Water Loss: ${totalDailyLoss.toFixed(0)} m³/day
• Daily Revenue Loss: $${dailyCost.toFixed(2)}
• Monthly Revenue Loss: $${monthlyCost.toFixed(2)}
• Annual Projected Loss: $${annualCost.toFixed(2)}

${leakCount > 0 ? `
LEAK-WISE ANALYSIS
------------------
${leaks.map(l => {
  const loss = l.estimated_loss * waterCost
  return `• ${l.location}
  - Daily Loss: $${loss.toFixed(2)} (${l.estimated_loss} m³/day)`
}).join('\n')}
` : `
CURRENT STATUS
--------------
No active leaks. Potential savings maintained.
`}

RECOVERY POTENTIAL
------------------
By addressing current leaks, LWSC can recover:
• Up to $${monthlyCost.toFixed(2)} monthly
• Up to $${annualCost.toFixed(2)} annually

================================================================================
`
        
      default:
        return header + `
REPORT CONTENT
--------------
• NRW Rate: ${nrwValue}%
• Active Sensors: ${sensorCount}
• DMAs: ${dmaCount}
• Leak Alerts: ${leakCount}

${dmas.length > 0 ? `
DMA STATUS
----------
${dmas.map(d => `• ${d.name}: ${d.nrw_percent}% NRW`).join('\n')}
` : ''}

================================================================================
`
    }
  }
  
  // View report in modal
  const viewReport = (report: Report) => {
    if (!report.content) return
    setViewingReport(report)
  }

  // Close report modal
  const closeReportModal = () => {
    setViewingReport(null)
    setCopied(false)
  }

  // Copy report to clipboard
  const copyToClipboard = async (report: Report) => {
    if (!report.content) return
    try {
      await navigator.clipboard.writeText(report.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  // Share via WhatsApp
  const shareViaWhatsApp = (report: Report) => {
    if (!report.content) return
    
    // Truncate content for WhatsApp (max ~65000 chars but shorter is better)
    const maxLength = 2000
    let shareText = `*${report.title}*\n\n`
    shareText += `Generated: ${formatDate(report.generated)}\n`
    shareText += `Report ID: ${report.id}\n\n`
    
    // Add truncated content
    const contentPreview = report.content.substring(0, maxLength)
    shareText += contentPreview
    if (report.content.length > maxLength) {
      shareText += '\n\n... [Report truncated - download full version]'
    }
    
    const encodedText = encodeURIComponent(shareText)
    window.open(`https://wa.me/?text=${encodedText}`, '_blank')
  }

  // Share via Email
  const shareViaEmail = (report: Report) => {
    if (!report.content) return
    
    const subject = encodeURIComponent(`LWSC NRW Report: ${report.title}`)
    const body = encodeURIComponent(
      `${report.title}\n\n` +
      `Generated: ${formatDate(report.generated)}\n` +
      `Report ID: ${report.id}\n\n` +
      `${'='.repeat(50)}\n\n` +
      report.content
    )
    
    window.location.href = `mailto:?subject=${subject}&body=${body}`
  }

  // Print report
  const printReport = (report: Report) => {
    if (!report.content) return
    
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>${report.title}</title>
            <style>
              @media print {
                body { margin: 0; padding: 20px; }
                .no-print { display: none !important; }
              }
              body { 
                font-family: 'Courier New', monospace; 
                padding: 40px; 
                background: white;
                color: #1e293b;
                line-height: 1.6;
              }
              .header { 
                border-bottom: 2px solid #3b82f6;
                padding-bottom: 20px;
                margin-bottom: 30px;
              }
              h1 { color: #1e3a5f; margin: 0 0 10px 0; font-size: 24px; }
              .meta { color: #64748b; font-size: 12px; }
              pre { 
                white-space: pre-wrap; 
                word-wrap: break-word; 
                margin: 0;
                font-size: 12px;
              }
              .logo { 
                font-weight: bold; 
                color: #3b82f6; 
                font-size: 14px;
                margin-bottom: 5px;
              }
            </style>
          </head>
          <body>
            <div class="header">
              <div class="logo">LWSC NRW Detection System</div>
              <h1>${report.title}</h1>
              <div class="meta">
                Report ID: ${report.id} | Generated: ${formatDate(report.generated)} | Type: ${report.type}
              </div>
            </div>
            <pre>${report.content}</pre>
            <script>window.onload = function() { window.print(); }</script>
          </body>
        </html>
      `)
      printWindow.document.close()
    }
  }

  // Open in new window (for viewing)
  const openInNewWindow = (report: Report) => {
    if (!report.content) return
    
    const newWindow = window.open('', '_blank')
    if (newWindow) {
      newWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>${report.title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
              * { box-sizing: border-box; }
              body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px; 
                background: #f1f5f9;
                margin: 0;
              }
              .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                overflow: hidden;
              }
              .header { 
                background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
                color: white;
                padding: 24px;
              }
              .logo { font-size: 12px; opacity: 0.8; margin-bottom: 8px; }
              h1 { margin: 0 0 12px 0; font-size: 22px; }
              .meta { opacity: 0.8; font-size: 13px; }
              .actions {
                padding: 16px 24px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
              }
              button {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
              }
              .btn-primary { background: #3b82f6; color: white; }
              .btn-primary:hover { background: #2563eb; }
              .btn-green { background: #22c55e; color: white; }
              .btn-green:hover { background: #16a34a; }
              .btn-secondary { background: #e2e8f0; color: #475569; }
              .btn-secondary:hover { background: #cbd5e1; }
              .content {
                padding: 24px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                line-height: 1.7;
                white-space: pre-wrap;
                word-wrap: break-word;
                background: #fafafa;
                border: 1px solid #e2e8f0;
                margin: 20px;
                border-radius: 8px;
                max-height: 60vh;
                overflow-y: auto;
              }
              @media (max-width: 600px) {
                body { padding: 10px; }
                .header { padding: 16px; }
                h1 { font-size: 18px; }
                .content { margin: 12px; padding: 16px; font-size: 11px; }
              }
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <div class="logo">LWSC NRW Detection System</div>
                <h1>${report.title}</h1>
                <div class="meta">
                  Report ID: ${report.id} | Generated: ${formatDate(report.generated)}
                </div>
              </div>
              <div class="actions">
                <button class="btn-primary" onclick="window.print()">
                  🖨️ Print / PDF
                </button>
                <button class="btn-green" onclick="shareWhatsApp()">
                  💬 WhatsApp
                </button>
                <button class="btn-secondary" onclick="shareEmail()">
                  ✉️ Email
                </button>
                <button class="btn-secondary" onclick="copyContent()">
                  📋 Copy
                </button>
              </div>
              <pre class="content">${report.content}</pre>
            </div>
            <script>
              const reportContent = ${JSON.stringify(report.content)};
              const reportTitle = ${JSON.stringify(report.title)};
              
              function shareWhatsApp() {
                const text = '*' + reportTitle + '*\\n\\n' + reportContent.substring(0, 2000);
                window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
              }
              
              function shareEmail() {
                const subject = 'LWSC NRW Report: ' + reportTitle;
                const body = reportTitle + '\\n\\n' + reportContent;
                window.location.href = 'mailto:?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
              }
              
              function copyContent() {
                navigator.clipboard.writeText(reportContent).then(() => {
                  alert('Report copied to clipboard!');
                });
              }
            </script>
          </body>
        </html>
      `)
      newWindow.document.close()
    }
  }
  
  // Download report as text file
  const downloadReport = (report: Report) => {
    if (!report.content) return
    
    const blob = new Blob([report.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.id}_${report.title.replace(/[^a-z0-9]/gi, '_')}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  // Delete report
  const deleteReport = (reportId: string) => {
    if (confirm('Are you sure you want to delete this report?')) {
      const newReports = reports.filter(r => r.id !== reportId)
      saveReports(newReports)
    }
  }
  
  const tabs = [
    { id: 'templates', label: 'Generate Reports', count: REPORT_TEMPLATES.length },
    { id: 'reports', label: 'Generated Reports', count: reports.length },
  ]
  
  const filteredReports = reports.filter(report => 
    !typeFilter || report.type === typeFilter
  )
  
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Generating...'
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-display font-bold text-text-primary">Reports</h1>
          <p className="text-xs sm:text-sm lg:text-body text-text-secondary mt-0.5 sm:mt-1">
            Generate and download real system reports using AI analysis
          </p>
        </div>
        <Button variant="secondary" onClick={fetchData}>
          <RefreshCw className="w-4 h-4" />
          <span className="hidden sm:inline">Refresh Data</span>
          <span className="sm:hidden">Refresh</span>
        </Button>
      </div>
      
      {/* Status Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">AI-Powered Report Generation</p>
            <p className="text-sm text-blue-700">
              Reports are generated using real-time data from your sensors and AI analysis.
              {metrics ? ` Current NRW: ${metrics.total_nrw_percent?.toFixed(1)}%` : ' Loading data...'}
            </p>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
      
      {activeTab === 'templates' && (
        <div className="space-y-6">
          {/* DMA Selector for DMA report */}
          {dmas.length > 0 && (
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-slate-700">Select DMA for Deep Dive:</label>
              <Select
                value={selectedDMA}
                options={[
                  { value: '', label: 'Select a DMA' },
                  ...dmas.map(d => ({ value: d.dma_id, label: d.name }))
                ]}
                onChange={setSelectedDMA}
              />
            </div>
          )}
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {REPORT_TEMPLATES.map((template) => (
              <div 
                key={template.id}
                className="card p-6 hover:shadow-lg hover:border-blue-300 transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                    <template.icon className="w-6 h-6 text-slate-600 group-hover:text-blue-600 transition-colors" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">{template.name}</h3>
                    <p className="text-sm text-slate-500 mt-1">{template.description}</p>
                    <Button 
                      variant="primary" 
                      size="sm" 
                      className="mt-3"
                      onClick={() => generateReport(template.id)}
                      disabled={generating === template.id || (template.id === 'dma' && !selectedDMA && dmas.length > 0)}
                    >
                      {generating === template.id ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <FileText className="w-4 h-4" />
                          Generate Report
                        </>
                      )}
                    </Button>
                    {template.id === 'dma' && !selectedDMA && dmas.length > 0 && (
                      <p className="text-xs text-amber-600 mt-2">Please select a DMA first</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {activeTab === 'reports' && (
        <>
          {/* Filters */}
          <div className="flex items-center gap-4">
            <Select
              value={typeFilter}
              options={[
                { value: '', label: 'All Types' },
                { value: 'monthly', label: 'Monthly' },
                { value: 'weekly', label: 'Weekly' },
                { value: 'dma', label: 'DMA Analysis' },
                { value: 'financial', label: 'Financial' },
              ]}
              onChange={setTypeFilter}
            />
          </div>
          
          {/* Reports List */}
          <SectionCard title="Generated Reports" subtitle={reports.length > 0 ? `${reports.length} report(s) available` : 'No reports generated yet'} noPadding>
            {filteredReports.length === 0 ? (
              <div className="p-8 text-center">
                <FileCheck className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-700 mb-2">No Reports Yet</h3>
                <p className="text-slate-500 mb-4">Generate your first report from the templates tab</p>
                <Button variant="primary" onClick={() => setActiveTab('templates')}>
                  <FileText className="w-4 h-4" />
                  Generate Report
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredReports.map((report) => (
                  <div key={report.id} className="p-3 sm:p-4 hover:bg-slate-50 transition-colors">
                    {/* Mobile-first layout */}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
                      {/* Report info */}
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-slate-900 text-sm sm:text-base truncate">{report.title}</h4>
                          <div className="flex flex-wrap items-center gap-1 sm:gap-3 mt-1">
                            <span className="text-xs text-slate-500 font-mono">{report.id}</span>
                            <span className="text-xs text-slate-400 hidden sm:inline">•</span>
                            <span className="text-xs text-slate-500 capitalize">{report.type}</span>
                            {report.size && (
                              <>
                                <span className="text-xs text-slate-400 hidden sm:inline">•</span>
                                <span className="text-xs text-slate-500">{report.size}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Status */}
                      <div className="flex items-center justify-between sm:justify-end gap-2 sm:gap-4">
                        <div className="text-left sm:text-right">
                          <div className="flex items-center gap-1 sm:gap-2">
                            {report.status === 'completed' ? (
                              <CheckCircle className="w-4 h-4 text-emerald-500" />
                            ) : report.status === 'failed' ? (
                              <AlertCircle className="w-4 h-4 text-red-500" />
                            ) : (
                              <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
                            )}
                            <span className={`text-xs sm:text-sm font-medium ${
                              report.status === 'completed' ? 'text-emerald-600' : 
                              report.status === 'failed' ? 'text-red-600' : 'text-amber-600'
                            }`}>
                              {report.status === 'completed' ? 'Completed' : 
                               report.status === 'failed' ? 'Failed' : 'Generating'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">{formatDate(report.generated)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Action buttons - separate row on mobile */}
                    <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-slate-100 sm:border-0 sm:pt-0 sm:mt-2 sm:ml-13">
                      <Button 
                        variant="primary" 
                        size="sm" 
                        disabled={report.status !== 'completed'}
                        onClick={() => viewReport(report)}
                        className="flex-1 sm:flex-none"
                      >
                        <Eye className="w-4 h-4" />
                        <span>View</span>
                      </Button>
                      <button
                        disabled={report.status !== 'completed'}
                        onClick={() => shareViaWhatsApp(report)}
                        className="flex items-center justify-center gap-1 px-3 py-1.5 bg-green-500 hover:bg-green-600 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg transition-colors text-xs font-medium flex-1 sm:flex-none"
                      >
                        <MessageCircle className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">WhatsApp</span>
                      </button>
                      <button
                        disabled={report.status !== 'completed'}
                        onClick={() => shareViaEmail(report)}
                        className="flex items-center justify-center gap-1 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg transition-colors text-xs font-medium flex-1 sm:flex-none"
                      >
                        <Mail className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Email</span>
                      </button>
                      <Button 
                        variant="secondary" 
                        size="sm" 
                        disabled={report.status !== 'completed'}
                        onClick={() => downloadReport(report)}
                        className="flex-1 sm:flex-none"
                      >
                        <Download className="w-4 h-4" />
                        <span className="hidden sm:inline">Download</span>
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => deleteReport(report.id)}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </>
      )}

      {/* Report Preview Modal */}
      {viewingReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-slate-800 to-blue-800 text-white p-4 sm:p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-blue-200 mb-1">LWSC NRW Detection System</p>
                  <h2 className="text-lg sm:text-xl font-bold truncate">{viewingReport.title}</h2>
                  <div className="flex flex-wrap items-center gap-2 sm:gap-4 mt-2 text-xs sm:text-sm text-blue-200">
                    <span className="font-mono">{viewingReport.id}</span>
                    <span>•</span>
                    <span>{formatDate(viewingReport.generated)}</span>
                    <span>•</span>
                    <span className="capitalize">{viewingReport.type}</span>
                  </div>
                </div>
                <button 
                  onClick={closeReportModal}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Share Actions */}
            <div className="bg-slate-50 border-b border-slate-200 p-3 sm:p-4">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => shareViaWhatsApp(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <MessageCircle className="w-4 h-4" />
                  <span className="hidden sm:inline">WhatsApp</span>
                </button>
                <button
                  onClick={() => shareViaEmail(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <Mail className="w-4 h-4" />
                  <span className="hidden sm:inline">Email</span>
                </button>
                <button
                  onClick={() => downloadReport(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Download</span>
                </button>
                <button
                  onClick={() => printReport(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <Printer className="w-4 h-4" />
                  <span className="hidden sm:inline">Print / PDF</span>
                </button>
                <button
                  onClick={() => copyToClipboard(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg transition-colors text-sm font-medium"
                >
                  {copied ? <CheckCircle className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                  <span className="hidden sm:inline">{copied ? 'Copied!' : 'Copy'}</span>
                </button>
                <button
                  onClick={() => openInNewWindow(viewingReport)}
                  className="flex items-center gap-2 px-3 sm:px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg transition-colors text-sm font-medium"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span className="hidden sm:inline">Open in Tab</span>
                </button>
              </div>
            </div>

            {/* Report Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-white">
              <pre className="whitespace-pre-wrap font-mono text-xs sm:text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">
                {viewingReport.content}
              </pre>
            </div>

            {/* Modal Footer */}
            <div className="border-t border-slate-200 p-3 sm:p-4 bg-slate-50 flex items-center justify-between gap-4">
              <p className="text-xs text-slate-500">
                {viewingReport.size} • Click any button above to share or download
              </p>
              <Button variant="secondary" onClick={closeReportModal}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
