import { NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

const OFFLINE_THRESHOLD_MINUTES = 5

interface Sensor {
  id: string
  type: string
  dma: string
  value: number | null
  unit: string
  status: 'online' | 'offline' | 'warning'
  battery: number | null
  last_reading: string | null
}

export async function GET() {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const now = new Date()
    const offlineThreshold = new Date(now.getTime() - OFFLINE_THRESHOLD_MINUTES * 60 * 1000)
    
    // Fetch real sensors from database
    const sensors = await db.collection('sensors').find({}).toArray()
    
    if (sensors.length === 0) {
      return NextResponse.json({
        success: true,
        data: [],
        data_available: false,
        message: 'No sensors registered. Connect ESP32 sensors to begin monitoring.',
        online_count: 0,
        offline_count: 0,
        total_count: 0,
        timestamp: now.toISOString()
      })
    }

    // Enrich sensors with latest readings and online status
    const enrichedSensors: Sensor[] = await Promise.all(sensors.map(async (sensor) => {
      // Get latest reading for this sensor
      const latestReading = await db.collection('sensor_readings').findOne(
        { sensor_id: sensor.sensor_id || sensor.id },
        { sort: { timestamp: -1 } }
      )

      const lastSeenDate = latestReading?.timestamp ? new Date(latestReading.timestamp) : 
                           sensor.last_seen ? new Date(sensor.last_seen) : null
      
      // Determine status based on last_seen
      let status: Sensor['status'] = 'offline'
      if (lastSeenDate && lastSeenDate >= offlineThreshold) {
        status = sensor.battery && sensor.battery < 20 ? 'warning' : 'online'
      }

      // Get the appropriate value based on sensor type
      let value: number | null = null
      let unit = ''
      if (latestReading) {
        if (sensor.type === 'pressure' || sensor.type === 'pressure_sensor') {
          value = latestReading.pressure ?? null
          unit = 'bar'
        } else if (sensor.type === 'flow' || sensor.type === 'flow_meter') {
          value = latestReading.flow_rate ?? null
          unit = 'm³/h'
        } else if (sensor.type === 'acoustic' || sensor.type === 'acoustic_sensor') {
          value = latestReading.acoustic_level ?? null
          unit = 'dB'
        }
      }

      return {
        id: sensor.sensor_id || sensor.id,
        type: sensor.type || 'unknown',
        dma: sensor.dma || 'Unassigned',
        value,
        unit,
        status,
        battery: sensor.battery ?? latestReading?.battery_level ?? null,
        last_reading: lastSeenDate?.toISOString() || null
      }
    }))

    const onlineCount = enrichedSensors.filter(s => s.status === 'online').length
    const offlineCount = enrichedSensors.filter(s => s.status === 'offline').length

    return NextResponse.json({
      success: true,
      data: enrichedSensors,
      data_available: true,
      online_count: onlineCount,
      offline_count: offlineCount,
      total_count: enrichedSensors.length,
      timestamp: now.toISOString()
    })

  } catch (error) {
    console.error('[Sensors API] Error:', error)
    return NextResponse.json({
      success: true,
      data: [],
      data_available: false,
      message: 'Database unavailable. Connect to MongoDB to see sensor data.',
      online_count: 0,
      offline_count: 0,
      total_count: 0,
      timestamp: new Date().toISOString()
    })
  }
}
