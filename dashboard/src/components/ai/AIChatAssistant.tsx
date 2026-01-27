'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { usePathname } from 'next/navigation'
import { 
  Send, X, Bot, User, Brain, Loader2,
  RefreshCw, Activity, Droplets, AlertTriangle, Sparkles,
  Volume2, VolumeX, Square, Maximize2, Minimize2, Navigation, Map,
  Settings, ChevronDown, Mic
} from 'lucide-react'

// System pages knowledge base - AI knows about all pages in the system
const SYSTEM_PAGES = {
  '/app': {
    name: 'Main Dashboard',
    description: 'The central control room showing real-time NRW metrics, system health, DMA status, active alerts, and key performance indicators.',
    features: ['Live NRW percentage', 'System health indicators', 'Active alerts', 'DMA overview', 'Sensor status', 'Recent activity feed']
  },
  '/leaks': {
    name: 'Leak Detection & Management',
    description: 'AI-powered leak detection interface showing all detected leaks, their severity, location, and repair status.',
    features: ['Live leak map', 'AI confidence scores', 'Priority queue', 'Repair tracking', 'Historical leak data', 'Cost estimation']
  },
  '/dma': {
    name: 'DMA Management',
    description: 'District Metered Area monitoring with zone-by-zone water balance analysis and performance tracking.',
    features: ['Zone maps', 'Flow analysis', 'NRW by zone', 'Pressure monitoring', 'Connection counts', 'Trend analysis']
  },
  '/map': {
    name: 'Network Map',
    description: 'Interactive GIS map showing the entire water distribution network, sensors, pipes, and infrastructure.',
    features: ['Pipe network visualization', 'Sensor locations', 'Leak markers', 'Pressure zones', 'Layer controls', 'Search functionality']
  },
  '/analytics': {
    name: 'Analytics Dashboard',
    description: 'Advanced analytics with charts, trends, predictions, and AI-driven insights.',
    features: ['Trend charts', 'Consumption patterns', 'Loss analysis', 'Predictive models', 'Export reports', 'Custom date ranges']
  },
  '/reports': {
    name: 'Reports Center',
    description: 'Generate and view system reports including NRW reports, leak summaries, and compliance documents.',
    features: ['Auto-generated reports', 'Custom report builder', 'Export PDF/Excel', 'Scheduled reports', 'Historical archives']
  },
  '/billing': {
    name: 'Billing & Revenue',
    description: 'Customer billing management, revenue tracking, and payment processing.',
    features: ['Customer accounts', 'Bill generation', 'Payment tracking', 'Revenue analytics', 'Debt management']
  },
  '/meters': {
    name: 'Meter Management',
    description: 'Water meter inventory, readings, and smart meter integration.',
    features: ['Meter inventory', 'Reading history', 'Smart meter data', 'Anomaly detection', 'Replacement scheduling']
  },
  '/smart-meters': {
    name: 'Smart Meters',
    description: 'IoT smart meter monitoring with real-time data from connected devices.',
    features: ['Live readings', 'Battery status', 'Signal strength', 'Data quality', 'Alert configuration']
  },
  '/sensors': {
    name: 'Sensor Network',
    description: 'IoT sensor management including flow meters, pressure sensors, and acoustic sensors.',
    features: ['Sensor inventory', 'Live data feeds', 'Calibration status', 'Maintenance alerts', 'Network topology']
  },
  '/predictions': {
    name: 'AI Predictions',
    description: 'Machine learning predictions for demand forecasting, leak probability, and system optimization.',
    features: ['Demand forecast', 'Leak risk zones', 'Maintenance predictions', 'Optimization suggestions']
  },
  '/autonomous': {
    name: 'Autonomous Operations',
    description: 'AI-driven autonomous control for pressure management and flow optimization.',
    features: ['Auto pressure control', 'Valve automation', 'AI decisions log', 'Override controls']
  },
  '/work-orders': {
    name: 'Work Order Management',
    description: 'Field crew work orders, job assignments, and task tracking.',
    features: ['Job queue', 'Crew assignments', 'GPS tracking', 'Completion tracking', 'Materials used']
  },
  '/field': {
    name: 'Field Operations',
    description: 'Mobile field team interface for on-site repairs and inspections.',
    features: ['Mobile-optimized view', 'GPS navigation', 'Photo upload', 'Status updates', 'Offline mode']
  },
  '/tickets': {
    name: 'Support Tickets',
    description: 'Customer complaint and support ticket management system.',
    features: ['Ticket queue', 'Priority levels', 'Assignment routing', 'Resolution tracking', 'SLA monitoring']
  },
  '/notifications': {
    name: 'Notification Center',
    description: 'System alerts, warnings, and notification management.',
    features: ['Alert history', 'Notification rules', 'Email/SMS settings', 'Escalation paths']
  },
  '/staff': {
    name: 'Staff Management',
    description: 'Employee directory, roles, and access management.',
    features: ['Employee list', 'Role assignments', 'Shift schedules', 'Performance tracking']
  },
  '/admin': {
    name: 'System Administration',
    description: 'System configuration, user management, and administrative controls.',
    features: ['User management', 'System settings', 'API keys', 'Audit logs', 'Backup controls']
  },
  '/audit': {
    name: 'Audit Trail',
    description: 'Complete audit log of all system activities for compliance and security.',
    features: ['Activity logs', 'User actions', 'Data changes', 'Security events', 'Export for compliance']
  },
  '/finance': {
    name: 'Financial Dashboard',
    description: 'Financial metrics, cost analysis, and revenue tracking.',
    features: ['Revenue tracking', 'Cost analysis', 'Budget vs actual', 'Savings from NRW reduction']
  },
  '/executive': {
    name: 'Executive Dashboard',
    description: 'High-level KPI dashboard for management and executives.',
    features: ['KPI summary', 'Trend indicators', 'Benchmark comparison', 'Strategic metrics']
  },
  '/community': {
    name: 'Community Portal',
    description: 'Public engagement portal for community water information.',
    features: ['Public announcements', 'Conservation tips', 'Report issues', 'Water quality info']
  },
  '/report-leak': {
    name: 'Report a Leak',
    description: 'Public interface for citizens to report water leaks and issues.',
    features: ['Easy reporting form', 'Photo upload', 'Location picker', 'Tracking number']
  },
  '/customer-portal': {
    name: 'Customer Self-Service',
    description: 'Customer portal for bill viewing, payments, and service requests.',
    features: ['View bills', 'Make payments', 'Usage history', 'Service requests']
  },
  '/water-quality': {
    name: 'Water Quality',
    description: 'Water quality monitoring and testing results.',
    features: ['Quality parameters', 'Test results', 'Compliance status', 'Treatment data']
  },
  '/weather': {
    name: 'Weather Integration',
    description: 'Weather data integration for demand forecasting and planning.',
    features: ['Current weather', 'Forecast', 'Weather impact analysis', 'Historical correlation']
  },
  '/satellite': {
    name: 'Satellite Monitoring',
    description: 'Satellite imagery analysis for infrastructure monitoring.',
    features: ['Satellite imagery', 'Change detection', 'Vegetation analysis', 'Leak signatures']
  },
  '/inventory': {
    name: 'Inventory Management',
    description: 'Parts, materials, and equipment inventory tracking.',
    features: ['Stock levels', 'Reorder alerts', 'Usage tracking', 'Supplier management']
  },
  '/shift-handover': {
    name: 'Shift Handover',
    description: 'Operator shift change documentation and handover notes.',
    features: ['Handover notes', 'Pending issues', 'Shift summary', 'Action items']
  },
  '/command-center': {
    name: 'Command Center',
    description: 'Real-time operations command center with all critical displays.',
    features: ['Multi-screen view', 'Live alerts', 'System overview', 'Emergency controls']
  },
  '/login': {
    name: 'Login Page',
    description: 'Secure authentication portal for system access.',
    features: ['Username/password login', 'Role-based access', 'Session management']
  }
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: string[]
  isLoading?: boolean
}

