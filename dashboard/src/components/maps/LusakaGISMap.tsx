'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'

// Real GPS coordinates for Lusaka DMAs/Areas
export const LUSAKA_DMAS = [
  { id: 'dma-001', name: 'Kabulonga', lat: -15.4192, lng: 28.3225, area: 'Residential High-Income' },
  { id: 'dma-002', name: 'Woodlands', lat: -15.4134, lng: 28.3064, area: 'Residential Mixed' },
  { id: 'dma-003', name: 'Roma', lat: -15.3958, lng: 28.3108, area: 'Residential Mid-Income' },
  { id: 'dma-004', name: 'Chelstone', lat: -15.3605, lng: 28.3517, area: 'Residential Large' },
  { id: 'dma-005', name: 'Chilenje', lat: -15.4433, lng: 28.2925, area: 'Residential Dense' },
  { id: 'dma-006', name: 'Matero', lat: -15.3747, lng: 28.2633, area: 'Residential High-Density' },
  { id: 'dma-007', name: 'Kalingalinga', lat: -15.4028, lng: 28.3350, area: 'Compound Urban' },
  { id: 'dma-008', name: 'Olympia Park', lat: -15.4089, lng: 28.2953, area: 'Residential Premium' },
  { id: 'dma-009', name: 'Kabwata', lat: -15.4311, lng: 28.2878, area: 'Residential Historic' },
  { id: 'dma-010', name: 'Town Centre', lat: -15.4162, lng: 28.2831, area: 'Commercial CBD' },
  { id: 'dma-011', name: 'Emmasdale', lat: -15.4422, lng: 28.2756, area: 'Residential Mixed' },
  { id: 'dma-012', name: 'Libala', lat: -15.4367, lng: 28.3156, area: 'Residential Mid-Income' },
  { id: 'dma-013', name: 'Garden', lat: -15.3944, lng: 28.2867, area: 'Commercial Light' },
  { id: 'dma-014', name: 'Rhodes Park', lat: -15.4092, lng: 28.2961, area: 'Residential Premium' },
  { id: 'dma-015', name: 'Munali', lat: -15.4428, lng: 28.3397, area: 'Residential Suburban' },
  { id: 'dma-016', name: 'Mtendere', lat: -15.4019, lng: 28.3611, area: 'Compound Dense' },
  { id: 'dma-017', name: 'PHI', lat: -15.4256, lng: 28.3311, area: 'Residential Mid-Income' },
  { id: 'dma-018', name: 'Avondale', lat: -15.4156, lng: 28.3047, area: 'Residential Established' },
]

// Simulated leak locations - these would come from real sensors/AI detection
export interface LeakLocation {
  id: string
  dma_id: string
  lat: number
  lng: number
  severity: 'critical' | 'major' | 'minor'
  type: 'pipe_burst' | 'joint_leak' | 'valve_leak' | 'service_connection'
  estimated_loss: number // liters per hour
  detected_at: string
  address: string
  confidence: number // AI confidence 0-100
}

