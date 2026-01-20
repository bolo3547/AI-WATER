'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

// Supported languages
export const languages = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇬🇧'
  },
  ny: {
    code: 'ny',
    name: 'Chichewa/Nyanja',
    nativeName: 'Chinyanja',
    flag: '🇿🇲'
  },
  bem: {
    code: 'bem',
    name: 'Bemba',
    nativeName: 'Ichibemba',
    flag: '🇿🇲'
  },
  toi: {
    code: 'toi',
    name: 'Tonga',
    nativeName: 'Chitonga',
    flag: '🇿🇲'
  },
  loz: {
    code: 'loz',
    name: 'Lozi',
    nativeName: 'Silozi',
    flag: '🇿🇲'
  }
}

// Translations
export const translations: Record<string, Record<string, string>> = {
  en: {
    // Common
    'app.name': 'LWSC NRW Detection System',
    'app.subtitle': 'Lusaka Water Supply & Sanitation Company',
    'republic': 'Republic of Zambia',
    'dashboard': 'Dashboard',
    'analytics': 'Analytics',
    'alerts': 'Alerts',
    'reports': 'Reports',
    'map': 'Map',
    'settings': 'Settings',
    'logout': 'Logout',
    'login': 'Login',
    'welcome': 'Welcome',
    'loading': 'Loading...',
    'save': 'Save',
    'cancel': 'Cancel',
    'delete': 'Delete',
    'edit': 'Edit',
    'view': 'View',
    'close': 'Close',
    'search': 'Search',
    'filter': 'Filter',
    'export': 'Export',
    'download': 'Download',
    
    // Dashboard
    'dashboard.title': 'NRW Dashboard',
    'dashboard.overview': 'System Overview',
    'dashboard.nrw_rate': 'NRW Rate',
    'dashboard.water_loss': 'Water Loss',
    'dashboard.active_leaks': 'Active Leaks',
    'dashboard.sensors_online': 'Sensors Online',
    'dashboard.revenue_lost': 'Revenue Lost',
    'dashboard.revenue_recovered': 'Revenue Recovered',
    'dashboard.response_time': 'Avg Response Time',
    'dashboard.today': 'Today',
    'dashboard.this_week': 'This Week',
    'dashboard.this_month': 'This Month',
    
    // Alerts
    'alerts.title': 'System Alerts',
    'alerts.critical': 'Critical',
    'alerts.warning': 'Warning',
    'alerts.info': 'Information',
    'alerts.new_leak': 'New Leak Detected',
    'alerts.pressure_drop': 'Pressure Drop Detected',
    'alerts.sensor_offline': 'Sensor Offline',
    'alerts.high_nrw': 'High NRW Rate Alert',
    'alerts.acknowledge': 'Acknowledge',
    'alerts.resolve': 'Resolve',
    
    // Leaks
    'leaks.title': 'Leak Management',
    'leaks.detected': 'Detected',
    'leaks.assigned': 'Assigned',
    'leaks.in_progress': 'In Progress',
    'leaks.repaired': 'Repaired',
    'leaks.severity': 'Severity',
    'leaks.location': 'Location',
    'leaks.flow_rate': 'Flow Rate',
    'leaks.assign_crew': 'Assign Crew',
    'leaks.mark_repaired': 'Mark as Repaired',
    
    // Reports
    'reports.title': 'Reports',
    'reports.generate': 'Generate Report',
    'reports.executive_summary': 'Executive Summary',
    'reports.nrw_analysis': 'NRW Analysis',
    'reports.financial_impact': 'Financial Impact',
    'reports.date_range': 'Date Range',
    
    // Map
    'map.title': 'Network Map',
    'map.dma_zones': 'DMA Zones',
    'map.leak_locations': 'Leak Locations',
    'map.sensors': 'Sensors',
    'map.pipes': 'Pipelines',
    
    // Settings
    'settings.title': 'Settings',
    'settings.language': 'Language',
    'settings.notifications': 'Notifications',
    'settings.theme': 'Theme',
    'settings.account': 'Account',
    'settings.security': 'Security',
    
    // Units
    'unit.cubic_meters': 'm³',
    'unit.liters_per_minute': 'L/min',
    'unit.percent': '%',
    'unit.hours': 'hours',
    'unit.days': 'days',
    'unit.zmw': 'ZMW',
  },
  
  ny: {
    // Chinyanja/Chichewa translations
    'app.name': 'LWSC Njira Yopezera Madzi Otayika',
    'app.subtitle': 'Kampani ya Madzi ndi Zaukhondo ku Lusaka',
    'republic': 'Dziko la Zambia',
    'dashboard': 'Tsamba Lalikulu',
    'analytics': 'Kuunika',
    'alerts': 'Zichenjezere',
    'reports': 'Malipoti',
    'map': 'Mapu',
    'settings': 'Zosintha',
    'logout': 'Tulukani',
    'login': 'Lowani',
    'welcome': 'Takulandirani',
    'loading': 'Kukonza...',
    'save': 'Sungani',
    'cancel': 'Lekani',
    'delete': 'Chotsani',
    'edit': 'Sinthani',
    'view': 'Onani',
    'close': 'Tsekani',
    'search': 'Funani',
    'filter': 'Sankhani',
    'export': 'Tulutsani',
    'download': 'Landitsani',
    
    'dashboard.title': 'Tsamba la NRW',
    'dashboard.overview': 'Chionetsero cha System',
    'dashboard.nrw_rate': 'Chiwerengero cha NRW',
    'dashboard.water_loss': 'Madzi Otayika',
    'dashboard.active_leaks': 'Kutayika Kwachitika',
    'dashboard.sensors_online': 'Ma Sensor Ogwira Ntchito',
    'dashboard.revenue_lost': 'Ndalama Zotayika',
    'dashboard.revenue_recovered': 'Ndalama Zobwezeretsedwa',
    'dashboard.response_time': 'Nthawi Yoyankha',
    'dashboard.today': 'Lero',
    'dashboard.this_week': 'Sabata Ino',
    'dashboard.this_month': 'Mwezi Uno',
    
    'alerts.title': 'Zichenjezere za System',
    'alerts.critical': 'Choopsa',
    'alerts.warning': 'Chenjezani',
    'alerts.info': 'Uthenga',
    'alerts.new_leak': 'Kutayika Kwatsopano Kwapezeka',
    'alerts.acknowledge': 'Vomerezani',
    'alerts.resolve': 'Konzani',
    
    'leaks.title': 'Kuyang\'anira Kutayika',
    'leaks.detected': 'Zapezeka',
    'leaks.repaired': 'Zakonzedwa',
    'leaks.severity': 'Kuopsa Kwake',
    'leaks.location': 'Malo',
    'leaks.assign_crew': 'Patulani Gulu',
    
    'reports.title': 'Malipoti',
    'reports.generate': 'Pangani Lipoti',
    
    'settings.title': 'Zosintha',
    'settings.language': 'Chilankhulo',
    
    'unit.cubic_meters': 'm³',
    'unit.percent': '%',
  },
  
  bem: {
    // Ichibemba translations
    'app.name': 'LWSC Inshila ya Kusanga Amenshi ya Kubulwa',
    'app.subtitle': 'Kampani ya Menshi na Ubuumi ku Lusaka',
    'republic': 'Icalo ca Zambia',
    'dashboard': 'Cibali Ciikalamba',
    'analytics': 'Ukusefya',
    'alerts': 'Ifitenteko',
    'reports': 'Imbila',
    'map': 'Imapu',
    'settings': 'Ukwalula',
    'logout': 'Fumaleni',
    'login': 'Ingila',
    'welcome': 'Mwaiseni',
    'loading': 'Nakuloada...',
    'save': 'Sungeni',
    'cancel': 'Lekeni',
    
    'dashboard.title': 'Cibali ca NRW',
    'dashboard.nrw_rate': 'Inshila ya NRW',
    'dashboard.water_loss': 'Amenshi ya Kubulwa',
    'dashboard.active_leaks': 'Ukubulwa Ukucitika',
    
    'alerts.title': 'Ifitenteko fya System',
    'alerts.critical': 'Ukuopsa',
    
    'settings.language': 'Ululimi',
  },
  
  toi: {
    // Chitonga translations
    'app.name': 'LWSC Nzila yakujana Maanzi Aakuba',
    'app.subtitle': 'Kampani ya Maanzi aLusaka',
    'republic': 'Cisi ca Zambia',
    'dashboard': 'Pepa Lipati',
    'welcome': 'Mwalandiwa',
    'settings.language': 'Mwaambo',
  },
  
  loz: {
    // Silozi translations
    'app.name': 'LWSC Nzila ya Kufumana Mezi a Lateha',
    'app.subtitle': 'Kampani ya Mezi ni Buiketo kwa Lusaka',
    'republic': 'Naha ya Zambia',
    'dashboard': 'Likepe Lelituna',
    'welcome': 'Muamuhezwi',
    'settings.language': 'Puo',
  },
}

