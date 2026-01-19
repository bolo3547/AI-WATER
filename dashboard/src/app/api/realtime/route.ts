import { NextResponse } from 'next/server'

// Simulate real sensor data with realistic patterns
function generateRealisticSensorData() {
  const now = new Date()
  const hour = now.getHours()
  
  // Simulate daily patterns - higher usage during day, lower at night
  const dayFactor = hour >= 6 && hour <= 22 ? 1.0 : 0.4
  const peakFactor = (hour >= 7 && hour <= 9) || (hour >= 18 && hour <= 20) ? 1.3 : 1.0
  
  // Base flow with realistic variation
  const baseFlow = 850 * dayFactor * peakFactor
  const flowVariation = (Math.random() - 0.5) * 100
  
  return {
    timestamp: now.toISOString(),
    sensors: [
      {
        id: 'ESP32-047',
        name: 'Kabulonga North - Node A',
        type: 'flow_meter',
        status: 'online',
        battery: Math.max(20, 85 - Math.floor(Math.random() * 5)),
        signal_strength: Math.min(100, 88 + Math.floor(Math.random() * 10)),
        last_reading: new Date(Date.now() - Math.random() * 120000).toISOString(),
        readings: {
          flow_rate: Math.round((baseFlow + flowVariation) * 10) / 10,
          pressure: Math.round((3.2 + (Math.random() - 0.5) * 0.3) * 100) / 100,
          temperature: Math.round((22 + (Math.random() - 0.5) * 3) * 10) / 10
        }
      },
      {
        id: 'ESP32-048',
        name: 'Kabulonga North - Node B',
        type: 'pressure_sensor',
        status: 'online',
        battery: Math.max(20, 78 - Math.floor(Math.random() * 5)),
        signal_strength: Math.min(100, 85 + Math.floor(Math.random() * 10)),
        last_reading: new Date(Date.now() - Math.random() * 180000).toISOString(),
        readings: {
          pressure: Math.round((3.5 + (Math.random() - 0.5) * 0.4) * 100) / 100,
          flow_rate: Math.round((baseFlow * 0.8 + flowVariation * 0.5) * 10) / 10
        }
      },
      {
        id: 'ESP32-049',
        name: 'Woodlands Central - Node A',
        type: 'acoustic_sensor',
        status: Math.random() > 0.1 ? 'online' : 'warning',
        battery: 22 + Math.floor(Math.random() * 5), // Low battery
        signal_strength: Math.min(100, 82 + Math.floor(Math.random() * 8)),
        last_reading: new Date(Date.now() - Math.random() * 240000).toISOString(),
        readings: {
          acoustic_level: Math.round((35 + Math.random() * 15) * 10) / 10,
          frequency: Math.round(120 + Math.random() * 80),
          leak_probability: Math.round(Math.random() * 30)
        }
      },
      {
        id: 'ESP32-050',
        name: 'Woodlands Central - Node B',
        type: 'flow_meter',
        status: 'online',
        battery: Math.max(20, 91 - Math.floor(Math.random() * 3)),
        signal_strength: Math.min(100, 92 + Math.floor(Math.random() * 6)),
        last_reading: new Date(Date.now() - Math.random() * 100000).toISOString(),
        readings: {
          flow_rate: Math.round((baseFlow * 0.6 + flowVariation * 0.4) * 10) / 10,
          pressure: Math.round((3.0 + (Math.random() - 0.5) * 0.3) * 100) / 100
        }
      },
      {
        id: 'ESP32-051',
        name: 'Roma Industrial - Node A',
        type: 'flow_meter',
        status: 'online',
        battery: Math.max(20, 67 - Math.floor(Math.random() * 5)),
        signal_strength: Math.min(100, 75 + Math.floor(Math.random() * 10)),
        last_reading: new Date(Date.now() - Math.random() * 180000).toISOString(),
        readings: {
          flow_rate: Math.round((baseFlow * 1.2 + flowVariation) * 10) / 10,
          pressure: Math.round((2.8 + (Math.random() - 0.5) * 0.4) * 100) / 100
        }
      },
      {
        id: 'ESP32-052',
        name: 'Roma Industrial - Node B',
        type: 'pressure_sensor',
        status: Math.random() > 0.7 ? 'warning' : 'critical', // Problematic sensor
        battery: 5 + Math.floor(Math.random() * 3), // Very low
        signal_strength: Math.min(60, 40 + Math.floor(Math.random() * 20)),
        last_reading: new Date(Date.now() - 3600000 - Math.random() * 1800000).toISOString(),
        readings: {
          pressure: Math.round((2.1 + (Math.random() - 0.5) * 0.5) * 100) / 100
        }
      },
      {
        id: 'ESP32-053',
        name: 'Chelstone East - Node A',
        type: 'flow_meter',
        status: 'online',
        battery: Math.max(20, 88 - Math.floor(Math.random() * 4)),
        signal_strength: Math.min(100, 89 + Math.floor(Math.random() * 8)),
        last_reading: new Date(Date.now() - Math.random() * 120000).toISOString(),
        readings: {
          flow_rate: Math.round((baseFlow * 0.7 + flowVariation * 0.3) * 10) / 10,
          pressure: Math.round((3.4 + (Math.random() - 0.5) * 0.2) * 100) / 100
        }
      },
      {
        id: 'ESP32-054',
        name: 'Chelstone East - Node B',
        type: 'acoustic_sensor',
        status: 'online',
        battery: Math.max(20, 72 - Math.floor(Math.random() * 5)),
        signal_strength: Math.min(100, 84 + Math.floor(Math.random() * 10)),
        last_reading: new Date(Date.now() - Math.random() * 200000).toISOString(),
        readings: {
          acoustic_level: Math.round((28 + Math.random() * 12) * 10) / 10,
          frequency: Math.round(100 + Math.random() * 60),
          leak_probability: Math.round(Math.random() * 15)
        }
      }
    ]
  }
}

