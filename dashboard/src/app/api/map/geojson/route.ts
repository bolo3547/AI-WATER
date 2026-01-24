import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

/**
 * MAP GEOJSON API ROUTE
 * =====================
 * 
 * Proxies requests to the FastAPI backend or generates sample data
 * for development. Returns GeoJSON for sensors, leaks, and DMAs.
 * 
 * GET /api/map/geojson?tenant={tenantId}&include_layers=dmas,sensors,leaks
 */

// =============================================================================
// TYPES
// =============================================================================

interface GeoJSONFeature {
  type: 'Feature'
  id?: string
  geometry: {
    type: 'Point' | 'Polygon'
    coordinates: number[] | number[][] | number[][][]
  }
  properties: Record<string, any>
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
  metadata?: Record<string, any>
}

// =============================================================================
// SAMPLE DATA GENERATOR
// =============================================================================

// Lusaka center coordinates
const CENTER_LAT = -15.4167
const CENTER_LNG = 28.2833

// DMA definitions
const DMA_DEFINITIONS = [
  { id: 'dma-woodlands', name: 'Woodlands', center: [-15.385, 28.310], radius: 1.8, nrw: 18.5, pop: 45000, conn: 8500 },
  { id: 'dma-kabulonga', name: 'Kabulonga', center: [-15.408, 28.332], radius: 1.5, nrw: 21.2, pop: 38000, conn: 7200 },
  { id: 'dma-roma', name: 'Roma', center: [-15.422, 28.298], radius: 1.2, nrw: 23.1, pop: 28000, conn: 5500 },
  { id: 'dma-matero', name: 'Matero', center: [-15.362, 28.278], radius: 2.0, nrw: 48.2, pop: 85000, conn: 12000 },
  { id: 'dma-chilenje', name: 'Chilenje', center: [-15.445, 28.268], radius: 1.6, nrw: 45.8, pop: 62000, conn: 9800 },
  { id: 'dma-garden', name: 'Garden', center: [-15.398, 28.285], radius: 1.0, nrw: 42.1, pop: 22000, conn: 4200 },
  { id: 'dma-rhodes-park', name: 'Rhodes Park', center: [-15.412, 28.305], radius: 0.9, nrw: 28.5, pop: 18000, conn: 3500 },
  { id: 'dma-olympia', name: 'Olympia', center: [-15.438, 28.312], radius: 1.1, nrw: 35.2, pop: 25000, conn: 4800 },
  { id: 'dma-kabwata', name: 'Kabwata', center: [-15.455, 28.285], radius: 1.4, nrw: 39.8, pop: 48000, conn: 7500 },
  { id: 'dma-mtendere', name: 'Mtendere', center: [-15.448, 28.342], radius: 1.7, nrw: 52.3, pop: 72000, conn: 10500 },
  { id: 'dma-kalingalinga', name: 'Kalingalinga', center: [-15.432, 28.355], radius: 1.3, nrw: 55.1, pop: 58000, conn: 8200 },
  { id: 'dma-chelstone', name: 'Chelstone', center: [-15.395, 28.365], radius: 2.2, nrw: 41.5, pop: 95000, conn: 14000 },
]

function generatePolygon(center: number[], radiusKm: number, points = 8): number[][] {
  const [lat, lng] = center
  const latDegree = radiusKm / 111.0
  const lngDegree = radiusKm / (111.0 * Math.cos(lat * Math.PI / 180))
  
  const coords: number[][] = []
  for (let i = 0; i < points; i++) {
    const angle = (2 * Math.PI * i) / points
    const rFactor = 1 + (Math.random() - 0.5) * 0.5
    
    const pLat = lat + latDegree * rFactor * Math.sin(angle)
    const pLng = lng + lngDegree * rFactor * Math.cos(angle)
    
    coords.push([pLng, pLat])
  }
  coords.push(coords[0]) // Close polygon
  
  return coords
}

function getNrwColor(nrw: number): string {
  if (nrw >= 50) return '#dc2626'
  if (nrw >= 45) return '#ef4444'
  if (nrw >= 40) return '#f97316'
  if (nrw >= 35) return '#f59e0b'
  if (nrw >= 30) return '#eab308'
  if (nrw >= 25) return '#84cc16'
  if (nrw >= 20) return '#22c55e'
  return '#10b981'
}

