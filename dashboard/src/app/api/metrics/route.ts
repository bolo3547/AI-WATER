import { NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

interface MetricsResponse {
  data_available: boolean
  message: string
  // Primary metrics
  total_nrw_percent: number | null
  water_recovered_30d: number | null
  revenue_recovered_30d: number | null
  sensor_count: number
  dma_count: number
  active_high_priority_leaks: number
  ai_confidence: number | null
  last_data_received: string | null
  // Additional metrics
  nrw_percentage: number | null
  nrw_trend: number | null
  total_leaks_detected: number
  leaks_this_month: number
  water_saved_m3: number | null
  cost_saved_php: number | null
  active_alerts: number
  sensors_online: number
  sensors_total: number
  system_health: number | null
  ai_accuracy: number | null
  response_time_avg_hours: number | null
  timestamp: string
}

export async function GET() {
  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)

  // Default response when no data is available
  const emptyResponse: MetricsResponse = {
    data_available: false,
    message: 'Waiting for sensor data. Connect ESP32 sensors to begin monitoring.',
    total_nrw_percent: null,
    water_recovered_30d: null,
    revenue_recovered_30d: null,
    sensor_count: 0,
    dma_count: 0,
    active_high_priority_leaks: 0,
    ai_confidence: null,
    last_data_received: null,
    nrw_percentage: null,
    nrw_trend: null,
    total_leaks_detected: 0,
    leaks_this_month: 0,
    water_saved_m3: null,
    cost_saved_php: null,
    active_alerts: 0,
    sensors_online: 0,
    sensors_total: 0,
    system_health: null,
    ai_accuracy: null,
    response_time_avg_hours: null,
    timestamp: now.toISOString()
  }

  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')

    // Get real counts from database
    const [
      sensorCount,
      dmaCount,
      leaksTotal,
      leaksThisMonth,
      highPriorityLeaks,
      activeAlerts,
      lastReading
    ] = await Promise.all([
      db.collection('sensors').countDocuments(),
      db.collection('dmas').countDocuments(),
      db.collection('leaks').countDocuments(),
      db.collection('leaks').countDocuments({ detected_at: { $gte: startOfMonth.toISOString() } }),
      db.collection('leaks').countDocuments({ priority: 'high', status: { $ne: 'resolved' } }),
      db.collection('alerts').countDocuments({ status: 'active' }),
      db.collection('sensor_readings').findOne({}, { sort: { timestamp: -1 } })
    ])

    // Check if we have any real sensor data
    const hasData = sensorCount > 0 || lastReading !== null

    if (!hasData) {
      return NextResponse.json(emptyResponse)
    }

    // Count online sensors (last_seen within 5 minutes)
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000)
    const onlineSensors = await db.collection('sensors').countDocuments({
      last_seen: { $gte: fiveMinutesAgo }
    })

    // Calculate NRW metrics from actual DMA data
    const dmaData = await db.collection('dmas').find({}).toArray()
    let avgNrw: number | null = null
    if (dmaData.length > 0) {
      const totalNrw = dmaData.reduce((sum, dma) => sum + (dma.nrw_percent || 0), 0)
      avgNrw = Math.round((totalNrw / dmaData.length) * 10) / 10
    }

    // Get water saved from resolved leaks
    const resolvedLeaks = await db.collection('leaks').find({
      status: 'resolved',
      resolved_at: { $gte: thirtyDaysAgo.toISOString() }
    }).toArray()
    
    const waterSaved = resolvedLeaks.reduce((sum, leak) => sum + (leak.estimated_loss || 0), 0)
    const costSaved = waterSaved * 20 // Approximate cost per m³ in ZMW

    // Get AI confidence from latest analysis
    const latestAnalysis = await db.collection('ai_analysis').findOne({}, { sort: { timestamp: -1 } })

    return NextResponse.json({
      data_available: true,
      message: hasData ? 'Live data from sensors' : 'No data yet',
      total_nrw_percent: avgNrw,
      water_recovered_30d: waterSaved > 0 ? waterSaved : null,
      revenue_recovered_30d: costSaved > 0 ? costSaved : null,
      sensor_count: sensorCount,
      dma_count: dmaCount,
      active_high_priority_leaks: highPriorityLeaks,
      ai_confidence: latestAnalysis?.confidence || null,
      last_data_received: lastReading?.timestamp || null,
      nrw_percentage: avgNrw,
      nrw_trend: null, // Would need historical data to calculate
      total_leaks_detected: leaksTotal,
      leaks_this_month: leaksThisMonth,
      water_saved_m3: waterSaved > 0 ? waterSaved : null,
      cost_saved_php: costSaved > 0 ? costSaved : null,
      active_alerts: activeAlerts,
      sensors_online: onlineSensors,
      sensors_total: sensorCount,
      system_health: sensorCount > 0 ? Math.round((onlineSensors / sensorCount) * 100) : null,
      ai_accuracy: latestAnalysis?.accuracy || null,
      response_time_avg_hours: null, // Would need work order completion data
      timestamp: now.toISOString()
    } as MetricsResponse)

  } catch (error) {
    console.error('[Metrics API] Error:', error)
    return NextResponse.json({
      ...emptyResponse,
      message: 'Database connection unavailable. Showing empty state.'
    })
  }
}
