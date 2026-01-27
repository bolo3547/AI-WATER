import { NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

const OFFLINE_THRESHOLD_MINUTES = 5
const STALE_THRESHOLD_MINUTES = 3

interface AIAnalysis {
  is_leak: boolean
  leak_type: 'none' | 'suspected' | 'probable' | 'confirmed'
  confidence: number
  severity: 'low' | 'medium' | 'high' | 'critical'
}

interface SensorReading {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'warning' | 'critical'
  battery: number | null
  signal_strength: number | null
  last_reading: string | null
  readings: Record<string, number>
  ai_analysis?: AIAnalysis
}

interface RealtimeResponse {
  timestamp: string
  data_available: boolean
  data_fresh: boolean
  message: string
  sensors: SensorReading[]
  system_metrics: {
    total_flow: number | null
    avg_pressure: number | null
    active_alerts: number
    ai_status: {
      model_version: string
      accuracy: number
      active_leaks: number
      leaks_today: number
    }
  }
}

export async function GET() {
  const now = new Date()
  const offlineThreshold = new Date(now.getTime() - OFFLINE_THRESHOLD_MINUTES * 60 * 1000)
  const staleThreshold = new Date(now.getTime() - STALE_THRESHOLD_MINUTES * 60 * 1000)

  // Default empty response
  const emptyResponse: RealtimeResponse = {
    timestamp: now.toISOString(),
    data_available: false,
    data_fresh: false,
    message: 'Waiting for sensor data. Connect ESP32 sensors via MQTT to begin real-time monitoring.',
    sensors: [],
    system_metrics: {
      total_flow: null,
      avg_pressure: null,
      active_alerts: 0,
      ai_status: {
        model_version: '2.2.0',
        accuracy: 94.5,
        active_leaks: 0,
        leaks_today: 0
      }
    }
  }

  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')

    // Get all sensors with their latest readings
    const sensors = await db.collection('sensors').find({}).toArray()

    if (sensors.length === 0) {
      return NextResponse.json(emptyResponse)
    }

    // Get the most recent reading timestamp
    const latestReading = await db.collection('sensor_readings').findOne(
      {},
      { sort: { timestamp: -1 } }
    )

    const lastDataTime = latestReading?.timestamp ? new Date(latestReading.timestamp) : null
    const dataFresh = lastDataTime ? lastDataTime >= staleThreshold : false

    // Enrich each sensor with its latest reading
    const enrichedSensors: SensorReading[] = await Promise.all(sensors.map(async (sensor) => {
      const reading = await db.collection('sensor_readings').findOne(
        { sensor_id: sensor.sensor_id || sensor.id },
        { sort: { timestamp: -1 } }
      )

      const lastSeenDate = reading?.timestamp ? new Date(reading.timestamp) : null
      
      // Determine status
      let status: SensorReading['status'] = 'offline'
      if (lastSeenDate) {
        if (lastSeenDate < offlineThreshold) {
          status = 'offline'
        } else if (sensor.battery && sensor.battery < 10) {
          status = 'critical'
        } else if (sensor.battery && sensor.battery < 25) {
          status = 'warning'
        } else {
          status = 'online'
        }
      }

      // Build readings object based on sensor type
      const readings: Record<string, number> = {}
      if (reading) {
        if (reading.flow_rate !== undefined) readings.flow_rate = reading.flow_rate
        if (reading.pressure !== undefined) readings.pressure = reading.pressure
        if (reading.temperature !== undefined) readings.temperature = reading.temperature
        if (reading.acoustic_level !== undefined) readings.acoustic_level = reading.acoustic_level
        if (reading.leak_probability !== undefined) readings.leak_probability = reading.leak_probability
      }

      return {
        id: sensor.sensor_id || sensor.id,
        name: sensor.name || `Sensor ${sensor.sensor_id || sensor.id}`,
        type: sensor.type || 'unknown',
        status,
        battery: sensor.battery ?? reading?.battery_level ?? null,
        signal_strength: sensor.signal_strength ?? reading?.signal_strength ?? null,
        last_reading: lastSeenDate?.toISOString() || null,
        readings,
        ai_analysis: reading?.ai_analysis ? {
          is_leak: reading.ai_analysis.leak_type !== 'none',
          leak_type: reading.ai_analysis.leak_type || 'none',
          confidence: reading.ai_analysis.confidence || 0,
          severity: reading.ai_analysis.severity || 'low'
        } : undefined
      }
    }))

    // Calculate system metrics from real data
    const flowReadings = enrichedSensors
      .filter(s => s.readings.flow_rate !== undefined)
      .map(s => s.readings.flow_rate)
    
    const pressureReadings = enrichedSensors
      .filter(s => s.readings.pressure !== undefined)
      .map(s => s.readings.pressure)

    const totalFlow = flowReadings.length > 0 
      ? Math.round(flowReadings.reduce((a, b) => a + b, 0) * 10) / 10 
      : null

    const avgPressure = pressureReadings.length > 0
      ? Math.round((pressureReadings.reduce((a, b) => a + b, 0) / pressureReadings.length) * 100) / 100
      : null

    const activeAlerts = await db.collection('alerts').countDocuments({ status: 'active' })
    
    // Get AI leak detection stats
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const [activeLeaks, leaksToday] = await Promise.all([
      db.collection('leaks').countDocuments({ status: { $in: ['new', 'investigating', 'confirmed'] } }),
      db.collection('leaks').countDocuments({ detected_at: { $gte: today.toISOString() } })
    ])

    const onlineSensors = enrichedSensors.filter(s => s.status === 'online' || s.status === 'warning')

    return NextResponse.json({
      timestamp: now.toISOString(),
      data_available: enrichedSensors.length > 0,
      data_fresh: dataFresh,
      message: dataFresh 
        ? `Live data from ${onlineSensors.length} sensors` 
        : lastDataTime 
          ? `Stale data - last reading ${Math.round((now.getTime() - lastDataTime.getTime()) / 60000)} minutes ago`
          : 'No sensor readings yet',
      sensors: enrichedSensors,
      system_metrics: {
        total_flow: totalFlow,
        avg_pressure: avgPressure,
        active_alerts: activeAlerts,
        ai_status: {
          model_version: '2.2.0',
          accuracy: 94.5,
          active_leaks: activeLeaks,
          leaks_today: leaksToday
        }
      }
    } as RealtimeResponse)

  } catch (error) {
    console.error('[Realtime API] Error:', error)
    return NextResponse.json({
      ...emptyResponse,
      message: 'Database connection unavailable.'
    })
  }
}
