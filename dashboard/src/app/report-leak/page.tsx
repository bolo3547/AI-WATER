'use client'

import { useState } from 'react'
import { 
  AlertTriangle, MapPin, Camera, Phone, Mail, User, 
  CheckCircle, Clock, Send, Upload, X, Info, 
  Droplets, MessageCircle, FileText, ChevronRight
} from 'lucide-react'

// Sample reported leaks from customers
const customerReports = [
  {
    id: 'RPT-001',
    location: 'Great East Road, Near Arcades',
    type: 'burst_pipe',
    severity: 'high',
    status: 'assigned',
    reportedAt: '2025-01-15 08:30',
    reportedBy: 'John M.',
    phone: '+260 97X XXX XXX',
    description: 'Large water fountain coming from ground',
    photos: 2,
    crew: 'Team Alpha'
  },
  {
    id: 'RPT-002',
    location: 'Kafue Road, Chilenje South',
    type: 'leaking_valve',
    severity: 'medium',
    status: 'pending',
    reportedAt: '2025-01-15 10:15',
    reportedBy: 'Mary C.',
    phone: '+260 96X XXX XXX',
    description: 'Water leaking from valve box at intersection',
    photos: 1,
    crew: null
  },
  {
    id: 'RPT-003',
    location: 'Los Angeles Blvd, Kabulonga',
    type: 'running_meter',
    severity: 'low',
    status: 'resolved',
    reportedAt: '2025-01-14 14:20',
    reportedBy: 'Peter N.',
    phone: '+260 95X XXX XXX',
    description: 'Water meter spinning when no taps are open',
    photos: 0,
    crew: 'Team Beta',
    resolvedAt: '2025-01-15 09:00'
  },
]

const leakTypes = [
  { id: 'burst_pipe', label: 'Burst Pipe', icon: '💧', description: 'Water shooting or gushing from ground/pipe' },
  { id: 'leaking_valve', label: 'Leaking Valve', icon: '🔧', description: 'Water leaking from valve box or hydrant' },
  { id: 'running_meter', label: 'Running Meter', icon: '📊', description: 'Meter spinning with no water usage' },
  { id: 'wet_ground', label: 'Wet Ground', icon: '🌊', description: 'Unusually wet area or pooling water' },
  { id: 'low_pressure', label: 'Low Pressure', icon: '📉', description: 'Very low water pressure in area' },
  { id: 'other', label: 'Other', icon: '❓', description: 'Other water-related issue' },
]

