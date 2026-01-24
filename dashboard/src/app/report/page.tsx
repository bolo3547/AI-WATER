'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  Droplets, MapPin, Camera, Phone, User, CheckCircle, 
  Send, Upload, X, AlertTriangle, Loader2, ChevronRight,
  Navigation, Image, Video, Info, Mail, Shield
} from 'lucide-react'
import Link from 'next/link'

// Report categories with icons and descriptions
const REPORT_CATEGORIES = [
  { 
    id: 'leak', 
    label: 'Leak / Drip', 
    icon: '💧', 
    description: 'Water leaking from pipe or connection',
    color: 'bg-blue-500'
  },
  { 
    id: 'burst', 
    label: 'Burst Pipe', 
    icon: '💦', 
    description: 'Water gushing or shooting from ground/pipe',
    color: 'bg-red-500'
  },
  { 
    id: 'no_water', 
    label: 'No Water', 
    icon: '🚫', 
    description: 'Complete lack of water supply',
    color: 'bg-slate-500'
  },
  { 
    id: 'low_pressure', 
    label: 'Low Pressure', 
    icon: '📉', 
    description: 'Very weak water flow',
    color: 'bg-amber-500'
  },
  { 
    id: 'illegal_connection', 
    label: 'Illegal Connection', 
    icon: '⚠️', 
    description: 'Suspected unauthorized water tap',
    color: 'bg-orange-500'
  },
  { 
    id: 'overflow', 
    label: 'Overflow / Flooding', 
    icon: '🌊', 
    description: 'Tank overflow or water flooding',
    color: 'bg-cyan-500'
  },
  { 
    id: 'contamination', 
    label: 'Water Quality Issue', 
    icon: '☣️', 
    description: 'Discolored, smelly, or unsafe water',
    color: 'bg-purple-500'
  },
  { 
    id: 'other', 
    label: 'Other Issue', 
    icon: '❓', 
    description: 'Other water-related problem',
    color: 'bg-slate-400'
  },
]

// Form steps
type FormStep = 'category' | 'location' | 'details' | 'contact' | 'review' | 'success'

interface FormData {
  category: string
  categoryLabel: string
  description: string
  latitude: number | null
  longitude: number | null
  areaText: string
  photos: File[]
  photoPreview: string[]
  reporterName: string
  reporterPhone: string
  reporterEmail: string
  reporterConsent: boolean
}

interface SubmitResponse {
  success: boolean
  ticket?: string
  message: string
  trackingUrl?: string
}

