'use client'

import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// =============================================================================
// TYPES
// =============================================================================

interface GeoJSONFeature {
  type: 'Feature'
  id?: string
  geometry: {
    type: 'Point' | 'Polygon' | 'LineString'
    coordinates: number[] | number[][] | number[][][]
  }
  properties: Record<string, any>
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection'
  features: GeoJSONFeature[]
  metadata?: Record<string, any>
}

interface MapData {
  tenantId: string
  layers: {
    dmas?: GeoJSONFeatureCollection
    sensors?: GeoJSONFeatureCollection
    leaks?: GeoJSONFeatureCollection
  }
  metadata: {
    total_dmas: number
    total_sensors: number
    sensors_online: number
    total_leaks: number
    active_leaks: number
    center: [number, number]
    zoom: number
  }
  generatedAt: string
}

interface LayerVisibility {
  dmas: boolean
  sensors: boolean
  leaks: boolean
  heatmap: boolean
}

interface IntelligentMapViewProps {
  mapData: MapData | null
  layers: LayerVisibility
  onFeatureClick: (feature: GeoJSONFeature) => void
  selectedFeature: GeoJSONFeature | null
}

// =============================================================================
// CUSTOM ICONS
// =============================================================================

// Fix Leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Create sensor icons
const createSensorIcon = (status: string, type: string) => {
  const colors: Record<string, string> = {
    online: '#10b981',
    warning: '#f59e0b',
    offline: '#ef4444',
    maintenance: '#6366f1'
  }
  
  const typeIcons: Record<string, string> = {
    flow: '💧',
    pressure: '📊',
    acoustic: '🔊',
    quality: '🧪'
  }
  
  const color = colors[status] || '#64748b'
  const icon = typeIcons[type] || '📡'
  
  return L.divIcon({
    className: 'custom-sensor-marker',
    html: `
      <div style="
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        ${status === 'warning' ? 'animation: pulse 2s infinite;' : ''}
      ">
        ${icon}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16]
  })
}

// Create leak icons
const createLeakIcon = (severity: string, status: string) => {
  const severityColors: Record<string, string> = {
    critical: '#dc2626',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6'
  }
  
  const color = severityColors[severity] || '#64748b'
  const isActive = status === 'active'
  const size = severity === 'critical' ? 40 : severity === 'high' ? 36 : 32
  
  return L.divIcon({
    className: 'custom-leak-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        position: relative;
      ">
        ${isActive ? `
          <div style="
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            background: ${color};
            opacity: 0.3;
            animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
          "></div>
        ` : ''}
        <div style="
          width: 100%;
          height: 100%;
          border-radius: 50%;
          background: ${color};
          border: 3px solid white;
          box-shadow: 0 2px 10px rgba(0,0,0,0.4);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <span style="color: white; font-size: ${size * 0.4}px;">💧</span>
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2]
  })
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function IntelligentMapView({
  mapData,
  layers,
  onFeatureClick,
  selectedFeature
}: IntelligentMapViewProps) {
  const mapRef = useRef<L.Map | null>(null)
  const mapContainerRef = useRef<HTMLDivElement>(null)
  
  // Layer groups
  const dmaLayerRef = useRef<L.LayerGroup | null>(null)
  const sensorLayerRef = useRef<L.LayerGroup | null>(null)
  const leakLayerRef = useRef<L.LayerGroup | null>(null)
  
  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return
    
    // Lusaka center
    const defaultCenter: [number, number] = [-15.4167, 28.2833]
    const defaultZoom = 12
    
    // Create map
    const map = L.map(mapContainerRef.current, {
      center: defaultCenter,
      zoom: defaultZoom,
      zoomControl: true,
      attributionControl: true
    })
    
    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19
    }).addTo(map)
    
    // Create layer groups
    dmaLayerRef.current = L.layerGroup().addTo(map)
    sensorLayerRef.current = L.layerGroup().addTo(map)
    leakLayerRef.current = L.layerGroup().addTo(map)
    
    mapRef.current = map
    
    // Add custom CSS for animations
    const style = document.createElement('style')
    style.textContent = `
      @keyframes ping {
        0% { transform: scale(1); opacity: 0.3; }
        75%, 100% { transform: scale(2); opacity: 0; }
      }
      @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
      }
      .custom-sensor-marker, .custom-leak-marker {
        background: transparent !important;
        border: none !important;
      }
    `
    document.head.appendChild(style)
    
    return () => {
      map.remove()
      mapRef.current = null
      style.remove()
    }
  }, [])
  
  // Update map center when data changes
  useEffect(() => {
    if (!mapRef.current || !mapData?.metadata?.center) return
    
    const [lng, lat] = mapData.metadata.center
    mapRef.current.setView([lat, lng], mapData.metadata.zoom || 12)
  }, [mapData?.metadata?.center])
  
  // Render DMA layer
  useEffect(() => {
    if (!dmaLayerRef.current) return
    
    dmaLayerRef.current.clearLayers()
    
    if (!layers.dmas || !mapData?.layers?.dmas) return
    
    mapData.layers.dmas.features.forEach(feature => {
      if (feature.geometry.type !== 'Polygon') return
      
      const props = feature.properties
      const coords = (feature.geometry.coordinates[0] as number[][]).map(
        ([lng, lat]) => [lat, lng] as [number, number]
      )
      
      const polygon = L.polygon(coords, {
        fillColor: props.fill_color || '#3b82f6',
        fillOpacity: layers.heatmap ? (props.fill_opacity || 0.4) : 0.1,
        color: props.stroke_color || '#1e293b',
        weight: props.stroke_width || 2,
        opacity: 0.8
      })
      
      // Popup content
      polygon.bindPopup(`
        <div style="min-width: 200px;">
          <h3 style="font-weight: 600; margin-bottom: 8px;">${props.name}</h3>
          <div style="display: grid; gap: 4px; font-size: 13px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">NRW:</span>
              <span style="font-weight: 600; color: ${props.nrw_percent > 35 ? '#dc2626' : '#10b981'};">
                ${props.nrw_percent}%
              </span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Status:</span>
              <span style="text-transform: capitalize;">${props.status}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Active Leaks:</span>
              <span>${props.active_leaks}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Flow:</span>
              <span>${props.flow_rate_m3h} m³/h</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Pressure:</span>
              <span>${props.pressure_bar} bar</span>
            </div>
          </div>
        </div>
      `, { maxWidth: 300 })
      
      polygon.on('click', () => onFeatureClick(feature))
      
      // Highlight on hover
      polygon.on('mouseover', () => {
        polygon.setStyle({ weight: 4, fillOpacity: (props.fill_opacity || 0.4) + 0.2 })
      })
      polygon.on('mouseout', () => {
        polygon.setStyle({ weight: props.stroke_width || 2, fillOpacity: layers.heatmap ? (props.fill_opacity || 0.4) : 0.1 })
      })
      
      dmaLayerRef.current?.addLayer(polygon)
      
      // Add DMA label
      const center = polygon.getBounds().getCenter()
      const label = L.marker(center, {
        icon: L.divIcon({
          className: 'dma-label',
          html: `
            <div style="
              background: white;
              padding: 2px 8px;
              border-radius: 4px;
              font-size: 11px;
              font-weight: 600;
              white-space: nowrap;
              box-shadow: 0 1px 3px rgba(0,0,0,0.2);
              border: 1px solid ${props.fill_color || '#3b82f6'};
            ">
              ${props.name}
              <span style="color: ${props.nrw_percent > 35 ? '#dc2626' : '#10b981'}; margin-left: 4px;">
                ${props.nrw_percent}%
              </span>
            </div>
          `,
          iconSize: [0, 0],
          iconAnchor: [0, 0]
        }),
        interactive: false
      })
      dmaLayerRef.current?.addLayer(label)
    })
  }, [mapData?.layers?.dmas, layers.dmas, layers.heatmap, onFeatureClick])
  
  // Render sensor layer
  useEffect(() => {
    if (!sensorLayerRef.current) return
    
    sensorLayerRef.current.clearLayers()
    
    if (!layers.sensors || !mapData?.layers?.sensors) return
    
    mapData.layers.sensors.features.forEach(feature => {
      if (feature.geometry.type !== 'Point') return
      
      const props = feature.properties
      const [lng, lat] = feature.geometry.coordinates as number[]
      
      const marker = L.marker([lat, lng], {
        icon: createSensorIcon(props.status, props.sensor_type)
      })
      
      // Popup content
      marker.bindPopup(`
        <div style="min-width: 180px;">
          <h3 style="font-weight: 600; margin-bottom: 8px;">${props.name}</h3>
          <div style="display: grid; gap: 4px; font-size: 13px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Type:</span>
              <span style="text-transform: capitalize;">${props.sensor_type}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Status:</span>
              <span style="color: ${props.status === 'online' ? '#10b981' : props.status === 'warning' ? '#f59e0b' : '#ef4444'};">
                ${props.status}
              </span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Value:</span>
              <span style="font-weight: 600;">${props.value} ${props.unit}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Battery:</span>
              <span style="color: ${props.battery_percent < 20 ? '#ef4444' : '#10b981'};">
                ${props.battery_percent}%
              </span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">DMA:</span>
              <span>${props.dma_name}</span>
            </div>
          </div>
        </div>
      `, { maxWidth: 250 })
      
      marker.on('click', () => onFeatureClick(feature))
      
      sensorLayerRef.current?.addLayer(marker)
    })
  }, [mapData?.layers?.sensors, layers.sensors, onFeatureClick])
  
  // Render leak layer
  useEffect(() => {
    if (!leakLayerRef.current) return
    
    leakLayerRef.current.clearLayers()
    
    if (!layers.leaks || !mapData?.layers?.leaks) return
    
    mapData.layers.leaks.features.forEach(feature => {
      if (feature.geometry.type !== 'Point') return
      
      const props = feature.properties
      const [lng, lat] = feature.geometry.coordinates as number[]
      
      const marker = L.marker([lat, lng], {
        icon: createLeakIcon(props.severity, props.status),
        zIndexOffset: props.severity === 'critical' ? 1000 : props.severity === 'high' ? 500 : 0
      })
      
      // Popup content
      marker.bindPopup(`
        <div style="min-width: 200px;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span style="
              display: inline-block;
              padding: 2px 8px;
              border-radius: 4px;
              font-size: 11px;
              font-weight: 600;
              text-transform: uppercase;
              background: ${props.severity === 'critical' ? '#fef2f2' : props.severity === 'high' ? '#fff7ed' : '#fefce8'};
              color: ${props.severity === 'critical' ? '#dc2626' : props.severity === 'high' ? '#ea580c' : '#ca8a04'};
            ">
              ${props.severity}
            </span>
            <span style="
              display: inline-block;
              padding: 2px 8px;
              border-radius: 4px;
              font-size: 11px;
              background: ${props.status === 'active' ? '#fef2f2' : '#f0f9ff'};
              color: ${props.status === 'active' ? '#dc2626' : '#0369a1'};
            ">
              ${props.status}
            </span>
          </div>
          <h3 style="font-weight: 600; margin-bottom: 8px;">${props.location}</h3>
          <div style="display: grid; gap: 4px; font-size: 13px;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Flow Rate:</span>
              <span style="font-weight: 600; color: #dc2626;">${props.flow_rate_lph} L/hr</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Est. Loss:</span>
              <span>${props.estimated_loss_m3_day} m³/day</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Detection:</span>
              <span style="text-transform: capitalize;">${props.detection_method?.replace('_', ' ')}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">AI Confidence:</span>
              <span>${props.confidence_percent}%</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">DMA:</span>
              <span>${props.dma_name}</span>
            </div>
          </div>
          ${props.status === 'active' ? `
            <button style="
              width: 100%;
              margin-top: 12px;
              padding: 8px;
              background: #2563eb;
              color: white;
              border: none;
              border-radius: 6px;
              font-weight: 600;
              cursor: pointer;
            ">
              Create Work Order
            </button>
          ` : ''}
        </div>
      `, { maxWidth: 280 })
      
      marker.on('click', () => onFeatureClick(feature))
      
      leakLayerRef.current?.addLayer(marker)
    })
  }, [mapData?.layers?.leaks, layers.leaks, onFeatureClick])
  
  // Highlight selected feature
  useEffect(() => {
    if (!mapRef.current || !selectedFeature) return
    
    const props = selectedFeature.properties
    const geometry = selectedFeature.geometry
    
    if (geometry.type === 'Point') {
      const [lng, lat] = geometry.coordinates as number[]
      mapRef.current.setView([lat, lng], 15, { animate: true })
    } else if (geometry.type === 'Polygon') {
      const coords = (geometry.coordinates[0] as number[][]).map(
        ([lng, lat]) => [lat, lng] as [number, number]
      )
      const bounds = L.latLngBounds(coords)
      mapRef.current.fitBounds(bounds, { padding: [50, 50], animate: true })
    }
  }, [selectedFeature])
  
  return (
    <div 
      ref={mapContainerRef} 
      className="w-full h-full"
      style={{ minHeight: '400px' }}
    />
  )
}
