import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

/**
 * AI Leak Detection Simulator
 * ============================
 * Generates realistic sensor data with various leak scenarios
 * to test and validate the AI detection engine.
 */

interface SimulationScenario {
  name: string
  description: string
  duration_minutes: number
  pressure_baseline: number
  flow_baseline: number
  leak_start_minute?: number
  leak_type?: 'gradual' | 'sudden' | 'burst' | 'intermittent'
  leak_magnitude?: number // 0-1 scale
}

const SCENARIOS: Record<string, SimulationScenario> = {
  normal: {
    name: 'Normal Operation',
    description: 'Typical sensor readings with no leaks',
    duration_minutes: 60,
    pressure_baseline: 3.0,
    flow_baseline: 50
  },
  gradual_leak: {
    name: 'Gradual Leak',
    description: 'Slow developing leak - pressure drops gradually over time',
    duration_minutes: 120,
    pressure_baseline: 3.0,
    flow_baseline: 50,
    leak_start_minute: 30,
    leak_type: 'gradual',
    leak_magnitude: 0.4
  },
  sudden_leak: {
    name: 'Sudden Leak',
    description: 'Sudden pressure drop indicating a pipe break',
    duration_minutes: 60,
    pressure_baseline: 3.0,
    flow_baseline: 50,
    leak_start_minute: 20,
    leak_type: 'sudden',
    leak_magnitude: 0.6
  },
  burst: {
    name: 'Pipe Burst',
    description: 'Major burst - large pressure drop, high flow',
    duration_minutes: 30,
    pressure_baseline: 3.0,
    flow_baseline: 50,
    leak_start_minute: 10,
    leak_type: 'burst',
    leak_magnitude: 0.9
  },
  intermittent: {
    name: 'Intermittent Leak',
    description: 'On-and-off leak pattern - hard to detect',
    duration_minutes: 180,
    pressure_baseline: 3.0,
    flow_baseline: 50,
    leak_start_minute: 30,
    leak_type: 'intermittent',
    leak_magnitude: 0.35
  },
  night_flow: {
    name: 'Night Flow Anomaly',
    description: 'Unusual flow during nighttime hours',
    duration_minutes: 480, // 8 hours
    pressure_baseline: 3.0,
    flow_baseline: 5 // Low baseline for night
  }
}

// Generate sensor reading with realistic noise
function generateReading(
  minute: number,
  scenario: SimulationScenario,
  sensorId: string,
  dmaId: string,
  baseTimestamp: Date
): Record<string, any> {
  const timestamp = new Date(baseTimestamp.getTime() + minute * 60000)
  const hour = timestamp.getHours()
  
  // Base values with circadian pattern
  let pressure = scenario.pressure_baseline
  let flowRate = scenario.flow_baseline
  
  // Circadian adjustment (higher usage during day)
  if (hour >= 6 && hour <= 22) {
    const peakHours = [7, 8, 12, 13, 18, 19, 20]
    if (peakHours.includes(hour)) {
      flowRate *= 1.3 + Math.random() * 0.2
      pressure -= 0.1 + Math.random() * 0.1
    } else {
      flowRate *= 1.1 + Math.random() * 0.15
    }
  } else {
    // Night time - minimal flow
    flowRate *= 0.2 + Math.random() * 0.1
    pressure += 0.1 // Pressure higher at night
  }
  
  // Add realistic noise
  pressure += (Math.random() - 0.5) * 0.1
  flowRate += (Math.random() - 0.5) * 5
  
  // Apply leak scenario if applicable
  if (scenario.leak_start_minute !== undefined && 
      minute >= scenario.leak_start_minute && 
      scenario.leak_type && 
      scenario.leak_magnitude) {
    
    const leakMinutes = minute - scenario.leak_start_minute
    const mag = scenario.leak_magnitude
    
    switch (scenario.leak_type) {
      case 'gradual':
        // Gradual pressure drop, gradual flow increase
        const gradualFactor = Math.min(leakMinutes / 60, 1) // Ramps up over an hour
        pressure -= mag * 0.8 * gradualFactor + (Math.random() * 0.05)
        flowRate += scenario.flow_baseline * mag * 0.5 * gradualFactor + (Math.random() * 2)
        break
        
      case 'sudden':
        // Immediate change
        pressure -= mag * 0.6 + (Math.random() * 0.1)
        flowRate += scenario.flow_baseline * mag * 0.7 + (Math.random() * 5)
        break
        
      case 'burst':
        // Large changes
        pressure -= mag * 1.2 + (Math.random() * 0.2)
        flowRate += scenario.flow_baseline * mag * 1.5 + (Math.random() * 20)
        break
        
      case 'intermittent':
        // On/off pattern
        const cyclePos = Math.sin(leakMinutes * 0.1) // ~30 min cycles
        if (cyclePos > 0.3) {
          pressure -= mag * 0.5 * cyclePos + (Math.random() * 0.05)
          flowRate += scenario.flow_baseline * mag * 0.4 * cyclePos + (Math.random() * 2)
        }
        break
    }
  }
  
  // Ensure realistic bounds
  pressure = Math.max(0.5, Math.min(5.0, pressure))
  flowRate = Math.max(0, Math.min(500, flowRate))
  
  // Generate temperature (ambient + friction heat)
  const baseTemp = 20 + (hour >= 10 && hour <= 16 ? 5 : 0) // Warmer during day
  const temperature = baseTemp + flowRate * 0.01 + (Math.random() - 0.5) * 2
  
  // Acoustic level (higher flow = more noise)
  const acousticBase = 30 + flowRate * 0.3
  const acousticLevel = acousticBase + (Math.random() - 0.5) * 5
  
  return {
    sensor_id: sensorId,
    dma_id: dmaId,
    pressure: Math.round(pressure * 100) / 100,
    flow_rate: Math.round(flowRate * 10) / 10,
    temperature: Math.round(temperature * 10) / 10,
    acoustic_level: Math.round(acousticLevel * 10) / 10,
    timestamp: timestamp.toISOString(),
    simulation: true,
    scenario: scenario.name
  }
}

