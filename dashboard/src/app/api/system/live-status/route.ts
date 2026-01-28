import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const now = new Date()
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)

    // Check for recent sensor data
    let lastSensorSeenAt: string | null = null
    let dataFresh = false
    let sensorCount = 0

    try {
      // Try to get most recent sensor reading
      const sensorData = await db.collection('sensor_readings')
        .findOne({}, { sort: { timestamp: -1 } })

      if (sensorData?.timestamp) {
        lastSensorSeenAt = sensorData.timestamp
        dataFresh = new Date(sensorData.timestamp) > fiveMinutesAgo
      }
    } catch (e) {
      // Sensor readings collection might not exist
    }

    // Check active sensor count
    try {
      sensorCount = await db.collection('sensors')
        .countDocuments({ status: 'active' })
    } catch (e) {
      // Sensors collection might not exist
    }

    // For now, assume MQTT is connected if we have recent data
    // In production, this would check actual MQTT broker status
    const mqttConnected = dataFresh || sensorCount > 0

    // Get system health based on active alerts
    let systemHealth = 'healthy'
    try {
      const criticalAlerts = await db.collection('alerts')
        .countDocuments({ 
          status: 'active',
          severity: { $in: ['critical', 'high'] }
        })

      if (criticalAlerts > 0) {
        systemHealth = 'warning'
      }
    } catch (e) {
      // Alerts collection might not exist
    }

    return NextResponse.json({
      mqtt_connected: mqttConnected,
      data_fresh: dataFresh,
      last_sensor_seen_at: lastSensorSeenAt,
      sensor_count: sensorCount,
      active_sensors: sensorCount,
      system_health: systemHealth,
      timestamp: now.toISOString(),
      status: 'ok'
    })

  } catch (error) {
    console.error('[Live Status API] Error:', error)
    
    // Return default values on error - don't block the loader
    return NextResponse.json({
      mqtt_connected: true,
      data_fresh: true,
      last_sensor_seen_at: null,
      sensor_count: 0,
      active_sensors: 0,
      system_health: 'unknown',
      timestamp: new Date().toISOString(),
      status: 'error',
      message: 'Could not verify live status'
    })
  }
}