// Generate realistic leak locations near DMAs
export const generateLeakLocations = (): LeakLocation[] => {
  const leaks: LeakLocation[] = [
    // Critical leaks - pipe bursts
    {
      id: 'leak-001',
      dma_id: 'dma-006',
      lat: -15.3762,
      lng: 28.2658,
      severity: 'critical',
      type: 'pipe_burst',
      estimated_loss: 2500,
      detected_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      address: 'Matero Main Rd, near Market',
      confidence: 94
    },
    {
      id: 'leak-002',
      dma_id: 'dma-005',
      lat: -15.4455,
      lng: 28.2948,
      severity: 'critical',
      type: 'pipe_burst',
      estimated_loss: 1800,
      detected_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      address: 'Chilenje South, Block 12',
      confidence: 91
    },
    // Major leaks
    {
      id: 'leak-003',
      dma_id: 'dma-007',
      lat: -15.4045,
      lng: 28.3372,
      severity: 'major',
      type: 'joint_leak',
      estimated_loss: 850,
      detected_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      address: 'Kalingalinga Main Junction',
      confidence: 87
    },
    {
      id: 'leak-004',
      dma_id: 'dma-016',
      lat: -15.4035,
      lng: 28.3628,
      severity: 'major',
      type: 'valve_leak',
      estimated_loss: 650,
      detected_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      address: 'Mtendere East, Section C',
      confidence: 82
    },
    {
      id: 'leak-005',
      dma_id: 'dma-004',
      lat: -15.3622,
      lng: 28.3538,
      severity: 'major',
      type: 'service_connection',
      estimated_loss: 420,
      detected_at: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(),
      address: 'Chelstone Extension, Plot 45',
      confidence: 79
    },
    // Minor leaks
    {
      id: 'leak-006',
      dma_id: 'dma-001',
      lat: -15.4208,
      lng: 28.3242,
      severity: 'minor',
      type: 'service_connection',
      estimated_loss: 180,
      detected_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      address: 'Kabulonga Rd, House 23',
      confidence: 76
    },
    {
      id: 'leak-007',
      dma_id: 'dma-012',
      lat: -15.4382,
      lng: 28.3178,
      severity: 'minor',
      type: 'joint_leak',
      estimated_loss: 220,
      detected_at: new Date(Date.now() - 36 * 60 * 60 * 1000).toISOString(),
      address: 'Libala South, Stage 2',
      confidence: 73
    },
    {
      id: 'leak-008',
      dma_id: 'dma-009',
      lat: -15.4328,
      lng: 28.2895,
      severity: 'minor',
      type: 'valve_leak',
      estimated_loss: 150,
      detected_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      address: 'Kabwata Site & Service',
      confidence: 71
    },
  ]
  return leaks
}

// Lusaka city center coordinates
export const LUSAKA_CENTER = {
  lat: -15.4067,
  lng: 28.2872,
  zoom: 12
}

interface DMAMapData {
  dma_id: string
  name: string
  nrw_percent: number
  priority_score: number
  status: 'critical' | 'warning' | 'healthy'
  trend: 'up' | 'down' | 'stable'
  input_flow?: number
  output_flow?: number
}

interface LusakaGISMapProps {
  dmas: DMAMapData[]
  leaks?: LeakLocation[]
  showLeaks?: boolean
  onDMAClick?: (dmaId: string) => void
  onLeakClick?: (leakId: string) => void
  selectedDMA?: string | null
}