interface SystemData {
  success: boolean
  data_available: boolean
  timestamp: string
  metrics: {
    timestamp: string
    total_nrw_percent: number
    total_inflow: number
    total_consumption: number
    total_losses: number
    water_recovered_30d: number
    revenue_recovered_30d: number
    sensor_count: number
    sensors_online: number
    dma_count: number
    active_high_priority_leaks: number
    ai_confidence: number
    detection_accuracy: number
    last_data_received: string | null
    public_reports_pending: number
    total_leaks: number
    active_alerts: number
  }
  dmas: Array<{
    dma_id: string
    name: string
    nrw_percent: number
    priority_score: number
    status: string
    trend: string
    inflow: number
    consumption: number
    real_losses: number
    connections: number
    leak_count: number
    pressure: number
    confidence: number
    last_updated: string
  }>
  sensors: {
    total: number
    online: number
    offline: number
    sensors: Array<{
      id: string
      name: string
      type: string
      status: string
      battery: number
      signal_strength: number
      last_reading: string | null
      dma: string | null
      flow_rate: number | null
      pressure: number | null
    }>
  }
  infrastructure: {
    status: string
    components: {
      api_server: { status: string; latency: number }
      database: { status: string; storage_percent: number }
      ai_engine: { status: string; model_version: string; accuracy: number }
      mqtt_broker: { status: string; connected_devices: number }
    }
  }
  recent_activity: {
    leaks_detected_today: number
    alerts_today: number
    reports_today: number
  }
}