function getNrwStatus(nrw: number): string {
  if (nrw >= 45) return 'critical'
  if (nrw >= 35) return 'warning'
  if (nrw >= 25) return 'moderate'
  return 'good'
}

function generateDMAs(tenantId: string): GeoJSONFeatureCollection {
  const features: GeoJSONFeature[] = DMA_DEFINITIONS.map(dma => {
    const currentNrw = Math.max(10, Math.min(65, dma.nrw + (Math.random() - 0.5) * 4))
    
    return {
      type: 'Feature',
      id: dma.id,
      geometry: {
        type: 'Polygon',
        coordinates: [generatePolygon(dma.center, dma.radius)]
      },
      properties: {
        id: dma.id,
        name: dma.name,
        type: 'dma',
        tenant_id: tenantId,
        nrw_percent: Math.round(currentNrw * 10) / 10,
        nrw_target: 20.0,
        status: getNrwStatus(currentNrw),
        fill_color: getNrwColor(currentNrw),
        fill_opacity: Math.min(0.7, 0.2 + (currentNrw / 100) * 0.6),
        stroke_color: '#1e293b',
        stroke_width: 2,
        population: dma.pop,
        connections: dma.conn,
        area_km2: Math.round(Math.PI * dma.radius * dma.radius * 100) / 100,
        flow_rate_m3h: Math.round(Math.random() * 150 + 50),
        pressure_bar: Math.round((Math.random() * 2 + 2) * 100) / 100,
        active_leaks: currentNrw > 30 ? Math.floor(Math.random() * 8) : Math.floor(Math.random() * 3),
        sensors_online: Math.floor(Math.random() * 2) + 3,
        sensors_total: 5,
        last_updated: new Date().toISOString()
      }
    }
  })
  
  return {
    type: 'FeatureCollection',
    features,
    metadata: { layer: 'dmas', total_count: features.length }
  }
}

function generateSensors(tenantId: string): GeoJSONFeatureCollection {
  const features: GeoJSONFeature[] = []
  let idx = 1
  
  const sensorTypes = ['flow', 'pressure', 'acoustic']
  
  for (const dma of DMA_DEFINITIONS) {
    const [centerLat, centerLng] = dma.center
    const spread = dma.radius / 111.0 * 0.7
    
    for (const type of sensorTypes) {
      const count = type === 'acoustic' ? 1 : 2
      
      for (let i = 0; i < count; i++) {
        const lat = centerLat + (Math.random() - 0.5) * 2 * spread
        const lng = centerLng + (Math.random() - 0.5) * 2 * spread
        
        const statusRoll = Math.random()
        let status = 'online'
        let battery = Math.floor(Math.random() * 50) + 50
        
        if (statusRoll > 0.95) {
          status = 'offline'
          battery = Math.floor(Math.random() * 10)
        } else if (statusRoll > 0.85) {
          status = 'warning'
          battery = Math.floor(Math.random() * 20) + 15
        }
        
        let value: number
        let unit: string
        
        if (type === 'flow') {
          value = Math.round(Math.random() * 1400 + 100)
          unit = 'L/hr'
        } else if (type === 'pressure') {
          value = Math.round((Math.random() * 3 + 1.5) * 100) / 100
          unit = 'bar'
        } else {
          value = Math.round(Math.random() * 70 + 15)
          unit = 'dB'
        }
        
        const sensorId = `ESP32-${String(idx).padStart(3, '0')}`
        
        features.push({
          type: 'Feature',
          id: sensorId,
          geometry: {
            type: 'Point',
            coordinates: [lng, lat]
          },
          properties: {
            id: sensorId,
            name: `${dma.name} ${type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}`,
            type: 'sensor',
            sensor_type: type,
            tenant_id: tenantId,
            dma_id: dma.id,
            dma_name: dma.name,
            status,
            battery_percent: battery,
            signal_strength: status !== 'offline' ? Math.floor(Math.random() * 40) + 60 : 0,
            value: status !== 'offline' ? value : null,
            unit,
            last_reading: status !== 'offline' 
              ? new Date().toISOString() 
              : new Date(Date.now() - Math.random() * 86400000).toISOString(),
            marker_color: status === 'online' ? '#10b981' : status === 'warning' ? '#f59e0b' : '#ef4444',
            has_alert: status === 'warning' || (type === 'acoustic' && value > 60),
            alert_type: (type === 'acoustic' && value > 60) ? 'high_acoustic' : (battery < 20 ? 'low_battery' : null)
          }
        })
        idx++
      }
    }
  }
  
  return {
    type: 'FeatureCollection',
    features,
    metadata: { layer: 'sensors', total_count: features.length }
  }
}

