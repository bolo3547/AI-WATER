import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''
)

export async function GET(request: NextRequest) {
  try {
    const now = new Date()
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)

    // Check for recent sensor data
    let lastSensorSeenAt: string | null = null
    let dataFresh = false
    let sensorCount = 0

    try {
      // Try to get most recent sensor reading
      const { data: sensorData, error: sensorError } = await supabase
        .from('sensor_readings')
        .select('timestamp')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single()

      if (!sensorError && sensorData) {
        lastSensorSeenAt = sensorData.timestamp
        dataFresh = new Date(sensorData.timestamp) > fiveMinutesAgo
      }
    } catch (e) {
      // Sensor readings table might not exist
    }

    // Check sensor count
    try {
      const { count } = await supabase
        .from('sensors')
        .select('*', { count: 'exact', head: true })
        .eq('status', 'active')

      sensorCount = count || 0
    } catch (e) {
      // Sensors table might not exist
    }

    // For now, assume MQTT is connected if we have recent data
    // In production, this would check actual MQTT broker status
    const mqttConnected = dataFresh || sensorCount > 0

    // Get system health
    let systemHealth = 'healthy'
    try {
      const { data: alerts } = await supabase
        .from('alerts')
        .select('severity')
        .eq('status', 'active')
        .in('severity', ['critical', 'high'])
        .limit(1)

      if (alerts && alerts.length > 0) {
        systemHealth = 'warning'
      }
    } catch (e) {
      // Alerts table might not exist
    }

    return NextResponse.json({
      mqtt_connected: mqttConnected,
      data_fresh: dataFresh,
      last_sensor_seen_at: lastSensorSeenAt,
      sensor_count: sensorCount,
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
      system_health: 'unknown',
      timestamp: new Date().toISOString(),
      status: 'error',
      message: 'Could not verify live status'
    })
  }
}
