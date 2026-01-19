import { NextResponse } from 'next/server'

function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export async function GET() {
  return NextResponse.json({
    // Primary metrics expected by dashboard
    total_nrw_percent: parseFloat((32.4 + randomFloat(-3, 3)).toFixed(1)),
    water_recovered_30d: 245800 + randomInt(-10000, 10000),
    revenue_recovered_30d: 1847000 + randomInt(-50000, 50000),
    sensor_count: 48,
    dma_count: 12,
    active_high_priority_leaks: randomInt(2, 5),
    ai_confidence: parseFloat((94 + randomFloat(-2, 2)).toFixed(1)),
    last_data_received: new Date().toISOString(),
    
    // Additional metrics
    nrw_percentage: parseFloat((28.5 + randomFloat(-3, 3)).toFixed(1)),
    nrw_trend: parseFloat((-2.3 + randomFloat(-1, 1)).toFixed(1)),
    total_leaks_detected: 156 + randomInt(0, 5),
    leaks_this_month: 12 + randomInt(-2, 2),
    water_saved_m3: 45000 + randomInt(-1000, 1000),
    cost_saved_php: 900000 + randomInt(-50000, 50000),
    active_alerts: randomInt(2, 5),
    sensors_online: 24 + randomInt(-2, 0),
    sensors_total: 26,
    system_health: randomInt(93, 98),
    ai_accuracy: parseFloat((87.5 + randomFloat(-2, 2)).toFixed(1)),
    response_time_avg_hours: parseFloat((2.3 + randomFloat(-0.5, 0.5)).toFixed(1)),
    timestamp: new Date().toISOString()
  })
}