// POST - Run simulation
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { 
      scenario: scenarioKey = 'gradual_leak', 
      sensor_id = 'SIM-001',
      dma_id = 'DMA-001',
      run_detection = true,
      start_time = new Date().toISOString()
    } = body
    
    const scenario = SCENARIOS[scenarioKey]
    if (!scenario) {
      return NextResponse.json({
        success: false,
        error: `Unknown scenario: ${scenarioKey}`,
        available_scenarios: Object.keys(SCENARIOS)
      }, { status: 400 })
    }
    
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const baseTimestamp = new Date(start_time)
    const readings: Record<string, any>[] = []
    
    // Generate readings every minute for the scenario duration
    for (let minute = 0; minute < scenario.duration_minutes; minute++) {
      const reading = generateReading(minute, scenario, sensor_id, dma_id, baseTimestamp)
      readings.push(reading)
    }
    
    // Store all readings
    if (readings.length > 0) {
      await db.collection('sensor_readings').insertMany(readings)
    }
    
    // Run AI detection on each reading if requested
    const detectionResults: any[] = []
    if (run_detection) {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'
      
      // Run detection on last 10 readings (most recent)
      const recentReadings = readings.slice(-10)
      
      for (const reading of recentReadings) {
        try {
          const response = await fetch(`${baseUrl}/api/ai/detect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              sensor_id: reading.sensor_id,
              dma_id: reading.dma_id,
              pressure: reading.pressure,
              flow_rate: reading.flow_rate,
              temperature: reading.temperature,
              acoustic_level: reading.acoustic_level
            })
          })
          
          if (response.ok) {
            const result = await response.json()
            detectionResults.push({
              timestamp: reading.timestamp,
              ...result.result
            })
          }
        } catch (error) {
          console.error('[Simulation] Detection failed for reading:', error)
        }
      }
    }
    
    // Count how many leaks were detected
    const leaksDetected = detectionResults.filter(r => r.is_leak).length
    
    return NextResponse.json({
      success: true,
      scenario: {
        name: scenario.name,
        description: scenario.description,
        duration_minutes: scenario.duration_minutes,
        leak_type: scenario.leak_type || 'none',
        leak_start_minute: scenario.leak_start_minute || 'N/A'
      },
      simulation: {
        readings_generated: readings.length,
        start_time: readings[0]?.timestamp,
        end_time: readings[readings.length - 1]?.timestamp,
        sensor_id,
        dma_id
      },
      detection_summary: run_detection ? {
        readings_analyzed: detectionResults.length,
        leaks_detected: leaksDetected,
        detection_rate: detectionResults.length > 0 
          ? `${Math.round(leaksDetected / detectionResults.length * 100)}%` 
          : 'N/A',
        results: detectionResults
      } : 'Detection not run',
      sample_readings: {
        first: readings[0],
        middle: readings[Math.floor(readings.length / 2)],
        last: readings[readings.length - 1]
      }
    })
    
  } catch (error) {
    console.error('[Simulation] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Simulation failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

// GET - List available scenarios
export async function GET() {
  const scenarios = Object.entries(SCENARIOS).map(([key, value]) => ({
    key,
    name: value.name,
    description: value.description,
    duration_minutes: value.duration_minutes,
    has_leak: !!value.leak_type,
    leak_type: value.leak_type || 'none'
  }))
  
  return NextResponse.json({
    success: true,
    scenarios,
    usage: {
      endpoint: 'POST /api/ai/simulate',
      body: {
        scenario: 'gradual_leak | sudden_leak | burst | intermittent | night_flow | normal',
        sensor_id: 'string (optional, default: SIM-001)',
        dma_id: 'string (optional, default: DMA-001)',
        run_detection: 'boolean (optional, default: true)',
        start_time: 'ISO string (optional, default: now)'
      }
    }
  })
}
