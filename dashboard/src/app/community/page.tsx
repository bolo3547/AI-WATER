'use client'

import { useState, useEffect } from 'react'
import { 
  MapPin, Camera, Send, CheckCircle, AlertTriangle, 
  Phone, MessageSquare, Clock, Users, TrendingUp,
  Droplets, ThumbsUp, Eye, Share2, Loader2, X,
  Navigation, Image as ImageIcon, Mic, Globe
} from 'lucide-react'

interface LeakReport {
  id: string
  location: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'verified' | 'assigned' | 'resolved'
  reportedBy: string
  phone: string
  timestamp: string
  coordinates?: { lat: number; lng: number }
  imageUrl?: string
  upvotes: number
  dma?: string
}

export default function CommunityReportingPage() {
  const [reports, setReports] = useState<LeakReport[]>([])
  const [showReportForm, setShowReportForm] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [gettingLocation, setGettingLocation] = useState(false)
  const [language, setLanguage] = useState('en')
  
  const [formData, setFormData] = useState({
    location: '',
    description: '',
    severity: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    reporterName: '',
    phone: '',
    coordinates: null as { lat: number; lng: number } | null
  })

  // Translations
  const translations: Record<string, Record<string, string>> = {
    en: {
      title: 'Community Leak Reporting',
      subtitle: 'Help us find and fix water leaks in your area',
      reportLeak: 'Report a Leak',
      recentReports: 'Recent Reports in Your Area',
      yourLocation: 'Your Location / Address',
      describeIssue: 'Describe the Issue',
      yourName: 'Your Name',
      phoneNumber: 'Phone Number',
      severity: 'Severity',
      low: 'Low - Small drip',
      medium: 'Medium - Steady leak',
      high: 'High - Large leak',
      critical: 'Critical - Flooding/Burst',
      submit: 'Submit Report',
      thankYou: 'Thank You!',
      reportReceived: 'Your report has been received. Reference:',
      useLocation: 'Use My Location',
      ussd: 'Report via USSD: *123*LEAK#',
      sms: 'SMS "LEAK" to 5555',
      stats: 'Community Impact',
      resolved: 'Leaks Resolved',
      pending: 'Pending Review',
      waterSaved: 'Water Saved'
    },
    bem: {
      title: 'Ukupeleka Amashiwi Ya Menshi',
      subtitle: 'Twafweni ukusanga no kulungika amashiwi ya menshi mu ncende yenu',
      reportLeak: 'Peleniko Ishiwi',
      recentReports: 'Amashiwi Yapita mu Ncende Yenu',
      yourLocation: 'Incende Yenu',
      describeIssue: 'Londololeni Ubwafya',
      yourName: 'Ishina Lyenu',
      phoneNumber: 'Inambala ya Foni',
      severity: 'Ubukulu',
      low: 'Panono - Tutontokanishya',
      medium: 'Pakati - Ishiwi Ilikalamba',
      high: 'Ilikulu - Ishiwi Ilikulu',
      critical: 'Icilimo - Amenshi Yalefuma Sana',
      submit: 'Tumeni',
      thankYou: 'Twatotela!',
      reportReceived: 'Amashiwi yenu yapokelwa. Inambala:',
      useLocation: 'Sebensesheni Incende Yandi',
      ussd: 'Peleniko pa USSD: *123*LEAK#',
      sms: 'Tumeni "LEAK" ku 5555',
      stats: 'Imilimo ya Bantu',
      resolved: 'Amashiwi Yalungikwa',
      pending: 'Yalelolela',
      waterSaved: 'Amenshi Yasungwa'
    },
    nya: {
      title: 'Kuuza za Madzi Omwe Akutayika',
      subtitle: 'Tithandizeni kupeza ndi kukonza madzi omwe akutayika',
      reportLeak: 'Uzani za Leak',
      recentReports: 'Mauthenga Apitawa',
      yourLocation: 'Malo Anu',
      describeIssue: 'Fotokozani Vuto',
      yourName: 'Dzina Lanu',
      phoneNumber: 'Nambala ya Foni',
      severity: 'Kukula',
      low: 'Pang\'ono',
      medium: 'Pakati',
      high: 'Kwambiri',
      critical: 'Choopsa',
      submit: 'Tumizani',
      thankYou: 'Zikomo!',
      reportReceived: 'Uthenga wanu walandiridwa. Nambala:',
      useLocation: 'Gwiritsani Malo Anga',
      ussd: 'Uzani pa USSD: *123*LEAK#',
      sms: 'Tumizani "LEAK" ku 5555',
      stats: 'Thandizo la Anthu',
      resolved: 'Zomwe Zakonzedwa',
      pending: 'Zikuyembekezera',
      waterSaved: 'Madzi Osungidwa'
    }
  }

  const t = translations[language] || translations.en

  // Load sample community reports
  useEffect(() => {
    setReports([
      {
        id: 'CR-001',
        location: 'Kabulonga Shopping Area, Near Total Filling Station',
        description: 'Large water fountain coming from ground near the road',
        severity: 'critical',
        status: 'assigned',
        reportedBy: 'John M.',
        phone: '097XXXXXXX',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        coordinates: { lat: -15.4192, lng: 28.3225 },
        upvotes: 24,
        dma: 'Kabulonga'
      },
      {
        id: 'CR-002',
        location: 'Chilenje South, Plot 234',
        description: 'Water leaking from meter box for 3 days',
        severity: 'medium',
        status: 'verified',
        reportedBy: 'Mary C.',
        phone: '096XXXXXXX',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        upvotes: 12,
        dma: 'Chilenje'
      },
      {
        id: 'CR-003',
        location: 'Matero Main Road, Near Market',
        description: 'Broken pipe spraying water on the road',
        severity: 'high',
        status: 'resolved',
        reportedBy: 'Peter K.',
        phone: '095XXXXXXX',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        upvotes: 45,
        dma: 'Matero'
      },
      {
        id: 'CR-004',
        location: 'Roma Township, Block 5',
        description: 'Small drip from exposed pipe',
        severity: 'low',
        status: 'pending',
        reportedBy: 'Grace N.',
        phone: '097XXXXXXX',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        upvotes: 3,
        dma: 'Roma'
      }
    ])
  }, [])

  const getCurrentLocation = () => {
    setGettingLocation(true)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData({
            ...formData,
            coordinates: {
              lat: position.coords.latitude,
              lng: position.coords.longitude
            },
            location: `GPS: ${position.coords.latitude.toFixed(6)}, ${position.coords.longitude.toFixed(6)}`
          })
          setGettingLocation(false)
        },
        (error) => {
          console.error('Location error:', error)
          setGettingLocation(false)
          alert('Could not get location. Please enter address manually.')
        }
      )
    }
  }

  const handleSubmit = async () => {
    if (!formData.location || !formData.description || !formData.phone) {
      alert('Please fill in all required fields')
      return
    }

    setIsSubmitting(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const newReport: LeakReport = {
      id: `CR-${String(reports.length + 1).padStart(3, '0')}`,
      location: formData.location,
      description: formData.description,
      severity: formData.severity,
      status: 'pending',
      reportedBy: formData.reporterName || 'Anonymous',
      phone: formData.phone,
      timestamp: new Date().toISOString(),
      coordinates: formData.coordinates || undefined,
      upvotes: 0
    }

    setReports([newReport, ...reports])
    setIsSubmitting(false)
    setSubmitted(true)
    
    // Reset after showing success
    setTimeout(() => {
      setSubmitted(false)
      setShowReportForm(false)
      setFormData({
        location: '',
        description: '',
        severity: 'medium',
        reporterName: '',
        phone: '',
        coordinates: null
      })
    }, 5000)
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending': return { color: 'bg-gray-100 text-gray-700', label: 'Pending Review' }
      case 'verified': return { color: 'bg-blue-100 text-blue-700', label: 'Verified' }
      case 'assigned': return { color: 'bg-purple-100 text-purple-700', label: 'Crew Assigned' }
      case 'resolved': return { color: 'bg-green-100 text-green-700', label: 'Resolved ✓' }
      default: return { color: 'bg-gray-100 text-gray-700', label: status }
    }
  }

  const stats = {
    resolved: reports.filter(r => r.status === 'resolved').length * 127 + 1847,
    pending: reports.filter(r => r.status === 'pending').length + 12,
    waterSaved: '2.4M'
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                <Droplets className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold">LWSC</h1>
                <p className="text-blue-200 text-xs sm:text-sm">{t.title}</p>
              </div>
            </div>
            
            {/* Language Selector */}
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-200" />
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-white/20 border border-white/30 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
              >
                <option value="en">English</option>
                <option value="bem">Bemba</option>
                <option value="nya">Nyanja</option>
              </select>
            </div>
          </div>
          
          <p className="mt-4 text-blue-100 text-sm sm:text-base">
            {t.subtitle}
          </p>

          {/* Quick Report Options */}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <div className="bg-white/10 px-3 py-1.5 rounded-full flex items-center gap-1">
              <Phone className="w-3 h-3" />
              {t.ussd}
            </div>
            <div className="bg-white/10 px-3 py-1.5 rounded-full flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              {t.sms}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 text-center">
            <CheckCircle className="w-6 h-6 text-green-500 mx-auto mb-1" />
            <p className="text-xl sm:text-2xl font-bold text-slate-900">{stats.resolved}</p>
            <p className="text-xs text-slate-500">{t.resolved}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 text-center">
            <Clock className="w-6 h-6 text-amber-500 mx-auto mb-1" />
            <p className="text-xl sm:text-2xl font-bold text-slate-900">{stats.pending}</p>
            <p className="text-xs text-slate-500">{t.pending}</p>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 text-center">
            <Droplets className="w-6 h-6 text-blue-500 mx-auto mb-1" />
            <p className="text-xl sm:text-2xl font-bold text-slate-900">{stats.waterSaved}</p>
            <p className="text-xs text-slate-500">{t.waterSaved} m³</p>
          </div>
        </div>

        {/* Report Button */}
        {!showReportForm && !submitted && (
          <button
            onClick={() => setShowReportForm(true)}
            className="w-full bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-2xl p-6 shadow-lg shadow-red-500/25 transition-all flex items-center justify-center gap-3"
          >
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="text-left">
              <p className="text-lg font-bold">{t.reportLeak}</p>
              <p className="text-red-200 text-sm">Tap to report a water leak</p>
            </div>
          </button>
        )}

        {/* Report Form */}
        {showReportForm && !submitted && (
          <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="bg-red-500 text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                <span className="font-semibold">{t.reportLeak}</span>
              </div>
              <button onClick={() => setShowReportForm(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              {/* Location */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t.yourLocation} *</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Kabulonga, Near Shoprite"
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <button
                    onClick={getCurrentLocation}
                    disabled={gettingLocation}
                    className="px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors"
                  >
                    {gettingLocation ? <Loader2 className="w-5 h-5 animate-spin" /> : <Navigation className="w-5 h-5" />}
                  </button>
                </div>
                {formData.coordinates && (
                  <p className="text-xs text-green-600 mt-1">📍 Location captured</p>
                )}
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">{t.describeIssue} *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what you see..."
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>

              {/* Severity */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">{t.severity}</label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { value: 'low', label: t.low, color: 'border-green-500 bg-green-50' },
                    { value: 'medium', label: t.medium, color: 'border-yellow-500 bg-yellow-50' },
                    { value: 'high', label: t.high, color: 'border-orange-500 bg-orange-50' },
                    { value: 'critical', label: t.critical, color: 'border-red-500 bg-red-50' }
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setFormData({ ...formData, severity: opt.value as any })}
                      className={`p-2 rounded-lg border-2 text-xs text-left transition-all ${
                        formData.severity === opt.value ? opt.color : 'border-slate-200 bg-white'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t.yourName}</label>
                  <input
                    type="text"
                    value={formData.reporterName}
                    onChange={(e) => setFormData({ ...formData, reporterName: e.target.value })}
                    placeholder="Optional"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">{t.phoneNumber} *</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="097XXXXXXX"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              </div>

              {/* Photo Upload Placeholder */}
              <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 text-center">
                <Camera className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-sm text-slate-500">Tap to add photo (optional)</p>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    {t.submit}
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Success Message */}
        {submitted && (
          <div className="bg-green-50 border border-green-200 rounded-2xl p-6 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-green-800">{t.thankYou}</h3>
            <p className="text-green-700 mt-2">
              {t.reportReceived}
            </p>
            <p className="text-2xl font-mono font-bold text-green-800 mt-2">
              {reports[0]?.id}
            </p>
            <p className="text-sm text-green-600 mt-4">
              We will SMS you with updates on your report
            </p>
          </div>
        )}

        {/* Recent Reports */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-4 border-b border-slate-100">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-500" />
              {t.recentReports}
            </h2>
          </div>
          <div className="divide-y divide-slate-100">
            {reports.map((report) => {
              const statusBadge = getStatusBadge(report.status)
              return (
                <div key={report.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={`w-3 h-3 rounded-full mt-1.5 ${getSeverityColor(report.severity)}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs text-slate-400">{report.id}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusBadge.color}`}>
                          {statusBadge.label}
                        </span>
                        {report.dma && (
                          <span className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full text-xs">
                            {report.dma}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-slate-900 mt-1">{report.location}</p>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{report.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                        <span>{report.reportedBy}</span>
                        <span>•</span>
                        <span>{new Date(report.timestamp).toLocaleString()}</span>
                        <span className="flex items-center gap-1">
                          <ThumbsUp className="w-3 h-3" />
                          {report.upvotes}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Emergency Contact */}
        <div className="bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl p-4 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <Phone className="w-6 h-6" />
            </div>
            <div>
              <p className="font-bold">Emergency Hotline</p>
              <p className="text-2xl font-bold">+260 211 252 931</p>
              <p className="text-red-100 text-sm">For major pipe bursts & flooding</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 text-white py-6 mt-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-slate-400 text-sm">
            © 2026 Lusaka Water Supply & Sewerage Company
          </p>
          <p className="text-slate-500 text-xs mt-1">
            Powered by AI NRW Detection System
          </p>
        </div>
      </footer>
    </div>
  )
}