// Language Context
type LanguageContextType = {
  language: string
  setLanguage: (lang: string) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState('en')

  const t = (key: string): string => {
    return translations[language]?.[key] || translations['en']?.[key] || key
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

// Language Selector Component
export function LanguageSelector({ variant = 'default' }: { variant?: 'default' | 'minimal' }) {
  const { language, setLanguage } = useLanguage()
  const [isOpen, setIsOpen] = useState(false)

  const currentLang = languages[language as keyof typeof languages]

  if (variant === 'minimal') {
    return (
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 px-2 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <span>{currentLang.flag}</span>
          <span className="hidden sm:inline">{currentLang.code.toUpperCase()}</span>
        </button>
        
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-xl shadow-lg border border-slate-100 py-1 z-50">
              {Object.values(languages).map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => { setLanguage(lang.code); setIsOpen(false); }}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-slate-50 transition-colors ${
                    language === lang.code ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
                  }`}
                >
                  <span className="text-lg">{lang.flag}</span>
                  <div className="text-left">
                    <p className="font-medium">{lang.name}</p>
                    <p className="text-[10px] text-slate-400">{lang.nativeName}</p>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-700">Language / Chilankhulo</label>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {Object.values(languages).map((lang) => (
          <button
            key={lang.code}
            onClick={() => setLanguage(lang.code)}
            className={`flex items-center gap-2 p-3 rounded-xl border-2 transition-all ${
              language === lang.code
                ? 'border-blue-500 bg-blue-50'
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            <span className="text-xl">{lang.flag}</span>
            <div className="text-left">
              <p className="text-sm font-medium text-slate-900">{lang.name}</p>
              <p className="text-[10px] text-slate-500">{lang.nativeName}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
