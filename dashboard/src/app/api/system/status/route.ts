import { NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

interface SystemStatus {
  mqtt_connected: boolean
  database_connected: boolean
  last_sensor_seen_at: string | null
  active_sensors: number
  offline_sensors: number
  total_sensors: number
  data_fresh: boolean
  data_staleness_minutes: number | null
  system_health: 'online' | 'degraded' | 'offline'
  uptime_seconds: number
  last_check: string
}

const STALE_THRESHOLD_MINUTES = 3 // Data older than 3 minutes is stale
const OFFLINE_THRESHOLD_MINUTES = 5 // Sensor offline if no data for 5 minutes

export async function GET() {
  const startTime = Date.now()
  
  let status: SystemStatus = {
    mqtt_connected: false,
    database_connected: false,
    last_sensor_seen_at: null,
    active_sensors: 0,
    offline_sensors: 0,
    total_sensors: 0,
    data_fresh: false,
    data_staleness_minutes: null,
    system_health: 'offline',
    uptime_seconds: 0,
    last_check: new Date().toISOString()
  }

  try {
    // Check database connection
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    // Test connection with a simple command
    await db.command({ ping: 1 })
    status.database_connected = true

    // Get sensor collection
    const sensorsCollection = db.collection('sensors')
    const readingsCollection = db.collection('sensor_readings')
    
    const now = new Date()
    const offlineThreshold = new Date(now.getTime() - OFFLINE_THRESHOLD_MINUTES * 60 * 1000)
    const staleThreshold = new Date(now.getTime() - STALE_THRESHOLD_MINUTES * 60 * 1000)

    // Count total sensors
    const totalSensors = await sensorsCollection.countDocuments()
    status.total_sensors = totalSensors

    // Count active sensors (last_seen within threshold)
    const activeSensors = await sensorsCollection.countDocuments({
      last_seen: { $gte: offlineThreshold }
    })
    status.active_sensors = activeSensors
    status.offline_sensors = totalSensors - activeSensors

    // Get last sensor reading timestamp
    const lastReading = await readingsCollection.findOne(
      {},
      { sort: { timestamp: -1 }, projection: { timestamp: 1 } }
    )

    if (lastReading?.timestamp) {
      const lastSeenDate = new Date(lastReading.timestamp)
      status.last_sensor_seen_at = lastSeenDate.toISOString()
      
      const minutesAgo = (now.getTime() - lastSeenDate.getTime()) / (1000 * 60)
      status.data_staleness_minutes = Math.round(minutesAgo * 10) / 10
      status.data_fresh = minutesAgo < STALE_THRESHOLD_MINUTES
    }

    // Check MQTT connection status from config/environment
    // In production, this would check actual MQTT broker connection
    const mqttBrokerUrl = process.env.MQTT_BROKER_URL
    status.mqtt_connected = !!mqttBrokerUrl && status.active_sensors > 0

    // Determine overall system health
    if (status.database_connected && status.active_sensors > 0 && status.data_fresh) {
      status.system_health = 'online'
    } else if (status.database_connected && (status.active_sensors > 0 || status.last_sensor_seen_at)) {
      status.system_health = 'degraded'
    } else {
      status.system_health = 'offline'
    }

    // Calculate uptime (from process start or last sensor data)
    status.uptime_seconds = Math.round((Date.now() - startTime) / 1000)

    return NextResponse.json(status)
  } catch (error) {
    console.error('System status check failed:', error)
    
    // Return offline status if any critical error - but still return 200 so frontend can display the status
    return NextResponse.json({
      ...status,
      system_health: 'offline',
      database_connected: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      last_check: new Date().toISOString()
    })
  }
}