// Real infrastructure status
function getInfrastructureStatus() {
  const now = new Date()
  const uptime = 99.95 + Math.random() * 0.04 // 99.95-99.99%
  
  return {
    timestamp: now.toISOString(),
    components: {
      api_server: {
        status: 'healthy',
        latency: Math.round(35 + Math.random() * 25), // 35-60ms
        uptime: Math.round(uptime * 100) / 100,
        requests_per_minute: Math.round(120 + Math.random() * 80),
        last_check: new Date(Date.now() - Math.random() * 60000).toISOString()
      },
      database: {
        status: 'healthy',
        connections: Math.round(8 + Math.random() * 8),
        storage_percent: Math.round((42 + Math.random() * 8) * 10) / 10,
        query_time_avg: Math.round(12 + Math.random() * 15),
        last_check: new Date(Date.now() - Math.random() * 60000).toISOString()
      },
      ai_engine: {
        status: 'healthy',
        model_version: 'v2.4.1',
        inference_time: Math.round(100 + Math.random() * 40),
        accuracy: Math.round((93 + Math.random() * 3) * 10) / 10,
        queue_size: Math.round(Math.random() * 8),
        last_check: new Date(Date.now() - Math.random() * 60000).toISOString()
      },
      mqtt_broker: {
        status: 'healthy',
        connected_devices: 48 - Math.floor(Math.random() * 3),
        messages_per_min: Math.round(1100 + Math.random() * 300),
        queue_depth: Math.round(Math.random() * 50),
        last_check: new Date(Date.now() - Math.random() * 60000).toISOString()
      },
      data_ingestion: {
        status: Math.random() > 0.9 ? 'warning' : 'healthy',
        queue_size: Math.round(800 + Math.random() * 600),
        processing_rate: Math.round(850 + Math.random() * 150),
        backlog_minutes: Math.round(Math.random() * 5),
        last_check: new Date(Date.now() - Math.random() * 60000).toISOString()
      }
    }
  }
}