export default function PublicReportPage() {
  const [step, setStep] = useState<FormStep>('category')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitResponse, setSubmitResponse] = useState<SubmitResponse | null>(null)
  const [locationLoading, setLocationLoading] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  
  const [formData, setFormData] = useState<FormData>({
    category: '',
    categoryLabel: '',
    description: '',
    latitude: null,
    longitude: null,
    areaText: '',
    photos: [],
    photoPreview: [],
    reporterName: '',
    reporterPhone: '',
    reporterEmail: '',
    reporterConsent: false,
  })

  // Get current GPS location
  const getCurrentLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser')
      return
    }

    setLocationLoading(true)
    setLocationError(null)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setFormData(prev => ({
          ...prev,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        }))
        setLocationLoading(false)
      },
      (error) => {
        setLocationLoading(false)
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location access denied. Please enter your location manually.')
            break
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location unavailable. Please enter your location manually.')
            break
          case error.TIMEOUT:
            setLocationError('Location request timed out. Please try again.')
            break
          default:
            setLocationError('Unable to get location. Please enter manually.')
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    )
  }, [])

  // Handle photo selection
  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const validFiles = files.filter(f => 
      f.type.startsWith('image/') || f.type.startsWith('video/')
    ).slice(0, 3) // Max 3 files

    // Create preview URLs
    const previews = validFiles.map(f => URL.createObjectURL(f))

    setFormData(prev => ({
      ...prev,
      photos: [...prev.photos, ...validFiles].slice(0, 3),
      photoPreview: [...prev.photoPreview, ...previews].slice(0, 3),
    }))
  }

  // Remove photo
  const removePhoto = (index: number) => {
    URL.revokeObjectURL(formData.photoPreview[index])
    setFormData(prev => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index),
      photoPreview: prev.photoPreview.filter((_, i) => i !== index),
    }))
  }

  // Handle form submission
  const handleSubmit = async () => {
    setIsSubmitting(true)

    try {
      // In real implementation, this would call the API
      const tenantId = 'lwsc-zambia' // Would come from context/URL
      
      const response = await fetch(`/api/public-reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          category: formData.category,
          description: formData.description,
          latitude: formData.latitude,
          longitude: formData.longitude,
          area_text: formData.areaText,
          reporter_name: formData.reporterName || null,
          reporter_phone: formData.reporterPhone || null,
          reporter_email: formData.reporterEmail || null,
          reporter_consent: formData.reporterConsent,
        }),
      })

      const result = await response.json()
      
      setSubmitResponse(result)
      setStep('success')
    } catch (error) {
      console.error('Submit error:', error)
      setSubmitResponse({
        success: false,
        message: 'Failed to submit report. Please try again.',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Step validation
  const canProceed = () => {
    switch (step) {
      case 'category':
        return formData.category !== ''
      case 'location':
        return (formData.latitude && formData.longitude) || formData.areaText.trim().length > 5
      case 'details':
        return true // Description is optional
      case 'contact':
        return true // Contact is optional
      case 'review':
        return true
      default:
        return false
    }
  }

  // Navigation
  const nextStep = () => {
    const steps: FormStep[] = ['category', 'location', 'details', 'contact', 'review']
    const currentIndex = steps.indexOf(step)
    if (currentIndex < steps.length - 1) {
      setStep(steps[currentIndex + 1])
    }
  }

  const prevStep = () => {
    const steps: FormStep[] = ['category', 'location', 'details', 'contact', 'review']
    const currentIndex = steps.indexOf(step)
    if (currentIndex > 0) {
      setStep(steps[currentIndex - 1])
    }
  }

  // Progress indicator
  const getProgress = () => {
    const steps: FormStep[] = ['category', 'location', 'details', 'contact', 'review']
    return ((steps.indexOf(step) + 1) / steps.length) * 100
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-sm border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Droplets className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100">AquaWatch</h1>
              <p className="text-xs text-slate-400">Report Water Issues</p>
            </div>
          </div>
          <Link 
            href="/track" 
            className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            Track Report <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Progress bar */}
      {step !== 'success' && (
        <div className="bg-slate-800/50 h-1">
          <div 
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${getProgress()}%` }}
          />
        </div>
      )}

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-4 py-6">
        
        {/* Step: Category Selection */}
        {step === 'category' && (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">What would you like to report?</h2>
              <p className="text-slate-400">Select the type of water issue</p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {REPORT_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setFormData(prev => ({ 
                    ...prev, 
                    category: cat.id,
                    categoryLabel: cat.label 
                  }))}
                  className={`p-4 rounded-xl border-2 transition-all text-left ${
                    formData.category === cat.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                  }`}
                >
                  <div className="text-3xl mb-2">{cat.icon}</div>
                  <h3 className="font-semibold text-slate-100">{cat.label}</h3>
                  <p className="text-xs text-slate-400 mt-1">{cat.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step: Location */}
        {step === 'location' && (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">Where is the issue?</h2>
              <p className="text-slate-400">Share location for faster response</p>
            </div>

            {/* GPS Button */}
            <button
              onClick={getCurrentLocation}
              disabled={locationLoading}
              className={`w-full p-4 rounded-xl border-2 flex items-center justify-center gap-3 transition-all ${
                formData.latitude
                  ? 'border-emerald-500 bg-emerald-500/10'
                  : 'border-slate-700 bg-slate-800/50 hover:border-blue-500'
              }`}
            >
              {locationLoading ? (
                <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
              ) : formData.latitude ? (
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              ) : (
                <Navigation className="w-6 h-6 text-blue-400" />
              )}
              <div className="text-left">
                <p className="font-semibold text-slate-100">
                  {formData.latitude ? 'Location captured!' : 'Use my current location'}
                </p>
                <p className="text-xs text-slate-400">
                  {formData.latitude 
                    ? `${formData.latitude.toFixed(6)}, ${formData.longitude?.toFixed(6)}`
                    : 'Tap to share your GPS location'
                  }
                </p>
              </div>
            </button>

            {locationError && (
              <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <p className="text-sm text-amber-200">{locationError}</p>
              </div>
            )}

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-700" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-slate-900 px-3 text-sm text-slate-400">or describe location</span>
              </div>
            </div>

            {/* Manual location input */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Area / Address / Landmark
              </label>
              <textarea
                value={formData.areaText}
                onChange={(e) => setFormData(prev => ({ ...prev, areaText: e.target.value }))}
                placeholder="e.g., Great East Road, near Arcades Shopping Mall, opposite Total Filling Station"
                rows={3}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-slate-400">
                Be as specific as possible - include road names, landmarks, building names
              </p>
            </div>
          </div>
        )}

        {/* Step: Details & Photos */}
        {step === 'details' && (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">Tell us more</h2>
              <p className="text-slate-400">Add description and photos (optional)</p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description (optional)
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe what you see... How severe is it? How long has it been happening?"
                rows={4}
                maxLength={500}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
              />
              <p className="mt-1 text-xs text-slate-400 text-right">
                {formData.description.length}/500 characters
              </p>
            </div>

            {/* Photo upload */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <Camera className="w-4 h-4 inline mr-1" />
                Photos / Videos (optional)
              </label>
              
              {/* Photo previews */}
              {formData.photoPreview.length > 0 && (
                <div className="flex gap-2 mb-3 flex-wrap">
                  {formData.photoPreview.map((preview, index) => (
                    <div key={index} className="relative">
                      <img 
                        src={preview} 
                        alt={`Preview ${index + 1}`}
                        className="w-20 h-20 object-cover rounded-lg border border-slate-700"
                      />
                      <button
                        onClick={() => removePhoto(index)}
                        className="absolute -top-2 -right-2 p-1 bg-red-500 rounded-full text-white"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload button */}
              {formData.photos.length < 3 && (
                <label className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer hover:border-blue-500 transition-colors">
                  <Upload className="w-5 h-5 text-slate-400" />
                  <span className="text-slate-400">
                    Tap to add photo/video ({3 - formData.photos.length} remaining)
                  </span>
                  <input
                    type="file"
                    accept="image/*,video/*"
                    multiple
                    onChange={handlePhotoSelect}
                    className="hidden"
                  />
                </label>
              )}
              <p className="mt-1 text-xs text-slate-400">
                Max 3 files, 10MB each. Photos help us respond faster.
              </p>
            </div>
          </div>
        )}

        {/* Step: Contact Information */}
        {step === 'contact' && (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">Your contact (optional)</h2>
              <p className="text-slate-400">Help us follow up if needed</p>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl flex items-start gap-3">
              <Shield className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-blue-200 font-medium">Your privacy is protected</p>
                <p className="text-blue-200/70 mt-1">
                  Contact information is never shared publicly. It's only used to send you updates about your report.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <User className="w-4 h-4 inline mr-1" />
                  Name
                </label>
                <input
                  type="text"
                  value={formData.reporterName}
                  onChange={(e) => setFormData(prev => ({ ...prev, reporterName: e.target.value }))}
                  placeholder="Your name"
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Phone className="w-4 h-4 inline mr-1" />
                  Phone number
                </label>
                <input
                  type="tel"
                  value={formData.reporterPhone}
                  onChange={(e) => setFormData(prev => ({ ...prev, reporterPhone: e.target.value }))}
                  placeholder="+260 9X XXX XXXX"
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  <Mail className="w-4 h-4 inline mr-1" />
                  Email (optional)
                </label>
                <input
                  type="email"
                  value={formData.reporterEmail}
                  onChange={(e) => setFormData(prev => ({ ...prev, reporterEmail: e.target.value }))}
                  placeholder="your@email.com"
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              {(formData.reporterName || formData.reporterPhone || formData.reporterEmail) && (
                <label className="flex items-start gap-3 p-3 bg-slate-800 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.reporterConsent}
                    onChange={(e) => setFormData(prev => ({ ...prev, reporterConsent: e.target.checked }))}
                    className="mt-1 w-5 h-5 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">
                    I consent to being contacted about this report and receiving status updates
                  </span>
                </label>
              )}
            </div>
          </div>
        )}

        {/* Step: Review */}
        {step === 'review' && (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">Review your report</h2>
              <p className="text-slate-400">Make sure everything looks correct</p>
            </div>

            <div className="space-y-4">
              {/* Category */}
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <p className="text-xs text-slate-400 uppercase tracking-wider">Issue Type</p>
                <p className="text-lg font-semibold text-slate-100 mt-1">
                  {REPORT_CATEGORIES.find(c => c.id === formData.category)?.icon}{' '}
                  {formData.categoryLabel}
                </p>
              </div>

              {/* Location */}
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                <p className="text-xs text-slate-400 uppercase tracking-wider">Location</p>
                {formData.latitude ? (
                  <p className="text-slate-100 mt-1">
                    📍 GPS: {formData.latitude.toFixed(6)}, {formData.longitude?.toFixed(6)}
                  </p>
                ) : null}
                {formData.areaText && (
                  <p className="text-slate-100 mt-1">{formData.areaText}</p>
                )}
              </div>

              {/* Description */}
              {formData.description && (
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                  <p className="text-xs text-slate-400 uppercase tracking-wider">Description</p>
                  <p className="text-slate-100 mt-1">{formData.description}</p>
                </div>
              )}

              {/* Photos */}
              {formData.photoPreview.length > 0 && (
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                  <p className="text-xs text-slate-400 uppercase tracking-wider">Photos</p>
                  <div className="flex gap-2 mt-2">
                    {formData.photoPreview.map((preview, index) => (
                      <img 
                        key={index}
                        src={preview} 
                        alt={`Photo ${index + 1}`}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Contact */}
              {(formData.reporterName || formData.reporterPhone) && (
                <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700">
                  <p className="text-xs text-slate-400 uppercase tracking-wider">Contact</p>
                  {formData.reporterName && (
                    <p className="text-slate-100 mt-1">{formData.reporterName}</p>
                  )}
                  {formData.reporterPhone && (
                    <p className="text-slate-100">{formData.reporterPhone}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step: Success */}
        {step === 'success' && submitResponse?.success && (
          <div className="text-center space-y-6 py-8">
            <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle className="w-10 h-10 text-emerald-400" />
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-slate-100">Report Submitted!</h2>
              <p className="text-slate-400">Thank you for helping improve water services</p>
            </div>

            <div className="p-6 bg-slate-800/50 rounded-xl border border-slate-700 space-y-4">
              <div>
                <p className="text-sm text-slate-400">Your Ticket Number</p>
                <p className="text-3xl font-mono font-bold text-blue-400 mt-1">
                  {submitResponse.ticket}
                </p>
              </div>
              <p className="text-sm text-slate-400">
                Save this number to track your report status
              </p>
            </div>

            <div className="space-y-3">
              <Link
                href={`/track/${submitResponse.ticket}`}
                className="block w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors"
              >
                Track Your Report
              </Link>
              <Link
                href="/report"
                onClick={() => {
                  setStep('category')
                  setFormData({
                    category: '',
                    categoryLabel: '',
                    description: '',
                    latitude: null,
                    longitude: null,
                    areaText: '',
                    photos: [],
                    photoPreview: [],
                    reporterName: '',
                    reporterPhone: '',
                    reporterEmail: '',
                    reporterConsent: false,
                  })
                  setSubmitResponse(null)
                }}
                className="block w-full py-3 bg-slate-700 hover:bg-slate-600 text-slate-100 font-semibold rounded-xl transition-colors"
              >
                Submit Another Report
              </Link>
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        {step !== 'success' && (
          <div className="flex gap-3 mt-8">
            {step !== 'category' && (
              <button
                onClick={prevStep}
                className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 text-slate-100 font-semibold rounded-xl transition-colors"
              >
                Back
              </button>
            )}
            
            {step === 'review' ? (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-600/50 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Submit Report
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={nextStep}
                disabled={!canProceed()}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                Continue
                <ChevronRight className="w-5 h-5" />
              </button>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-2xl mx-auto px-4 py-8 text-center">
        <p className="text-sm text-slate-500">
          Powered by <span className="text-blue-400">AquaWatch NRW</span>
        </p>
        <p className="text-xs text-slate-600 mt-1">
          Helping reduce water loss in Zambia
        </p>
      </footer>
    </div>
  )
}