// Create the map component that will only render on client
function MapComponent({ dmas, leaks, showLeaks = true, onDMAClick, onLeakClick, selectedDMA }: LusakaGISMapProps) {
  const [L, setL] = useState<any>(null)
  const [MapContainer, setMapContainer] = useState<any>(null)
  const [TileLayer, setTileLayer] = useState<any>(null)
  const [Marker, setMarker] = useState<any>(null)
  const [Popup, setPopup] = useState<any>(null)
  const [Circle, setCircle] = useState<any>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  
  // Use provided leaks or generate default ones
  const activeLeaks = leaks || generateLeakLocations()

  useEffect(() => {
    // Dynamically import Leaflet on client side only
    Promise.all([
      import('leaflet'),
      import('react-leaflet')
    ]).then(([leaflet, reactLeaflet]) => {
      setL(leaflet.default)
      setMapContainer(() => reactLeaflet.MapContainer)
      setTileLayer(() => reactLeaflet.TileLayer)
      setMarker(() => reactLeaflet.Marker)
      setPopup(() => reactLeaflet.Popup)
      setCircle(() => reactLeaflet.Circle)
      setIsLoaded(true)
    })
  }, [])

  if (!isLoaded || !L || !MapContainer) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-600">Loading Map...</p>
        </div>
      </div>
    )
  }

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical': return '#ef4444' // red
      case 'warning': return '#f59e0b' // amber
      case 'healthy': return '#10b981' // green
      default: return '#6b7280' // gray
    }
  }

  // Custom icon creator
  const createIcon = (status: string) => {
    const color = getStatusColor(status)
    return L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          width: 28px; 
          height: 28px; 
          background: ${color}; 
          border-radius: 50%; 
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
          </svg>
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 28],
      popupAnchor: [0, -28]
    })
  }
  
  // Leak icon creator with pulsing animation
  const createLeakIcon = (severity: 'critical' | 'major' | 'minor') => {
    const colors = {
      critical: { bg: '#dc2626', pulse: '#ef4444' },
      major: { bg: '#ea580c', pulse: '#f97316' },
      minor: { bg: '#ca8a04', pulse: '#eab308' }
    }
    const { bg, pulse } = colors[severity]
    const size = severity === 'critical' ? 24 : severity === 'major' ? 20 : 16
    
    return L.divIcon({
      className: 'leak-marker',
      html: `
        <div style="position: relative; width: ${size}px; height: ${size}px;">
          <div style="
            position: absolute;
            width: ${size}px; 
            height: ${size}px; 
            background: ${bg}; 
            border-radius: 50%; 
            border: 2px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2;
          ">
            <svg width="${size * 0.5}" height="${size * 0.5}" viewBox="0 0 24 24" fill="white">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
            </svg>
          </div>
          <div style="
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: ${size * 2}px;
            height: ${size * 2}px;
            background: ${pulse};
            border-radius: 50%;
            opacity: 0.4;
            animation: pulse-leak 1.5s ease-out infinite;
            z-index: 1;
          "></div>
        </div>
        <style>
          @keyframes pulse-leak {
            0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0.6; }
            100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
          }
        </style>
      `,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -size / 2]
    })
  }

  // Match DMAs from props with location data
  const dmasWithLocations = dmas.map(dma => {
    const location = LUSAKA_DMAS.find(loc => 
      loc.name.toLowerCase() === dma.name.toLowerCase() ||
      loc.id === dma.dma_id
    )
    return { ...dma, location }
  }).filter(d => d.location)

  return (
    <MapContainer
      center={[LUSAKA_CENTER.lat, LUSAKA_CENTER.lng]}
      zoom={LUSAKA_CENTER.zoom}
      style={{ height: '100%', width: '100%' }}
      className="rounded-lg z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* DMA Markers with Circles */}
      {dmasWithLocations.map((dma) => {
        if (!dma.location) return null
        const isSelected = selectedDMA === dma.dma_id
        const color = getStatusColor(dma.status)
        
        return (
          <div key={dma.dma_id}>
            {/* Coverage Circle */}
            <Circle
              center={[dma.location.lat, dma.location.lng]}
              radius={800}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: isSelected ? 0.3 : 0.15,
                weight: isSelected ? 3 : 1
              }}
            />
            
            {/* DMA Marker */}
            <Marker
              position={[dma.location.lat, dma.location.lng]}
              icon={createIcon(dma.status)}
              eventHandlers={{
                click: () => onDMAClick?.(dma.dma_id)
              }}
            >
              <Popup>
                <div className="p-1 min-w-[200px]">
                  <h3 className="font-bold text-gray-900 text-base mb-1">{dma.name}</h3>
                  <p className="text-xs text-gray-500 mb-2">{dma.location?.area}</p>
                  
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="text-xs text-gray-500">NRW Rate</p>
                      <p className="font-bold text-lg" style={{ color: color }}>
                        {dma.nrw_percent.toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-gray-50 p-2 rounded">
                      <p className="text-xs text-gray-500">Priority</p>
                      <p className="font-bold text-lg text-gray-900">
                        {dma.priority_score}
                      </p>
                    </div>
                  </div>
                  
                  {dma.input_flow && (
                    <div className="text-xs text-gray-600 border-t pt-2">
                      <p>Input Flow: <span className="font-medium">{dma.input_flow.toFixed(0)} m³/h</span></p>
                    </div>
                  )}
                  
                  <div className="mt-2 pt-2 border-t">
                    <span 
                      className="inline-block px-2 py-0.5 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: color }}
                    >
                      {dma.status.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      Trend: {dma.trend === 'up' ? '↑' : dma.trend === 'down' ? '↓' : '→'}
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          </div>
        )
      })}
      
      {/* Leak Markers with Pulsing Animation */}
      {showLeaks && activeLeaks.map((leak) => {
        const dmaInfo = LUSAKA_DMAS.find(d => d.id === leak.dma_id)
        const timeAgo = Math.floor((Date.now() - new Date(leak.detected_at).getTime()) / (1000 * 60 * 60))
        
        return (
          <Marker
            key={leak.id}
            position={[leak.lat, leak.lng]}
            icon={createLeakIcon(leak.severity)}
            eventHandlers={{
              click: () => onLeakClick?.(leak.id)
            }}
          >
            <Popup>
              <div className="p-1 min-w-[220px]">
                <div className="flex items-center gap-2 mb-2">
                  <span 
                    className="inline-block px-2 py-0.5 rounded-full text-xs font-bold text-white uppercase"
                    style={{ 
                      backgroundColor: leak.severity === 'critical' ? '#dc2626' : 
                                       leak.severity === 'major' ? '#ea580c' : '#ca8a04' 
                    }}
                  >
                    {leak.severity} Leak
                  </span>
                  <span className="text-xs text-gray-500">{timeAgo}h ago</span>
                </div>
                
                <h3 className="font-bold text-gray-900 text-sm mb-1">
                  {leak.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                <p className="text-xs text-gray-600 mb-2">📍 {leak.address}</p>
                
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <div className="bg-red-50 p-2 rounded">
                    <p className="text-xs text-gray-500">Water Loss</p>
                    <p className="font-bold text-red-600 text-sm">
                      {leak.estimated_loss.toLocaleString()} L/hr
                    </p>
                  </div>
                  <div className="bg-blue-50 p-2 rounded">
                    <p className="text-xs text-gray-500">AI Confidence</p>
                    <p className="font-bold text-blue-600 text-sm">
                      {leak.confidence}%
                    </p>
                  </div>
                </div>
                
                {dmaInfo && (
                  <p className="text-xs text-gray-500 border-t pt-2">
                    DMA: <span className="font-medium">{dmaInfo.name}</span>
                  </p>
                )}
                
                <button 
                  className="w-full mt-2 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition-colors"
                  onClick={() => onLeakClick?.(leak.id)}
                >
                  View Details & Dispatch Team
                </button>
              </div>
            </Popup>
          </Marker>
        )
      })}
      
      {/* LWSC HQ Marker */}
      <Marker
        position={[LUSAKA_CENTER.lat, LUSAKA_CENTER.lng]}
        icon={L.divIcon({
          className: 'hq-marker',
          html: `
            <div style="
              width: 36px; 
              height: 36px; 
              background: linear-gradient(135deg, #2563eb, #1d4ed8); 
              border-radius: 8px; 
              border: 3px solid white;
              box-shadow: 0 2px 8px rgba(0,0,0,0.4);
              display: flex;
              align-items: center;
              justify-content: center;
            ">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
              </svg>
            </div>
          `,
          iconSize: [36, 36],
          iconAnchor: [18, 36],
          popupAnchor: [0, -36]
        })}
      >
        <Popup>
          <div className="p-1 text-center">
            <h3 className="font-bold text-blue-800">LWSC Headquarters</h3>
            <p className="text-xs text-gray-500">Lusaka Water & Sewerage Company</p>
            <p className="text-xs text-gray-500 mt-1">Cairo Road, Lusaka</p>
          </div>
        </Popup>
      </Marker>
    </MapContainer>
  )
}

// Export with dynamic import to avoid SSR issues
export default function LusakaGISMap(props: LusakaGISMapProps) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])
  
  if (!mounted) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-slate-100">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-600">Initializing GIS Map...</p>
        </div>
      </div>
    )
  }
  
  return <MapComponent {...props} />
}