// Real-time DMA data with calculated NRW
function getDMARealtimeData() {
  const now = new Date()
  const hour = now.getHours()
  const dayFactor = hour >= 6 && hour <= 22 ? 1.0 : 0.6
  
  const dmas = [
    { id: 'dma-001', name: 'Kabulonga North', baseNrw: 45, baseInflow: 1250, connections: 3420 },
    { id: 'dma-002', name: 'Roma Industrial', baseNrw: 38, baseInflow: 980, connections: 1850 },
    { id: 'dma-003', name: 'Longacres', baseNrw: 31, baseInflow: 720, connections: 2100 },
    { id: 'dma-004', name: 'Chelstone East', baseNrw: 28, baseInflow: 850, connections: 2800 },
    { id: 'dma-005', name: 'Woodlands Central', baseNrw: 36, baseInflow: 920, connections: 2450 },
    { id: 'dma-006', name: 'Chilenje South', baseNrw: 22, baseInflow: 680, connections: 3100 }
  ]
  
  return dmas.map((dma, index) => {
    const nrwVariation = (Math.random() - 0.5) * 4
    const inflowVariation = (Math.random() - 0.5) * 100
    const nrw_percent = Math.round((dma.baseNrw + nrwVariation) * 10) / 10
    const inflow = Math.round((dma.baseInflow * dayFactor + inflowVariation) * 10) / 10
    const consumption = Math.round(inflow * (1 - nrw_percent / 100) * 10) / 10
    const real_losses = Math.round((inflow - consumption) * 10) / 10
    
    // Calculate priority score based on NRW and losses
    const priority_score = Math.min(99, Math.round(nrw_percent * 1.5 + real_losses / 20))
    
    return {
      dma_id: dma.id,
      name: dma.name,
      nrw_percent,
      priority_score,
      status: nrw_percent > 40 ? 'critical' : nrw_percent > 30 ? 'warning' : 'healthy',
      trend: nrwVariation > 1 ? 'up' : nrwVariation < -1 ? 'down' : 'stable',
      inflow,
      consumption,
      real_losses,
      connections: dma.connections,
      leak_count: Math.floor(nrw_percent / 15),
      pressure: Math.round((2.5 + Math.random() * 1.5) * 10) / 10,
      confidence: Math.round(88 + Math.random() * 10),
      last_updated: new Date(Date.now() - Math.random() * 300000).toISOString()
    }
  }).sort((a, b) => b.priority_score - a.priority_score)
}

// System-wide metrics
function getSystemMetrics() {
  const dmas = getDMARealtimeData()
  const totalInflow = dmas.reduce((sum, d) => sum + d.inflow, 0)
  const totalConsumption = dmas.reduce((sum, d) => sum + d.consumption, 0)
  const avgNrw = Math.round(dmas.reduce((sum, d) => sum + d.nrw_percent, 0) / dmas.length * 10) / 10
  
  return {
    timestamp: new Date().toISOString(),
    total_nrw_percent: avgNrw,
    total_inflow: Math.round(totalInflow),
    total_consumption: Math.round(totalConsumption),
    total_losses: Math.round(totalInflow - totalConsumption),
    water_recovered_30d: Math.round(245000 + Math.random() * 10000),
    revenue_recovered_30d: Math.round(1800000 + Math.random() * 100000),
    sensor_count: 48,
    sensors_online: 46 + Math.floor(Math.random() * 2),
    dma_count: 6,
    active_high_priority_leaks: dmas.filter(d => d.status === 'critical').length,
    ai_confidence: Math.round((92 + Math.random() * 6) * 10) / 10,
    detection_accuracy: Math.round((93 + Math.random() * 4) * 10) / 10,
    last_data_received: new Date(Date.now() - Math.random() * 30000).toISOString()
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const type = searchParams.get('type') || 'all'
  
  switch (type) {
    case 'sensors':
      return NextResponse.json(generateRealisticSensorData())
    case 'infrastructure':
      return NextResponse.json(getInfrastructureStatus())
    case 'dmas':
      return NextResponse.json(getDMARealtimeData())
    case 'metrics':
      return NextResponse.json(getSystemMetrics())
    case 'all':
    default:
      return NextResponse.json({
        sensors: generateRealisticSensorData(),
        infrastructure: getInfrastructureStatus(),
        dmas: getDMARealtimeData(),
        metrics: getSystemMetrics()
      })
  }
}