export default function ReportLeakPage() {
  const [activeTab, setActiveTab] = useState<'report' | 'track'>('report')
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    type: '',
    location: '',
    description: '',
    name: '',
    phone: '',
    email: '',
    photos: [] as string[],
    severity: 'medium',
  })
  const [trackingId, setTrackingId] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleSubmit = () => {
    setIsSubmitting(true)
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false)
      setIsSubmitted(true)
    }, 2000)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-amber-100 text-amber-700'
      case 'assigned': return 'bg-blue-100 text-blue-700'
      case 'in_progress': return 'bg-purple-100 text-purple-700'
      case 'resolved': return 'bg-emerald-100 text-emerald-700'
      default: return 'bg-slate-100 text-slate-700'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-700 border-red-300'
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-300'
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-300'
      default: return 'bg-slate-100 text-slate-700 border-slate-300'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      {/* Public Header */}
      <div className="bg-gradient-to-r from-green-700 via-emerald-600 to-orange-500 text-white">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <Droplets className="w-6 h-6" />
              </div>
              <div>
                <p className="text-[10px] sm:text-xs opacity-80">Republic of Zambia</p>
                <h1 className="text-sm sm:text-base font-bold">LWSC Leak Reporting</h1>
              </div>
            </div>
            <a href="tel:+260211251778" className="flex items-center gap-2 bg-white/20 hover:bg-white/30 px-3 py-2 rounded-lg transition-colors">
              <Phone className="w-4 h-4" />
              <span className="text-xs sm:text-sm font-medium hidden sm:inline">Emergency: 211-251778</span>
            </a>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Tab Switcher */}
        <div className="flex bg-white rounded-xl shadow-sm p-1 mb-6">
          <button
            onClick={() => { setActiveTab('report'); setIsSubmitted(false); setStep(1); }}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'report'
                ? 'bg-blue-600 text-white'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Report a Leak
          </button>
          <button
            onClick={() => setActiveTab('track')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'track'
                ? 'bg-blue-600 text-white'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <FileText className="w-4 h-4" />
            Track Report
          </button>
        </div>

        {activeTab === 'report' ? (
          isSubmitted ? (
            /* Success Message */
            <div className="bg-white rounded-2xl shadow-sm p-6 sm:p-8 text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-2">Report Submitted!</h2>
              <p className="text-sm text-slate-500 mb-6">
                Thank you for helping us maintain Lusaka&apos;s water network.
              </p>
              <div className="bg-blue-50 rounded-xl p-4 mb-6">
                <p className="text-xs text-blue-600 mb-1">Your Tracking ID</p>
                <p className="text-2xl font-bold text-blue-700">RPT-{Date.now().toString().slice(-6)}</p>
              </div>
              <div className="space-y-3 text-left bg-slate-50 rounded-xl p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-500" />
                  <span className="text-sm text-slate-700">Report received and logged</span>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-blue-500" />
                  <span className="text-sm text-slate-700">Technician assignment within 2 hours</span>
                </div>
                <div className="flex items-center gap-3">
                  <MessageCircle className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-slate-700">SMS updates sent to your phone</span>
                </div>
              </div>
              <button
                onClick={() => { setIsSubmitted(false); setStep(1); setFormData({ ...formData, type: '', description: '' }); }}
                className="mt-6 w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
              >
                Report Another Issue
              </button>
            </div>
          ) : (
            /* Report Form */
            <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
              {/* Progress Steps */}
              <div className="flex border-b border-slate-100">
                {[1, 2, 3].map((s) => (
                  <div
                    key={s}
                    className={`flex-1 py-3 text-center text-xs sm:text-sm font-medium transition-colors ${
                      step === s
                        ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
                        : step > s
                        ? 'text-emerald-600 bg-emerald-50'
                        : 'text-slate-400'
                    }`}
                  >
                    {s === 1 ? '1. Issue Type' : s === 2 ? '2. Location' : '3. Contact'}
                  </div>
                ))}
              </div>

              <div className="p-4 sm:p-6">
                {step === 1 && (
                  <div className="space-y-4">
                    <h2 className="text-base sm:text-lg font-semibold text-slate-900">What type of issue are you reporting?</h2>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {leakTypes.map((type) => (
                        <button
                          key={type.id}
                          onClick={() => setFormData({ ...formData, type: type.id })}
                          className={`p-3 sm:p-4 rounded-xl border-2 text-left transition-all ${
                            formData.type === type.id
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          <span className="text-2xl mb-2 block">{type.icon}</span>
                          <p className="text-xs sm:text-sm font-medium text-slate-900">{type.label}</p>
                          <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5 line-clamp-2">{type.description}</p>
                        </button>
                      ))}
                    </div>

                    {/* Severity */}
                    <div className="pt-4">
                      <label className="block text-sm font-medium text-slate-700 mb-2">How severe is the issue?</label>
                      <div className="flex gap-2">
                        {[
                          { id: 'high', label: 'High', desc: 'Major flooding/safety hazard' },
                          { id: 'medium', label: 'Medium', desc: 'Visible leak, needs attention' },
                          { id: 'low', label: 'Low', desc: 'Minor issue, not urgent' },
                        ].map((sev) => (
                          <button
                            key={sev.id}
                            onClick={() => setFormData({ ...formData, severity: sev.id })}
                            className={`flex-1 p-2 sm:p-3 rounded-lg border-2 text-center transition-all ${
                              formData.severity === sev.id
                                ? getSeverityColor(sev.id) + ' border-2'
                                : 'border-slate-200'
                            }`}
                          >
                            <p className="text-xs sm:text-sm font-medium">{sev.label}</p>
                            <p className="text-[9px] sm:text-[10px] text-slate-500 mt-0.5">{sev.desc}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={() => setStep(2)}
                      disabled={!formData.type}
                      className={`w-full py-3 rounded-xl font-medium transition-colors ${
                        formData.type
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      }`}
                    >
                      Continue
                    </button>
                  </div>
                )}

                {step === 2 && (
                  <div className="space-y-4">
                    <h2 className="text-base sm:text-lg font-semibold text-slate-900">Where is the issue located?</h2>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Location / Address</label>
                      <div className="relative">
                        <MapPin className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                        <textarea
                          value={formData.location}
                          onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                          placeholder="Enter street name, nearby landmarks, or address..."
                          rows={3}
                          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        placeholder="Describe what you see (water flowing, wet ground, etc.)..."
                        rows={3}
                        className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>

                    {/* Photo Upload */}
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Add Photos (Optional)</label>
                      <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-slate-300 transition-colors cursor-pointer">
                        <Camera className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                        <p className="text-sm text-slate-600">Tap to take or upload photos</p>
                        <p className="text-xs text-slate-400">Photos help us respond faster</p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setStep(1)}
                        className="flex-1 py-3 border border-slate-200 rounded-xl font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                      >
                        Back
                      </button>
                      <button
                        onClick={() => setStep(3)}
                        disabled={!formData.location}
                        className={`flex-1 py-3 rounded-xl font-medium transition-colors ${
                          formData.location
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        }`}
                      >
                        Continue
                      </button>
                    </div>
                  </div>
                )}

                {step === 3 && (
                  <div className="space-y-4">
                    <h2 className="text-base sm:text-lg font-semibold text-slate-900">Your Contact Information</h2>
                    <p className="text-xs text-slate-500">We&apos;ll send you updates about your report</p>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                          placeholder="Your name"
                          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number *</label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="tel"
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                          placeholder="+260 97X XXX XXX"
                          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Email (Optional)</label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                        <input
                          type="email"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          placeholder="your.email@example.com"
                          className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>

                    {/* Summary */}
                    <div className="bg-slate-50 rounded-xl p-4">
                      <p className="text-xs font-medium text-slate-500 mb-2">Report Summary</p>
                      <div className="space-y-1 text-sm">
                        <p><span className="text-slate-500">Type:</span> <span className="font-medium">{leakTypes.find(t => t.id === formData.type)?.label}</span></p>
                        <p><span className="text-slate-500">Severity:</span> <span className={`font-medium capitalize ${formData.severity === 'high' ? 'text-red-600' : formData.severity === 'medium' ? 'text-amber-600' : 'text-blue-600'}`}>{formData.severity}</span></p>
                        <p><span className="text-slate-500">Location:</span> <span className="font-medium">{formData.location}</span></p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setStep(2)}
                        className="flex-1 py-3 border border-slate-200 rounded-xl font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                      >
                        Back
                      </button>
                      <button
                        onClick={handleSubmit}
                        disabled={!formData.phone || isSubmitting}
                        className={`flex-1 py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2 ${
                          formData.phone && !isSubmitting
                            ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        }`}
                      >
                        {isSubmitting ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Submitting...
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4" />
                            Submit Report
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        ) : (
          /* Track Report Tab */
          <div className="space-y-4">
            {/* Search */}
            <div className="bg-white rounded-2xl shadow-sm p-4 sm:p-6">
              <h2 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">Track Your Report</h2>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={trackingId}
                  onChange={(e) => setTrackingId(e.target.value.toUpperCase())}
                  placeholder="Enter tracking ID (e.g., RPT-001234)"
                  className="flex-1 px-4 py-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors">
                  Track
                </button>
              </div>
            </div>

            {/* Recent Reports */}
            <div className="bg-white rounded-2xl shadow-sm p-4 sm:p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-4">Recent Community Reports</h3>
              <div className="space-y-3">
                {customerReports.map((report) => (
                  <div
                    key={report.id}
                    className="p-3 sm:p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-xs font-mono text-blue-600">{report.id}</p>
                        <p className="text-sm font-medium text-slate-900">{report.location}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-[10px] sm:text-xs font-medium capitalize ${getStatusColor(report.status)}`}>
                        {report.status.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mb-2 line-clamp-1">{report.description}</p>
                    <div className="flex items-center justify-between text-[10px] sm:text-xs text-slate-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {report.reportedAt}
                      </span>
                      {report.crew && (
                        <span className="text-blue-600">Assigned: {report.crew}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Info */}
            <div className="bg-blue-50 rounded-2xl p-4 flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-xs sm:text-sm text-blue-700">
                <p className="font-medium mb-1">Response Times</p>
                <ul className="space-y-0.5 text-blue-600">
                  <li>• High severity: Within 2 hours</li>
                  <li>• Medium severity: Within 24 hours</li>
                  <li>• Low severity: Within 72 hours</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