function generateLeaks(tenantId: string): GeoJSONFeatureCollection {
  const leakData = [
    { dma: 'dma-matero', loc: 'Great East Rd & Lumumba Rd', severity: 'critical', status: 'active', flow: 67.3 },
    { dma: 'dma-matero', loc: 'Matero Main Market', severity: 'high', status: 'assigned', flow: 45.2 },
    { dma: 'dma-chilenje', loc: 'Kafue Rd Junction', severity: 'high', status: 'active', flow: 52.1 },
    { dma: 'dma-chilenje', loc: 'Chilenje South', severity: 'medium', status: 'in-progress', flow: 28.4 },
    { dma: 'dma-mtendere', loc: 'Chelstone Market Area', severity: 'high', status: 'assigned', flow: 41.5 },
    { dma: 'dma-mtendere', loc: 'Mtendere Clinic Road', severity: 'medium', status: 'monitoring', flow: 22.8 },
    { dma: 'dma-kalingalinga', loc: 'Kalingalinga Main St', severity: 'critical', status: 'active', flow: 78.2 },
    { dma: 'dma-kabwata', loc: 'Chawama Rd Junction', severity: 'high', status: 'active', flow: 38.9 },
    { dma: 'dma-garden', loc: 'Cairo Rd South', severity: 'medium', status: 'repaired', flow: 0 },
    { dma: 'dma-rhodes-park', loc: 'Independence Ave', severity: 'low', status: 'verified', flow: 5.2 },
    { dma: 'dma-kabulonga', loc: 'Los Angeles Blvd', severity: 'medium', status: 'assigned', flow: 18.4 },
    { dma: 'dma-woodlands', loc: 'Manda Hill Area', severity: 'low', status: 'monitoring', flow: 8.1 },
    { dma: 'dma-olympia', loc: 'Olympia Park Rd', severity: 'medium', status: 'in-progress', flow: 24.6 },
    { dma: 'dma-chelstone', loc: 'Chelstone Mall Area', severity: 'high', status: 'assigned', flow: 35.7 },
  ]
  
  const dmaMap = Object.fromEntries(DMA_DEFINITIONS.map(d => [d.id, d]))
  
  const severityColors: Record<string, string> = {
    critical: '#dc2626',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6'
  }
  
  const features: GeoJSONFeature[] = leakData.map((leak, idx) => {
    const dma = dmaMap[leak.dma]
    if (!dma) return null
    
    const [centerLat, centerLng] = dma.center
    const spread = dma.radius / 111.0 * 0.6
    
    const lat = centerLat + (Math.random() - 0.5) * 2 * spread
    const lng = centerLng + (Math.random() - 0.5) * 2 * spread
    
    const leakId = `LEAK-${tenantId.slice(0, 3).toUpperCase()}-${String(idx + 1).padStart(4, '0')}`
    const daysAgo = Math.floor(Math.random() * 14)
    
    return {
      type: 'Feature',
      id: leakId,
      geometry: {
        type: 'Point',
        coordinates: [lng, lat]
      },
      properties: {
        id: leakId,
        type: 'leak',
        tenant_id: tenantId,
        dma_id: leak.dma,
        dma_name: dma.name,
        location: leak.loc,
        severity: leak.severity,
        status: leak.status,
        flow_rate_lph: leak.status !== 'repaired' ? leak.flow : 0,
        estimated_loss_m3_day: leak.flow > 0 ? Math.round(leak.flow * 24 / 1000 * 100) / 100 : 0,
        detected_at: new Date(Date.now() - daysAgo * 86400000).toISOString(),
        detection_method: ['acoustic', 'pressure_anomaly', 'flow_analysis', 'customer_report'][Math.floor(Math.random() * 4)],
        confidence_percent: leak.status !== 'verified' ? Math.floor(Math.random() * 23) + 75 : 100,
        ai_probability: Math.round(Math.random() * 0.28 * 100 + 70) / 100,
        assigned_to: ['assigned', 'in-progress'].includes(leak.status) ? `TECH-${String(Math.floor(Math.random() * 20) + 1).padStart(3, '0')}` : null,
        work_order_id: ['assigned', 'in-progress', 'repaired'].includes(leak.status) ? `WO-${Math.floor(Math.random() * 9000) + 1000}` : null,
        marker_color: severityColors[leak.severity] || '#64748b',
        marker_size: { critical: 18, high: 16, medium: 14, low: 12 }[leak.severity] || 14,
        pulse: leak.status === 'active' && ['critical', 'high'].includes(leak.severity),
        priority_score: Math.round(
          ({ critical: 1, high: 0.75, medium: 0.5, low: 0.25 }[leak.severity] || 0.5) *
          ({ active: 1, assigned: 0.8, 'in-progress': 0.6, monitoring: 0.4, repaired: 0.1, verified: 0.05 }[leak.status] || 0.5) *
          Math.min(1, leak.flow / 100) * 90
        )
      }
    }
  }).filter(Boolean) as GeoJSONFeature[]
  
  return {
    type: 'FeatureCollection',
    features,
    metadata: { layer: 'leaks', total_count: features.length }
  }
}