interface ConversationMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export default function AIChatAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [systemData, setSystemData] = useState<SystemData | null>(null)
  const [lastFetch, setLastFetch] = useState<Date | null>(null)
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pathname = usePathname()
  
  // Get current page info
  const currentPageInfo = SYSTEM_PAGES[pathname as keyof typeof SYSTEM_PAGES] || SYSTEM_PAGES['/app']
  
  // Build system navigation knowledge
  const buildNavigationContext = (): string => {
    const pages = Object.entries(SYSTEM_PAGES).map(([path, info]) => 
      `- **${info.name}** (${path}): ${info.description} Features: ${info.features.join(', ')}`
    ).join('\n')
    
    return `
## SYSTEM NAVIGATION - ALL AVAILABLE PAGES:
The user is currently on: **${currentPageInfo.name}** (${pathname})
Current page features: ${currentPageInfo.features.join(', ')}

### Complete System Pages:
${pages}

When users ask about navigation, pages, or where to find features, use this information to guide them.
`
  }
  
  // Text-to-speech state
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null)
  const [showVoiceSettings, setShowVoiceSettings] = useState(false)
  const [voiceSpeed, setVoiceSpeed] = useState(0.95) // Natural speaking rate
  const speechSynthRef = useRef<SpeechSynthesisUtterance | null>(null)

  // Speech recognition (voice input) state
  const [isListening, setIsListening] = useState(false)
  const [interimTranscript, setInterimTranscript] = useState('')
  const [autoSendVoice, setAutoSendVoice] = useState(true) // Auto-send after voice input
  const [autoSpeakResponse, setAutoSpeakResponse] = useState(true) // Auto-speak AI response after voice input
  const [usedVoiceInput, setUsedVoiceInput] = useState(false) // Track if last input was voice
  const recognitionRef = useRef<any>(null)
  const voiceInputRef = useRef<string>('')  // Track voice input for auto-send

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window === 'undefined') return

    // Check for browser support
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsListening(true)
      setInterimTranscript('')
      voiceInputRef.current = ''
    }

    recognition.onresult = (event: any) => {
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          final += transcript
        } else {
          interim += transcript
        }
      }

      if (final) {
        const newValue = final.trim()
        setInput(prev => {
          voiceInputRef.current = prev + newValue
          return prev + newValue
        })
        setInterimTranscript('')
      } else {
        setInterimTranscript(interim)
      }
    }

    recognition.onerror = (event: any) => {
      console.warn('Speech recognition error:', event.error)
      setIsListening(false)
      setInterimTranscript('')
      
      // Show user-friendly error messages
      if (event.error === 'no-speech') {
        // Silent - user just didn't speak
      } else if (event.error === 'audio-capture') {
        alert('No microphone found. Please check your microphone settings.')
      } else if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please allow microphone access in your browser settings.')
      }
    }

    recognition.onend = () => {
      setIsListening(false)
      setInterimTranscript('')
      // Auto-send the voice input
      const voiceText = voiceInputRef.current.trim()
      if (voiceText) {
        // Mark that voice input was used (for auto-speak response)
        setUsedVoiceInput(true)
        // Delay to show transcribed text briefly
        setTimeout(() => {
          if (handleSendRef.current) {
            handleSendRef.current(voiceText)
          }
        }, 300)
      }
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [])

  // Auto-send voice input when recognition ends
  const handleVoiceSend = useCallback((text: string) => {
    if (text.trim() && autoSendVoice) {
      // Small delay to show the user what was transcribed
      setTimeout(() => {
        handleSendRef.current?.(text)
      }, 500)
    }
  }, [autoSendVoice])

  // Reference to handleSend for voice callback
  const handleSendRef = useRef<((text?: string) => Promise<void>) | null>(null)

  // Toggle voice input
  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      try {
        setInterimTranscript('')
        recognitionRef.current.start()
      } catch (error) {
        console.error('Error starting speech recognition:', error)
        setIsListening(false)
      }
    }
  }, [isListening])

  // Clean text for speech (remove markdown formatting)
  const cleanTextForSpeech = (text: string): string => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
      .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
      .replace(/#{1,6}\s/g, '') // Remove headers
      .replace(/`(.*?)`/g, '$1') // Remove code formatting
      .replace(/•/g, '. ') // Replace bullets with periods
      .replace(/\n{2,}/g, '. ') // Replace multiple newlines with period
      .replace(/\n/g, '. ') // Replace newlines with period
      .replace(/📊|🎯|👋|💬|📡|💡|⚠️|✅|❌|🔴|🟡|🟢|✨|🚰|💧/g, '') // Remove emojis
      .trim()
  }

  // Get the best available voice - prioritize natural/neural voices
  const getBestVoice = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null
    
    const voices = window.speechSynthesis.getVoices()
    if (!voices.length) return null

    // Priority list for high-quality voices (neural/natural sounding)
    const premiumVoicePatterns = [
      // Microsoft Neural voices (Edge/Windows 11) - Best quality
      { pattern: /Microsoft.*Online.*Natural/i, priority: 1 },
      { pattern: /Microsoft.*Aria/i, priority: 2 },
      { pattern: /Microsoft.*Jenny/i, priority: 3 },
      { pattern: /Microsoft.*Guy/i, priority: 4 },
      { pattern: /Microsoft.*Davis/i, priority: 5 },
      // Google voices (Chrome)
      { pattern: /Google.*US.*English/i, priority: 6 },
      { pattern: /Google.*UK.*English/i, priority: 7 },
      // Apple voices (Safari/macOS)
      { pattern: /Samantha/i, priority: 8 },
      { pattern: /Alex/i, priority: 9 },
      { pattern: /Karen/i, priority: 10 },
      { pattern: /Daniel/i, priority: 11 },
      // Other quality voices
      { pattern: /Natural/i, priority: 12 },
      { pattern: /Neural/i, priority: 13 },
      { pattern: /Premium/i, priority: 14 },
    ]

    // Find the best voice based on priority
    let bestVoice: SpeechSynthesisVoice | null = null
    let bestPriority = Infinity

    for (const voice of voices) {
      // Only consider English voices
      if (!voice.lang.startsWith('en')) continue

      for (const { pattern, priority } of premiumVoicePatterns) {
        if (pattern.test(voice.name) && priority < bestPriority) {
          bestVoice = voice
          bestPriority = priority
          break
        }
      }
    }

    // Fallback to any English voice if no premium voice found
    if (!bestVoice) {
      bestVoice = voices.find(v => v.lang === 'en-US') 
        || voices.find(v => v.lang === 'en-GB')
        || voices.find(v => v.lang.startsWith('en'))
        || voices[0]
    }

    return bestVoice
  }, [])

  // Initialize voices (they load async in some browsers)
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([])
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices()
      setAvailableVoices(voices)
      if (!selectedVoice) {
        setSelectedVoice(getBestVoice())
      }
    }

    // Load voices immediately if available
    loadVoices()

    // Also listen for voiceschanged event (Chrome loads voices async)
    window.speechSynthesis.onvoiceschanged = loadVoices

    return () => {
      window.speechSynthesis.onvoiceschanged = null
    }
  }, [getBestVoice, selectedVoice])

  // Text-to-speech function with improved voice
  const speakText = useCallback((text: string, messageId: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      console.warn('Speech synthesis not supported')
      return
    }

    // Stop any current speech
    window.speechSynthesis.cancel()

    const cleanText = cleanTextForSpeech(text)
    
    // Split into sentences for more natural pauses
    const sentences = cleanText.match(/[^.!?]+[.!?]+/g) || [cleanText]
    
    let currentIndex = 0
    
    const speakNextSentence = () => {
      if (currentIndex >= sentences.length) {
        setIsSpeaking(false)
        setSpeakingMessageId(null)
        return
      }

      const sentence = sentences[currentIndex].trim()
      if (!sentence) {
        currentIndex++
        speakNextSentence()
        return
      }

      const utterance = new SpeechSynthesisUtterance(sentence)
      
      // Use the selected voice or get the best one
      const voice = selectedVoice || getBestVoice()
      if (voice) {
        utterance.voice = voice
      }

      // Natural speech settings with user-configurable speed
      utterance.rate = voiceSpeed
      utterance.pitch = 1.05 // Slightly higher for more engaging sound
      utterance.volume = 1.0

      utterance.onstart = () => {
        if (currentIndex === 0) {
          setIsSpeaking(true)
          setSpeakingMessageId(messageId)
        }
      }

      utterance.onend = () => {
        currentIndex++
        // Small pause between sentences
        setTimeout(speakNextSentence, 150)
      }

      utterance.onerror = (e) => {
        console.warn('Speech error:', e)
        setIsSpeaking(false)
        setSpeakingMessageId(null)
      }

      speechSynthRef.current = utterance
      window.speechSynthesis.speak(utterance)
    }

    speakNextSentence()
  }, [selectedVoice, getBestVoice, voiceSpeed])

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    setIsSpeaking(false)
    setSpeakingMessageId(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  // Fetch real system data from database
  const fetchSystemData = async (): Promise<SystemData | null> => {
    try {
      const response = await fetch('/api/ai/system-data')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data: SystemData = await response.json()
      setSystemData(data)
      setLastFetch(new Date())
      console.log('[AI Assistant] System data loaded:', data.data_available ? 'Data available' : 'No data yet')
      return data
    } catch (error) {
      console.error('[AI Assistant] Failed to fetch system data:', error)
      return null
    }
  }

  // Build system context from live data
  const buildSystemContext = (data: SystemData | null): string => {
    if (!data || !data.metrics) return 'No live system data available. The system is initializing.'
    
    if (!data.data_available) {
      return `LWSC WATER SYSTEM STATUS: No sensor data available yet.
The system is ready but waiting for sensors to be connected.
Infrastructure: ${data.infrastructure?.status || 'checking'}
Database: ${data.infrastructure?.components?.database?.status || 'checking'}`
    }
    
    const criticalDmas = data.dmas?.filter(d => d.status === 'critical') || []
    const warningDmas = data.dmas?.filter(d => d.status === 'warning') || []
    const totalLeaks = data.dmas?.reduce((sum, d) => sum + (d.leak_count || 0), 0) || 0
    
    return `
LIVE LWSC WATER SYSTEM DATA (as of ${new Date().toLocaleTimeString()}):

NETWORK METRICS:
- Total NRW (Non-Revenue Water): ${data.metrics.total_nrw_percent ?? 0}%
- Total Inflow: ${(data.metrics.total_inflow ?? 0).toLocaleString()} m³/hr
- Total Consumption: ${(data.metrics.total_consumption ?? 0).toLocaleString()} m³/hr  
- Total Losses: ${(data.metrics.total_losses ?? 0).toLocaleString()} m³/hr
- Water Recovered (30 days): ${(data.metrics.water_recovered_30d ?? 0).toLocaleString()} m³
- Revenue Recovered (30 days): K${(data.metrics.revenue_recovered_30d ?? 0).toLocaleString()}
- Active High Priority Leaks: ${data.metrics.active_high_priority_leaks ?? 0}
- Total Leaks Detected: ${data.metrics.total_leaks ?? 0}
- Active Alerts: ${data.metrics.active_alerts ?? 0}
- AI Detection Confidence: ${data.metrics.ai_confidence ?? 0}%
- Detection Accuracy: ${data.metrics.detection_accuracy ?? 0}%

SENSORS:
- Total Sensors: ${data.sensors?.total ?? data.metrics.sensor_count ?? 0}
- Sensors Online: ${data.sensors?.online ?? data.metrics.sensors_online ?? 0}
- Sensors Offline: ${data.sensors?.offline ?? 0}
${data.sensors?.sensors?.length ? `- Sensor Details: ${data.sensors.sensors.slice(0, 5).map(s => `${s.name}: ${s.status}, Battery ${s.battery ?? 0}%, Signal ${s.signal_strength ?? 0}%`).join('; ')}${data.sensors.sensors.length > 5 ? ` ...and ${data.sensors.sensors.length - 5} more` : ''}` : '- No sensors connected yet'}

DMAs (District Metered Areas):
- Total DMAs: ${data.dmas?.length ?? data.metrics.dma_count ?? 0}
- Critical (need immediate attention): ${criticalDmas.length} - ${criticalDmas.map(d => d.name).join(', ') || 'None'}
- Warning: ${warningDmas.length} - ${warningDmas.map(d => d.name).join(', ') || 'None'}
- Total Active Leaks: ${totalLeaks}

${data.dmas?.length ? `DMA DETAILS:\n${data.dmas.map(d => `- ${d.name}: NRW ${d.nrw_percent ?? 0}%, Status ${d.status}, ${d.leak_count ?? 0} leaks, Inflow ${d.inflow ?? 0} m³/hr, Losses ${d.real_losses ?? 0} m³/hr, ${d.connections ?? 0} connections`).join('\n')}` : 'No DMAs configured yet.'}

INFRASTRUCTURE STATUS:
- API Server: ${data.infrastructure?.components?.api_server?.status ?? 'unknown'} (${data.infrastructure?.components?.api_server?.latency ?? 0}ms latency)
- Database: ${data.infrastructure?.components?.database?.status ?? 'unknown'} (${data.infrastructure?.components?.database?.storage_percent ?? 0}% storage used)
- AI Engine: ${data.infrastructure?.components?.ai_engine?.status ?? 'unknown'} (v${data.infrastructure?.components?.ai_engine?.model_version ?? '0.0.0'}, ${data.infrastructure?.components?.ai_engine?.accuracy ?? 0}% accuracy)
- MQTT Broker: ${data.infrastructure?.components?.mqtt_broker?.status ?? 'unknown'} (${data.infrastructure?.components?.mqtt_broker?.connected_devices ?? 0} devices)

RECENT ACTIVITY:
- Leaks Detected Today: ${data.recent_activity?.leaks_detected_today ?? 0}
- Alerts Today: ${data.recent_activity?.alerts_today ?? 0}
- Public Reports Today: ${data.recent_activity?.reports_today ?? 0}
- Pending Public Reports: ${data.metrics.public_reports_pending ?? 0}
`.trim()
  }

  // Initial data fetch and welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      fetchSystemData().then(data => {
        const hasRealData = data?.data_available && data?.metrics
        const nrwPercent = data?.metrics?.total_nrw_percent ?? 0
        const dmaCount = data?.dmas?.length ?? 0
        const criticalDmas = data?.dmas?.filter((d: any) => d.status === 'critical').length ?? 0
        const sensorsOnline = data?.metrics?.sensors_online ?? 0
        const sensorCount = data?.metrics?.sensor_count ?? 0
        const aiConfidence = data?.metrics?.ai_confidence ?? 92

        const welcomeMessage: Message = {
          id: '0',
          role: 'assistant',
          content: hasRealData 
            ? `👋 **Hello! I'm LWSC AI Assistant** - your intelligent companion powered by advanced AI.\n\n📍 **You're on: ${currentPageInfo.name}**\n${currentPageInfo.description}\n\n📊 **Live System Status:**\n• Network NRW: **${nrwPercent}%**\n• Active DMAs: **${dmaCount}** (${criticalDmas} critical)\n• Sensors Online: **${sensorsOnline}/${sensorCount}**\n• AI Confidence: **${aiConfidence}%**\n${data?.metrics?.active_high_priority_leaks ? `• ⚠️ High Priority Leaks: **${data.metrics.active_high_priority_leaks}**` : ''}\n\n🧭 **I know the entire system!** Ask me:\n• "What can I do on this page?"\n• "Where do I find leak reports?"\n• "Navigate to analytics"\n• Or ask anything else!\n\nHow can I help you today?`
            : `👋 **Hello! I'm LWSC AI Assistant** - your intelligent companion.\n\n📍 **You're on: ${currentPageInfo.name}**\n${currentPageInfo.description}\n\n📡 **System Status:** Waiting for sensor data...\n\n🧭 **I know all ${Object.keys(SYSTEM_PAGES).length} pages of this system!**\nAsk me about:\n• What features are on each page\n• How to navigate the system\n• Water management & NRW\n• General questions\n\nHow can I assist you today?`,
          timestamp: new Date(),
          suggestions: ['What can I do here?', 'Show all pages', 'System status', 'Help']
        }
        setMessages([welcomeMessage])
        
        // Initialize conversation history with enhanced system prompt including navigation
        setConversationHistory([{
          role: 'system',
          content: `You are LWSC AI Assistant, an advanced AI assistant similar to ChatGPT, specialized for Lusaka Water & Sewerage Company (LWSC) in Zambia. 

## Your Role:
- Answer ANY question (water-related or general) intelligently and helpfully
- Be conversational, friendly, and engaging
- Use markdown formatting and emojis where appropriate
- Provide accurate, detailed responses

## Live Data Access:
${buildSystemContext(data)}

Remember: You can discuss ANY topic, not just water! Be as helpful as ChatGPT.`
        }])
      })
    }
  }, [isOpen, messages.length])

  // Refresh data periodically when chat is open
  useEffect(() => {
    if (isOpen) {
      const interval = setInterval(fetchSystemData, 30000)
      return () => clearInterval(interval)
    }
  }, [isOpen])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Call AI API for intelligent responses
  const callAI = async (userMessage: string): Promise<{ content: string, suggestions: string[] }> => {
    // Update system context with latest data
    const latestData = await fetchSystemData()
    
    // Build messages for AI - Enhanced ChatGPT-like system prompt with navigation knowledge
    const updatedHistory: ConversationMessage[] = [
      {
        role: 'system',
        content: `You are LWSC AI Assistant, an advanced AI assistant similar to ChatGPT, specialized for Lusaka Water & Sewerage Company (LWSC) in Zambia. You are knowledgeable, helpful, and conversational.

## Your Capabilities:
1. **Water Management Expert**: Deep knowledge of NRW (Non-Revenue Water), leak detection, pressure management, water distribution, DMAs, and utility operations
2. **General Assistant**: You can answer ANY question like ChatGPT - math, science, history, coding, writing, analysis, advice, etc.
3. **Real-Time Data Access**: You have live system data from LWSC sensors, DMAs, and infrastructure
4. **System Navigation Expert**: You know ALL pages in this system and can guide users to the right place
5. **Multilingual**: You can respond in English, and understand basic local context (Zambia)

## Conversation Style:
- Be friendly, conversational, and engaging like ChatGPT
- Use emojis sparingly but effectively for visual appeal 🎯
- Format responses with markdown: **bold**, *italic*, bullet points, numbered lists
- Keep responses focused but thorough (150-400 words typically)
- Ask clarifying questions when needed
- Remember context from the conversation

## When Answering:
- For water/LWSC questions: Use the live data provided below
- For navigation/page questions: Use the system pages knowledge to guide users
- For general questions: Answer knowledgeably like ChatGPT would
- Always be accurate and helpful
- If you don't know something, say so honestly

## Response Format:
At the end of your response, ALWAYS provide 2-4 suggested follow-up questions in this exact format:
[SUGGESTIONS: question1 | question2 | question3]

${buildNavigationContext()}

## CURRENT LIVE LWSC SYSTEM DATA:
${buildSystemContext(latestData)}

You are both a water utility expert AND a general-purpose AI assistant with complete system knowledge. Answer any question the user asks - don't limit yourself to only water topics!`
      },
      ...conversationHistory.filter(m => m.role !== 'system'),
      { role: 'user', content: userMessage }
    ]

    try {
      // Call AI API
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: updatedHistory,
          systemData: latestData
        })
      })

      if (!response.ok) {
        throw new Error('AI service unavailable')
      }

      const data = await response.json()
      let content = data.content || data.message || 'I apologize, but I couldn\'t generate a response.'
      
      // Extract suggestions if present
      let suggestions: string[] = ['System status', 'Show NRW', 'Help']
      const suggestionsMatch = content.match(/\[SUGGESTIONS?:\s*([^\]]+)\]/i)
      if (suggestionsMatch) {
        suggestions = suggestionsMatch[1].split('|').map((s: string) => s.trim()).filter((s: string) => s.length > 0)
        content = content.replace(/\[SUGGESTIONS?:\s*[^\]]+\]/i, '').trim()
      }

      // Update conversation history
      setConversationHistory([
        ...updatedHistory,
        { role: 'assistant', content }
      ])

      return { content, suggestions }
    } catch (error) {
      console.error('AI API error:', error)
      // Fallback to local response if API fails
      return generateLocalResponse(userMessage, latestData)
    }
  }

  // Local fallback response generator (used when API is unavailable)
  const generateLocalResponse = (query: string, data: SystemData | null): { content: string, suggestions: string[] } => {
    if (!data || !data.metrics) {
      return {
        content: `⚠️ Unable to connect to system data. Please check your connection and try again.\n\nThe system is ready but waiting for sensor data to be available.`,
        suggestions: ['Retry', 'Check system health', 'What is NRW?']
      }
    }

    const q = query.toLowerCase()
    const metrics = data.metrics
    const dmas = data.dmas || []
    const sensors = data.sensors || { total: 0, online: 0, offline: 0, sensors: [] }
    const infrastructure = data.infrastructure || { status: 'unknown', components: {} }

    // System status / overview
    if (q.includes('status') || q.includes('overview') || q.includes('system') || q.includes('health')) {
      const criticalDmas = dmas.filter((d: any) => d.status === 'critical')
      const warningDmas = dmas.filter((d: any) => d.status === 'warning')
      const offlineSensors = sensors.sensors?.filter((s: any) => s.status !== 'online') || []
      
      return {
        content: `📊 **Live System Status** (as of ${new Date().toLocaleTimeString()})\n\n` +
          `**Network Performance:**\n` +
          `• Total NRW: **${metrics.total_nrw_percent ?? 0}%** ${(metrics.total_nrw_percent ?? 0) > 35 ? '🔴' : (metrics.total_nrw_percent ?? 0) > 25 ? '🟡' : '🟢'}\n` +
          `• Water Inflow: **${(metrics.total_inflow ?? 0).toLocaleString()} m³/hr**\n` +
          `• Consumption: **${(metrics.total_consumption ?? 0).toLocaleString()} m³/hr**\n` +
          `• Losses: **${(metrics.total_losses ?? 0).toLocaleString()} m³/hr**\n` +
          `• Active Leaks: **${metrics.total_leaks ?? 0}** (${metrics.active_high_priority_leaks ?? 0} high priority)\n\n` +
          `**Infrastructure:**\n` +
          `• API Server: ${infrastructure.components?.api_server?.status === 'healthy' ? '✅' : '⚠️'} ${infrastructure.components?.api_server?.latency ?? 0}ms\n` +
          `• Database: ${infrastructure.components?.database?.status === 'healthy' ? '✅' : '⚠️'} ${infrastructure.components?.database?.storage_percent ?? 0}% storage\n` +
          `• AI Engine: ${infrastructure.components?.ai_engine?.status === 'healthy' ? '✅' : '⚠️'} v${infrastructure.components?.ai_engine?.model_version ?? '0.0.0'}\n` +
          `• MQTT: ${infrastructure.components?.mqtt_broker?.status === 'healthy' ? '✅' : infrastructure.components?.mqtt_broker?.status === 'waiting' ? '⏳' : '⚠️'} ${infrastructure.components?.mqtt_broker?.connected_devices ?? 0} devices\n\n` +
          `**Sensors:** ${sensors.online ?? 0}/${sensors.total ?? 0} online\n` +
          `**Alerts:** ${criticalDmas.length} critical, ${warningDmas.length} warning, ${offlineSensors.length} sensors offline`,
        suggestions: ['Show critical DMAs', 'Sensor details', 'NRW breakdown']
      }
    }

    // NRW queries
    if (q.includes('nrw') || q.includes('non-revenue') || q.includes('loss') || q.includes('water loss')) {
      if (dmas.length === 0) {
        return {
          content: `📉 **NRW Analysis**\n\n` +
            `**Network Summary:**\n` +
            `• Current NRW Rate: **${metrics.total_nrw_percent ?? 0}%**\n` +
            `• Total Leaks Detected: **${metrics.total_leaks ?? 0}**\n` +
            `• High Priority Leaks: **${metrics.active_high_priority_leaks ?? 0}**\n` +
            `• 30-Day Water Recovered: **${(metrics.water_recovered_30d ?? 0).toLocaleString()} m³**\n` +
            `• 30-Day Revenue Recovered: **K${(metrics.revenue_recovered_30d ?? 0).toLocaleString()}**\n\n` +
            `📡 No DMAs configured yet. Add DMAs to see detailed zone analysis.`,
          suggestions: ['What is NRW?', 'System status', 'How to reduce NRW']
        }
      }
      
      const sortedByNrw = [...dmas].sort((a: any, b: any) => (b.nrw_percent ?? 0) - (a.nrw_percent ?? 0))
      const worst3 = sortedByNrw.slice(0, 3)
      const best3 = sortedByNrw.slice(-3).reverse()
      
      return {
        content: `📉 **Live NRW Analysis** (Updated: ${new Date().toLocaleTimeString()})\n\n` +
          `**Network Summary:**\n` +
          `• Current NRW Rate: **${metrics.total_nrw_percent ?? 0}%**\n` +
          `• Daily Loss Volume: **${Math.round((metrics.total_losses ?? 0) * 24).toLocaleString()} m³**\n` +
          `• Est. Revenue Loss: **K${Math.round((metrics.total_losses ?? 0) * 24 * 50).toLocaleString()}/day**\n` +
          `• 30-Day Recovery: **K${(metrics.revenue_recovered_30d ?? 0).toLocaleString()}**\n\n` +
          `**Worst Performing DMAs:**\n` +
          worst3.map((d: any, i: number) => `${i + 1}. **${d.name}** - ${d.nrw_percent ?? 0}% ${d.status === 'critical' ? '🔴' : '🟡'}`).join('\n') +
          `\n\n**Best Performing DMAs:**\n` +
          best3.map((d: any, i: number) => `${i + 1}. **${d.name}** - ${d.nrw_percent ?? 0}% 🟢`).join('\n') +
          (worst3[0] ? `\n\n💡 **AI Tip:** Focus on ${worst3[0].name} to reduce NRW by ~${Math.round((worst3[0].nrw_percent ?? 0) * 0.1)}%` : ''),
        suggestions: worst3[0] ? [`Details: ${worst3[0].name}`, 'Show all DMAs', 'NRW trend'] : ['Show all DMAs', 'System status']
      }
    }

    // DMA queries
    if (q.includes('dma') || q.includes('zone') || q.includes('district') || q.includes('area')) {
      if (dmas.length === 0) {
        return {
          content: `🗺️ **District Metered Areas (DMAs)**\n\n` +
            `No DMAs configured in the system yet.\n\n` +
            `DMAs are geographic zones used to monitor water distribution and detect losses. ` +
            `Configure DMAs in the admin panel to begin zone-by-zone monitoring.`,
          suggestions: ['What are DMAs?', 'System status', 'How to configure DMAs']
        }
      }
      
      const criticalDmas = dmas.filter((d: any) => d.status === 'critical')
      const warningDmas = dmas.filter((d: any) => d.status === 'warning')
      
      // Check for specific DMA
      const specificDma = dmas.find((d: any) => q.includes(d.name.toLowerCase()))
      if (specificDma) {
        return {
          content: `🗺️ **${specificDma.name} - Live Data**\n\n` +
            `**Performance:**\n` +
            `• NRW Rate: **${specificDma.nrw_percent ?? 0}%** ${specificDma.status === 'critical' ? '🔴' : specificDma.status === 'warning' ? '🟡' : '🟢'}\n` +
            `• Priority Score: **${specificDma.priority_score ?? 0}/100**\n` +
            `• Trend: ${specificDma.trend === 'up' ? '📈 Increasing' : specificDma.trend === 'down' ? '📉 Improving' : '➡️ Stable'}\n\n` +
            `**Flow Data:**\n` +
            `• Inflow: **${specificDma.inflow ?? 0} m³/hr**\n` +
            `• Consumption: **${specificDma.consumption ?? 0} m³/hr**\n` +
            `• Losses: **${specificDma.real_losses ?? 0} m³/hr**\n` +
            `• Pressure: **${specificDma.pressure ?? 0} bar**\n\n` +
            `**Coverage:** ${(specificDma.connections ?? 0).toLocaleString()} connections | ${specificDma.leak_count ?? 0} leaks`,
          suggestions: ['Compare DMAs', 'Dispatch crew', 'Show leaks']
        }
      }

      // Critical DMAs
      if (q.includes('critical') || q.includes('worst') || q.includes('priority')) {
        return {
          content: `🚨 **Critical DMAs Requiring Attention**\n\n` +
            (criticalDmas.length > 0 
              ? criticalDmas.map((d: any, i: number) => 
                  `**${i + 1}. ${d.name}** (Score: ${d.priority_score ?? 0})\n` +
                  `   NRW: ${d.nrw_percent ?? 0}% | Losses: ${d.real_losses ?? 0} m³/hr | Leaks: ${d.leak_count ?? 0}`
                ).join('\n\n')
              : '✅ No critical DMAs!') +
            (warningDmas.length > 0 
              ? `\n\n**Warning (${warningDmas.length}):** ${warningDmas.map((d: any) => d.name).join(', ')}`
              : '') +
            `\n\n💡 Potential savings: **K${Math.round(criticalDmas.reduce((sum: number, d: any) => sum + (d.real_losses ?? 0) * 24 * 50 * 0.3, 0)).toLocaleString()}/day**`,
          suggestions: criticalDmas.length > 0 ? [`Fix ${criticalDmas[0].name}`, 'Dispatch crews'] : ['View all DMAs']
        }
      }

      // All DMAs
      return {
        content: `🗺️ **All DMAs - Live Status**\n\n` +
          dmas.map((d: any, i: number) => 
            `**${i + 1}. ${d.name}** ${d.status === 'critical' ? '🔴' : d.status === 'warning' ? '🟡' : '🟢'}\n` +
            `   NRW: ${d.nrw_percent ?? 0}% | Inflow: ${d.inflow ?? 0} m³/hr | Leaks: ${d.leak_count ?? 0}`
          ).join('\n\n') +
          `\n\n**Summary:** ${criticalDmas.length} critical, ${warningDmas.length} warning`,
        suggestions: ['Critical only', 'NRW breakdown', 'Best performers']
      }
    }

    // Sensor queries
    if (q.includes('sensor') || q.includes('meter') || q.includes('device') || q.includes('iot')) {
      const sensorList = sensors.sensors || []
      if (sensorList.length === 0) {
        return {
          content: `📡 **Sensor Network**\n\n` +
            `No sensors configured yet.\n\n` +
            `Connect ESP32 sensors via MQTT to begin real-time monitoring. ` +
            `See the documentation for setup instructions.`,
          suggestions: ['Setup guide', 'System status', 'What sensors do I need?']
        }
      }
      
      const onlineSensors = sensorList.filter((s: any) => s.status === 'online')
      const offlineSensors = sensorList.filter((s: any) => s.status !== 'online')
      const lowBattery = sensorList.filter((s: any) => (s.battery ?? 100) < 30)
      
      return {
        content: `📡 **Sensor Network - Live**\n\n` +
          `**Overview:**\n` +
          `• Total: **${sensorList.length}**\n` +
          `• Online: **${onlineSensors.length}** ✅\n` +
          `• Offline: **${offlineSensors.length}** ${offlineSensors.length > 0 ? '⚠️' : ''}\n` +
          `• Low Battery: **${lowBattery.length}** ${lowBattery.length > 0 ? '🔋' : ''}\n\n` +
          `**Sensors:**\n` +
          sensorList.slice(0, 10).map((s: any) => 
            `• **${s.name}**\n  ${s.status === 'online' ? '🟢' : '🔴'} ${s.status} | 🔋 ${s.battery ?? 0}% | 📶 ${s.signal_strength ?? 0}%`
          ).join('\n\n') +
          (sensorList.length > 10 ? `\n\n...and ${sensorList.length - 10} more sensors` : '') +
          (lowBattery.length > 0 
            ? `\n\n⚠️ **Low Battery:** ${lowBattery.map((s: any) => `${s.name} (${s.battery ?? 0}%)`).join(', ')}`
            : ''),
        suggestions: lowBattery.length > 0 ? ['Schedule maintenance', 'Battery report'] : ['View readings']
      }
    }

    // Leak queries
    if (q.includes('leak') || q.includes('burst') || q.includes('pipe')) {
      const dmasWithLeaks = dmas.filter((d: any) => (d.leak_count ?? 0) > 0).sort((a: any, b: any) => (b.leak_count ?? 0) - (a.leak_count ?? 0))
      const totalLeaks = dmas.reduce((sum: number, d: any) => sum + (d.leak_count ?? 0), 0)
      
      return {
        content: `🔍 **Active Leak Detection** (Live)\n\n` +
          `**Summary:**\n` +
          `• Total Leaks: **${totalLeaks}**\n` +
          `• High Priority: **${metrics.active_high_priority_leaks ?? 0}**\n` +
          `• Water Loss: **${(metrics.total_losses ?? 0).toLocaleString()} m³/hr**\n` +
          `• AI Accuracy: **${metrics.detection_accuracy ?? 0}%**\n\n` +
          `**By Location:**\n` +
          (dmasWithLeaks.length > 0 
            ? dmasWithLeaks.map((d: any, i: number) => 
                `**${i + 1}. ${d.name}** - ${d.leak_count ?? 0} leak${(d.leak_count ?? 0) > 1 ? 's' : ''} ${d.status === 'critical' ? '🔴' : '🟡'}\n` +
                `   Losses: ${d.real_losses ?? 0} m³/hr | Pressure: ${d.pressure ?? 0} bar`
              ).join('\n\n')
            : '✅ No active leaks!') +
          `\n\n💡 ${dmasWithLeaks.length > 0 
            ? `Fix ${dmasWithLeaks[0].name} to save K${Math.round((dmasWithLeaks[0].real_losses ?? 0) * 24 * 50).toLocaleString()}/day`
            : 'Network performing well!'}`,
        suggestions: dmasWithLeaks.length > 0 
          ? [`Fix ${dmasWithLeaks[0].name}`, 'Show on map', 'Dispatch crew']
          : ['View predictions', 'Check sensors']
      }
    }

    // Crew / dispatch
    if (q.includes('crew') || q.includes('team') || q.includes('dispatch') || q.includes('technician')) {
      const priorityDmas = dmas.filter((d: any) => (d.leak_count ?? 0) > 0).slice(0, 4)
      if (priorityDmas.length === 0) {
        return {
          content: `👷 **Dispatch Recommendations**\n\n` +
            `✅ No active leaks requiring dispatch at this time.\n\n` +
            `The network is performing well. Continue monitoring for new issues.`,
          suggestions: ['System status', 'View sensors', 'Schedule maintenance']
        }
      }
      return {
        content: `👷 **Dispatch Recommendations** (Based on Live Data)\n\n` +
          `**Priority Deployments:**\n` +
          priorityDmas.map((d: any, i: number) => 
            `${i + 1}. **${d.name}** - ${d.leak_count ?? 0} leak${(d.leak_count ?? 0) > 1 ? 's' : ''}\n` +
            `   Priority: ${d.priority_score ?? 0}/100 | Est. time: ${(d.leak_count ?? 1) * 2}h`
          ).join('\n\n') +
          `\n\n**Optimal Route:**\n` +
          `${priorityDmas.slice(0, 3).map((d: any) => d.name).join(' → ')}\n` +
          `Est. time saved: ~2.4 hours\n\n` +
          `💡 Start with **${priorityDmas[0]?.name || 'N/A'}** - highest impact`,
        suggestions: ['Create work order', 'View all tasks', 'Optimize routes']
      }
    }

    // Report / summary
    if (q.includes('report') || q.includes('summary') || q.includes('daily') || q.includes('today')) {
      return {
        content: `📋 **System Report** (${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()})\n\n` +
          `**Network:**\n` +
          `• NRW: ${metrics.total_nrw_percent ?? 0}%\n` +
          `• Inflow: ${(metrics.total_inflow ?? 0).toLocaleString()} m³/hr\n` +
          `• Losses: ${(metrics.total_losses ?? 0).toLocaleString()} m³/hr\n` +
          `• Total Leaks: ${metrics.total_leaks ?? 0}\n\n` +
          `**DMAs:** ${dmas.length} total\n` +
          `• Critical: ${dmas.filter((d: any) => d.status === 'critical').length}\n` +
          `• Warning: ${dmas.filter((d: any) => d.status === 'warning').length}\n` +
          `• Healthy: ${dmas.filter((d: any) => d.status === 'healthy').length}\n\n` +
          `**Sensors:** ${sensors.online ?? metrics.sensors_online ?? 0}/${sensors.total ?? metrics.sensor_count ?? 0} online\n\n` +
          `**30-Day Recovery:**\n` +
          `• Water: ${(metrics.water_recovered_30d ?? 0).toLocaleString()} m³\n` +
          `• Revenue: K${(metrics.revenue_recovered_30d ?? 0).toLocaleString()}\n\n` +
          `AI Confidence: ${metrics.ai_confidence ?? 0}%`,
        suggestions: ['Export PDF', 'Weekly trend', 'Compare periods']
      }
    }

    // Help
    if (q.includes('help') || q.includes('what can') || q.includes('how to')) {
      return {
        content: `👋 **I'm LWSC AI Assistant** - Connected to Live Data!\n\n` +
          `**Ask me about:**\n\n` +
          `🔍 **Leaks:** "Show active leaks", "Where are leaks?"\n` +
          `📊 **NRW:** "What's our NRW?", "Worst DMAs"\n` +
          `🗺️ **DMAs:** "Critical DMAs", "Details for Kabulonga"\n` +
          `📡 **Sensors:** "Sensor health", "Low battery"\n` +
          `📋 **Reports:** "System status", "Daily summary"\n` +
          `👷 **Dispatch:** "Dispatch crews", "Priority tasks"\n\n` +
          `I fetch **real-time data** for every response!`,
        suggestions: ['System status', 'Show NRW', 'Critical DMAs', 'Sensors']
      }
    }

    // Default
    return {
      content: `I understand you're asking about "${query}".\n\n` +
        `**Current System:**\n` +
        `• NRW: ${metrics.total_nrw_percent}%\n` +
        `• Leaks: ${dmas.reduce((sum: number, d: any) => sum + d.leak_count, 0)}\n` +
        `• Critical DMAs: ${dmas.filter((d: any) => d.status === 'critical').length}\n` +
        `• Sensors: ${metrics.sensors_online}/${metrics.sensor_count} online\n\n` +
        `Ask about leaks, NRW, DMAs, sensors, or say "help" for options.`,
      suggestions: ['System status', 'Show leaks', 'NRW analysis', 'Help']
    }
  }

  const handleSend = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim()) return

    // Check if this is a voice-initiated send
    const isVoiceTriggered = usedVoiceInput

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    voiceInputRef.current = '' // Clear voice input
    setUsedVoiceInput(false) // Reset voice input flag
    setIsTyping(true)

    const loadingId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: loadingId,
      role: 'assistant',
      content: '✨ Thinking...',
      timestamp: new Date(),
      isLoading: true
    }])

    // Use AI API for response
    const { content, suggestions } = await callAI(messageText)
    
    setMessages(prev => prev.map(m => 
      m.id === loadingId 
        ? { ...m, content, suggestions, isLoading: false }
        : m
    ))
    setIsTyping(false)

    // Auto-speak response if user used voice input
    if (isVoiceTriggered && autoSpeakResponse) {
      // Small delay to let the UI update
      setTimeout(() => {
        speakText(content, loadingId)
      }, 300)
    }
  }

  // Store handleSend in ref for voice callback
  useEffect(() => {
    handleSendRef.current = handleSend
  })

  // Close chat and stop any speech
  const handleClose = () => {
    stopSpeaking()
    setIsOpen(false)
    setIsFullscreen(false)
  }

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  return (
    <>
      {/* Chat Button - Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-4 right-4 sm:bottom-6 sm:right-6 w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full shadow-lg shadow-purple-500/30 flex items-center justify-center text-white hover:scale-110 active:scale-95 transition-all z-50 ${isOpen ? 'hidden' : ''}`}
        aria-label="Open AI Assistant"
      >
        <Sparkles className="w-6 h-6 sm:w-7 sm:h-7" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-2 border-white animate-pulse" />
      </button>

      {/* Chat Window - Fully Responsive */}
      {isOpen && (
        <>
          {/* Backdrop for mobile fullscreen */}
          {isFullscreen && (
            <div 
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={handleClose}
            />
          )}
          
          <div className={`fixed z-50 bg-white shadow-2xl flex flex-col overflow-hidden border border-slate-200 transition-all duration-300 ease-in-out
            ${isFullscreen 
              ? 'inset-2 sm:inset-4 md:inset-6 lg:inset-10 rounded-2xl' 
              : 'bottom-4 right-4 sm:bottom-6 sm:right-6 w-[calc(100vw-2rem)] sm:w-[400px] md:w-[450px] lg:w-[480px] h-[calc(100vh-8rem)] sm:h-[500px] md:h-[600px] lg:h-[650px] max-h-[calc(100vh-2rem)] rounded-2xl'
            }`}
          >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-3 sm:p-4 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className="w-9 h-9 sm:w-10 sm:h-10 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h3 className="font-bold text-sm sm:text-base flex items-center gap-2 truncate">
                  LWSC AI 
                  <span className="text-[10px] sm:text-xs bg-white/20 px-2 py-0.5 rounded-full">GPT</span>
                </h3>
                <div className="flex items-center gap-2 text-[10px] sm:text-xs text-purple-200">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse flex-shrink-0" />
                  <span className="truncate">📍 {currentPageInfo.name}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1 flex-shrink-0">
              {/* Voice Settings Button */}
              <div className="relative">
                <button 
                  onClick={() => setShowVoiceSettings(!showVoiceSettings)}
                  className={`p-2 hover:bg-white/20 rounded-lg transition-colors ${isSpeaking ? 'bg-white/20' : ''}`}
                  title="Voice settings"
                >
                  {isSpeaking ? (
                    <div className="relative">
                      <Volume2 className="w-4 h-4" />
                      <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    </div>
                  ) : (
                    <Mic className="w-4 h-4" />
                  )}
                </button>
                
                {/* Voice Settings Dropdown */}
                {showVoiceSettings && (
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-2xl border border-slate-200 p-4 z-50 text-slate-700">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold text-sm">Voice Settings</h4>
                      <button 
                        onClick={() => setShowVoiceSettings(false)}
                        className="p-1 hover:bg-slate-100 rounded"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    
                    {/* Current Voice */}
                    <div className="mb-3">
                      <label className="text-xs text-slate-500 block mb-1">Voice</label>
                      <select 
                        className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white"
                        value={selectedVoice?.name || ''}
                        onChange={(e) => {
                          const voice = availableVoices.find(v => v.name === e.target.value)
                          if (voice) setSelectedVoice(voice)
                        }}
                      >
                        {availableVoices.filter(v => v.lang.startsWith('en')).map(voice => (
                          <option key={voice.name} value={voice.name}>
                            {voice.name.replace('Microsoft ', '').replace('Google ', '')}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Speed Control */}
                    <div className="mb-3">
                      <label className="text-xs text-slate-500 block mb-1">
                        Speed: {voiceSpeed.toFixed(2)}x
                      </label>
                      <input 
                        type="range"
                        min="0.5"
                        max="1.5"
                        step="0.05"
                        value={voiceSpeed}
                        onChange={(e) => setVoiceSpeed(parseFloat(e.target.value))}
                        className="w-full accent-purple-600"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400">
                        <span>Slow</span>
                        <span>Normal</span>
                        <span>Fast</span>
                      </div>
                    </div>

                    <div className="border-t border-slate-200 pt-3 mb-3">
                      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">Voice Conversation</p>
                    </div>

                    {/* Auto-send voice input toggle */}
                    <div className="mb-3 flex items-center justify-between">
                      <label className="text-xs text-slate-600">Auto-send voice</label>
                      <button
                        onClick={() => setAutoSendVoice(!autoSendVoice)}
                        className={`w-10 h-5 rounded-full transition-colors ${
                          autoSendVoice ? 'bg-purple-600' : 'bg-slate-300'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          autoSendVoice ? 'translate-x-5' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>

                    {/* Auto-speak response toggle */}
                    <div className="mb-3 flex items-center justify-between">
                      <label className="text-xs text-slate-600">AI speaks back</label>
                      <button
                        onClick={() => setAutoSpeakResponse(!autoSpeakResponse)}
                        className={`w-10 h-5 rounded-full transition-colors ${
                          autoSpeakResponse ? 'bg-purple-600' : 'bg-slate-300'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full shadow transition-transform ${
                          autoSpeakResponse ? 'translate-x-5' : 'translate-x-0.5'
                        }`} />
                      </button>
                    </div>
                    
                    {/* Test Voice Button */}
                    <button
                      onClick={() => {
                        const testText = "Hello! I'm your LWSC AI Assistant. How can I help you today?"
                        speakText(testText, 'test')
                      }}
                      className="w-full py-2 px-3 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <Volume2 className="w-4 h-4" />
                      Test Voice
                    </button>
                  </div>
                )}
              </div>
              
              <button 
                onClick={fetchSystemData}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button 
                onClick={toggleFullscreen}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors hidden sm:flex"
                title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button 
                onClick={handleClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Current Page Info Bar */}
          <div className="bg-gradient-to-r from-slate-100 to-slate-50 px-3 sm:px-4 py-2 border-b border-slate-200 flex items-center gap-2 text-xs overflow-x-auto flex-shrink-0">
            <Navigation className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" />
            <span className="text-slate-500 flex-shrink-0">Current:</span>
            <span className="font-medium text-slate-700 truncate">{currentPageInfo.name}</span>
            <span className="text-slate-400 hidden sm:inline">•</span>
            <span className="text-slate-500 text-[10px] hidden sm:inline truncate">{currentPageInfo.features.slice(0, 2).join(', ')}</span>
          </div>

          {/* Data Indicators */}
          {systemData && systemData.metrics && (
            <div className="bg-slate-50 px-3 sm:px-4 py-2 border-b border-slate-200 flex items-center gap-3 sm:gap-4 text-[10px] sm:text-xs overflow-x-auto flex-shrink-0">
              <div className="flex items-center gap-1 flex-shrink-0">
                <Activity className="w-3 h-3 text-emerald-500" />
                <span className="text-slate-600">NRW: <strong className={(systemData.metrics.total_nrw_percent ?? 0) > 35 ? 'text-red-600' : 'text-emerald-600'}>{systemData.metrics.total_nrw_percent ?? 0}%</strong></span>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <Droplets className="w-3 h-3 text-blue-500" />
                <span className="text-slate-600">Loss: <strong>{systemData.metrics.total_losses ?? 0}</strong></span>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                <AlertTriangle className="w-3 h-3 text-amber-500" />
                <span className="text-slate-600">Alerts: <strong>{systemData.dmas?.filter((d: any) => d.status === 'critical').length ?? 0}</strong></span>
              </div>
              <div className="hidden md:flex items-center gap-1 flex-shrink-0">
                <Map className="w-3 h-3 text-purple-500" />
                <span className="text-slate-600">Pages: <strong>{Object.keys(SYSTEM_PAGES).length}</strong></span>
              </div>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 bg-slate-50">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[92%] sm:max-w-[85%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`flex items-end gap-2 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gradient-to-br from-purple-500 to-blue-500 text-white'
                    }`}>
                      {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={`px-3 py-2.5 sm:px-4 sm:py-3 rounded-2xl ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-br-md' 
                        : 'bg-white shadow-sm border border-slate-200 rounded-bl-md'
                    }`}>
                      {message.isLoading ? (
                        <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-500">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Thinking...
                        </div>
                      ) : (
                        <>
                          <div className={`text-xs sm:text-sm whitespace-pre-wrap leading-relaxed ${message.role === 'user' ? '' : 'text-slate-700'}`}>
                            {message.content.split('\n').map((line, i) => {
                              const parts = line.split(/(\*\*.*?\*\*)/g)
                              return (
                                <p key={i} className={i > 0 ? 'mt-1' : ''}>
                                  {parts.map((part, j) => {
                                    if (part.startsWith('**') && part.endsWith('**')) {
                                      return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>
                                    }
                                    return part
                                  })}
                                </p>
                              )
                            })}
                          </div>
                          {/* Read Aloud Button for assistant messages */}
                          {message.role === 'assistant' && (
                            <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-2 flex-wrap">
                              <button
                                onClick={() => {
                                  if (isSpeaking && speakingMessageId === message.id) {
                                    stopSpeaking()
                                  } else {
                                    speakText(message.content, message.id)
                                  }
                                }}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] sm:text-xs font-medium transition-all ${
                                  isSpeaking && speakingMessageId === message.id
                                    ? 'bg-gradient-to-r from-red-500 to-pink-500 text-white shadow-lg shadow-red-200'
                                    : 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg shadow-purple-200 hover:shadow-purple-300'
                                }`}
                                title={isSpeaking && speakingMessageId === message.id ? 'Stop speaking' : 'Read aloud'}
                              >
                                {isSpeaking && speakingMessageId === message.id ? (
                                  <>
                                    <Square className="w-3 h-3" />
                                    <span>Stop</span>
                                    {/* Audio wave animation */}
                                    <div className="flex items-center gap-0.5 ml-1">
                                      <span className="w-0.5 h-2 bg-white rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                                      <span className="w-0.5 h-3 bg-white rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                                      <span className="w-0.5 h-2 bg-white rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                                      <span className="w-0.5 h-4 bg-white rounded-full animate-pulse" style={{ animationDelay: '450ms' }} />
                                      <span className="w-0.5 h-2 bg-white rounded-full animate-pulse" style={{ animationDelay: '600ms' }} />
                                    </div>
                                  </>
                                ) : (
                                  <>
                                    <Volume2 className="w-3.5 h-3.5" />
                                    <span>🔊 Listen</span>
                                  </>
                                )}
                              </button>
                              {/* Voice info */}
                              {selectedVoice && (
                                <span className="text-[9px] text-slate-400 hidden sm:inline">
                                  Voice: {selectedVoice.name.replace('Microsoft ', '').replace('Google ', '').split(' ').slice(0, 2).join(' ')}
                                </span>
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  
                  {message.role === 'assistant' && message.suggestions && !message.isLoading && (
                    <div className="mt-1.5 sm:mt-2 ml-7 sm:ml-9 flex flex-wrap gap-1">
                      {message.suggestions.slice(0, 4).map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(suggestion)}
                          className="px-2.5 py-1 sm:px-3 sm:py-1.5 bg-white border border-slate-200 rounded-full text-[10px] sm:text-xs text-slate-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-3 sm:p-4 border-t border-slate-200 bg-white flex-shrink-0">
            {/* Voice Status Indicator */}
            {isListening && (
              <div className="mb-3 p-3 bg-gradient-to-r from-red-50 to-pink-50 rounded-xl border border-red-200 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 bg-red-500 rounded-full flex items-center justify-center">
                      <Mic className="w-5 h-5 text-white" />
                    </div>
                    {/* Pulsing rings */}
                    <div className="absolute inset-0 w-10 h-10 bg-red-400 rounded-full animate-ping opacity-30" />
                    <div className="absolute -inset-1 w-12 h-12 border-2 border-red-300 rounded-full animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-700">🎤 Listening...</p>
                    <p className="text-xs text-red-500">
                      {interimTranscript || 'Speak now...'}
                    </p>
                  </div>
                  <button
                    onClick={toggleListening}
                    className="p-2 bg-red-100 hover:bg-red-200 rounded-lg transition-colors"
                  >
                    <Square className="w-4 h-4 text-red-600" />
                  </button>
                </div>
              </div>
            )}

            {/* AI Speaking Indicator */}
            {isSpeaking && !isListening && (
              <div className="mb-3 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-200">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                      <Volume2 className="w-5 h-5 text-white" />
                    </div>
                    {/* Audio wave animation */}
                    <div className="absolute -right-1 top-1/2 -translate-y-1/2 flex items-center gap-0.5">
                      <span className="w-0.5 h-3 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                      <span className="w-0.5 h-4 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
                      <span className="w-0.5 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-purple-700">🔊 AI Speaking...</p>
                    <p className="text-xs text-purple-500">
                      {selectedVoice ? selectedVoice.name.replace('Microsoft ', '').split(' ').slice(0, 2).join(' ') : 'System voice'}
                    </p>
                  </div>
                  <button
                    onClick={stopSpeaking}
                    className="p-2 bg-purple-100 hover:bg-purple-200 rounded-lg transition-colors"
                  >
                    <Square className="w-4 h-4 text-purple-600" />
                  </button>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              {/* Voice Input Button */}
              <button
                onClick={toggleListening}
                disabled={isTyping}
                className={`w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition-all ${
                  isListening
                    ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-300'
                    : 'bg-slate-100 text-slate-600 hover:bg-purple-100 hover:text-purple-600'
                } disabled:opacity-50`}
                title={isListening ? 'Stop listening' : 'Voice input'}
              >
                {isListening ? (
                  <div className="relative">
                    <Mic className="w-5 h-5" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>

              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !isTyping && handleSend()}
                placeholder={isListening ? "Listening..." : "Ask me anything about the system..."}
                disabled={isTyping}
                className="flex-1 px-4 py-2.5 sm:py-3 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/30 focus:bg-white transition-colors disabled:opacity-50"
              />
              <button 
                onClick={() => handleSend()}
                disabled={!input.trim() || isTyping}
                className="w-10 h-10 sm:w-11 sm:h-11 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl flex items-center justify-center text-white hover:opacity-90 active:scale-95 transition-all disabled:opacity-50"
              >
                {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
            
            {/* Quick Actions */}
            <div className="mt-2 flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-[10px] text-slate-400 flex-shrink-0">Quick:</span>
              <button 
                onClick={() => handleSend("What can I do on this page?")}
                className="px-2.5 py-1 text-[10px] sm:text-xs bg-purple-50 text-purple-600 rounded-full whitespace-nowrap hover:bg-purple-100 transition-colors"
              >
                📍 This page
              </button>
              <button 
                onClick={() => handleSend("Show me all available pages")}
                className="px-2.5 py-1 text-[10px] sm:text-xs bg-blue-50 text-blue-600 rounded-full whitespace-nowrap hover:bg-blue-100 transition-colors"
              >
                🗺️ All pages
              </button>
              <button 
                onClick={() => handleSend("System status")}
                className="px-2.5 py-1 text-[10px] sm:text-xs bg-emerald-50 text-emerald-600 rounded-full whitespace-nowrap hover:bg-emerald-100 transition-colors"
              >
                📊 Status
              </button>
              <button 
                onClick={() => handleSend("Help me navigate")}
                className="px-2.5 py-1 text-[10px] sm:text-xs bg-amber-50 text-amber-600 rounded-full whitespace-nowrap hover:bg-amber-100 transition-colors"
              >
                🧭 Navigate
              </button>
            </div>

            {/* Voice input hint */}
            <div className="mt-2 text-center">
              <p className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                💡 Click <span className="inline-flex items-center justify-center w-5 h-5 bg-slate-200 rounded"><Mic className="w-3 h-3" /></span> to speak • Auto-sends when done
              </p>
            </div>
          </div>
        </div>
        </>
      )}
    </>
  )
}