// =============================================================================
// API HANDLER
// =============================================================================

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    
    const tenantId = searchParams.get('tenant') || 'lusaka-water'
    const includeLayers = searchParams.get('include_layers')?.split(',') || ['dmas', 'sensors', 'leaks']
    const sensorStatus = searchParams.get('sensor_status')
    const leakStatus = searchParams.get('leak_status')
    const leakSeverity = searchParams.get('leak_severity')
    const minNrw = searchParams.get('min_nrw') ? parseFloat(searchParams.get('min_nrw')!) : null
    
    // Generate layers
    const layers: Record<string, GeoJSONFeatureCollection> = {}
    
    if (includeLayers.includes('dmas')) {
      let dmas = generateDMAs(tenantId)
      if (minNrw !== null) {
        dmas.features = dmas.features.filter(f => f.properties.nrw_percent >= minNrw)
      }
      layers.dmas = dmas
    }
    
    if (includeLayers.includes('sensors')) {
      let sensors = generateSensors(tenantId)
      if (sensorStatus && sensorStatus !== 'all') {
        sensors.features = sensors.features.filter(f => f.properties.status === sensorStatus)
      }
      layers.sensors = sensors
    }
    
    if (includeLayers.includes('leaks')) {
      let leaks = generateLeaks(tenantId)
      if (leakStatus && leakStatus !== 'all') {
        leaks.features = leaks.features.filter(f => f.properties.status === leakStatus)
      }
      if (leakSeverity && leakSeverity !== 'all') {
        leaks.features = leaks.features.filter(f => f.properties.severity === leakSeverity)
      }
      layers.leaks = leaks
    }
    
    // Calculate metadata
    const totalSensors = layers.sensors?.features.length || 0
    const sensorsOnline = layers.sensors?.features.filter(f => f.properties.status === 'online').length || 0
    const activeLeaks = layers.leaks?.features.filter(f => f.properties.status === 'active').length || 0
    
    return NextResponse.json({
      tenantId,
      layers,
      metadata: {
        total_dmas: layers.dmas?.features.length || 0,
        total_sensors: totalSensors,
        sensors_online: sensorsOnline,
        total_leaks: layers.leaks?.features.length || 0,
        active_leaks: activeLeaks,
        center: [CENTER_LNG, CENTER_LAT],
        zoom: 12,
        filters_applied: {
          sensor_status: sensorStatus,
          leak_status: leakStatus,
          leak_severity: leakSeverity,
          min_nrw: minNrw
        }
      },
      generatedAt: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Map GeoJSON API error:', error)
    return NextResponse.json(
      { error: 'Failed to generate map data' },
      { status: 500 }
    )
  }
}
