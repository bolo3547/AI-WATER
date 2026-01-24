// =============================================================================
// AUTONOMOUS OPERATIONS - REAL-TIME STREAM
// =============================================================================
// Server-Sent Events (SSE) for real-time autonomous system updates
// Pushes valve changes, AI decisions, and incidents as they happen
// =============================================================================

import { NextRequest } from 'next/server'

// Force dynamic rendering for SSE
export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

// Store for connected clients and system state
let decisionCounter = 0
let lastIncidentTime = Date.now()

// AI Decision generator - simulates real autonomous decisions
function generateAutonomousDecision(): any {
  const decisionTypes = [
    {
      type: 'pressure_adjust',
      templates: [
        { action: 'Reduce PRV-{id} to {percent}%', reason: 'Night-time pressure optimization to reduce background losses' },
        { action: 'Increase PRV-{id} to {percent}%', reason: 'Peak demand detected, increasing pressure to maintain service' },
      ]
    },
    {
      type: 'valve_control',
      templates: [
        { action: 'Throttle VLV-{id} to {percent}%', reason: 'Flow balancing across network segments' },
        { action: 'Open VLV-{id} fully', reason: 'Demand spike in downstream DMA' },
      ]
    },
    {
      type: 'alert',
      templates: [
        { action: 'Generate maintenance alert for VLV-{id}', reason: 'Actuator response time degraded by {percent}%' },
        { action: 'Flag anomaly in SEG-{id}', reason: 'Flow imbalance detected: {percent}% deviation from baseline' },
      ]
    },
    {
      type: 'reroute',
      templates: [
        { action: 'Activate bypass route via VLV-{id}', reason: 'Compensating for reduced capacity in adjacent segment' },
      ]
    }
  ]
  
  const dmas = ['Kabulonga', 'Roma', 'Chelstone', 'Matero', 'Woodlands', 'Chilenje', 'Kalingalinga', 'Emmasdale']
  const typeConfig = decisionTypes[Math.floor(Math.random() * decisionTypes.length)]
  const template = typeConfig.templates[Math.floor(Math.random() * typeConfig.templates.length)]
  
  const id = String(Math.floor(Math.random() * 8) + 1).padStart(3, '0')
  const percent = Math.floor(Math.random() * 50) + 30
  
  return {
    id: `DEC-${Date.now()}-${++decisionCounter}`,
    timestamp: new Date().toISOString(),
    type: typeConfig.type,
    action: template.action.replace('{id}', id).replace('{percent}', String(percent)),
    reason: template.reason.replace('{id}', id).replace('{percent}', String(percent)),
    affectedArea: dmas[Math.floor(Math.random() * dmas.length)],
    status: 'executed',
    confidence: 85 + Math.random() * 15,
    triggeredBy: 'Autonomous AI Engine',
    executedAt: new Date().toISOString(),
    waterSaved: typeConfig.type === 'pressure_adjust' ? Math.floor(Math.random() * 50) : 0,
    customersAffected: Math.floor(Math.random() * 500),
    riskScore: Math.random() * 0.2
  }
}

// Valve state change generator
function generateValveUpdate(): any {
  const valveIds = ['VLV-001', 'VLV-002', 'VLV-003', 'VLV-004', 'VLV-005', 'VLV-006', 'VLV-007', 'VLV-008']
  const valveId = valveIds[Math.floor(Math.random() * valveIds.length)]
  
  // Small random changes to simulate real-time adjustments
  const pressureChange = (Math.random() - 0.5) * 0.2
  const flowChange = (Math.random() - 0.5) * 20
  
  return {
    id: valveId,
    pressure: Math.max(0, 3.5 + pressureChange).toFixed(1),
    flow: Math.max(0, Math.floor(400 + flowChange)),
    updatedAt: new Date().toISOString()
  }
}

// Segment state change generator
function generateSegmentUpdate(): any {
  const segmentIds = ['SEG-001', 'SEG-002', 'SEG-003', 'SEG-004', 'SEG-005', 'SEG-006']
  const segmentId = segmentIds[Math.floor(Math.random() * segmentIds.length)]
  
  const flowInChange = Math.floor((Math.random() - 0.5) * 30)
  const flowOutChange = Math.floor((Math.random() - 0.5) * 25)
  
  return {
    id: segmentId,
    flowIn: Math.max(0, 500 + flowInChange),
    flowOut: Math.max(0, 480 + flowOutChange),
    pressure: (3.5 + (Math.random() - 0.5) * 0.3).toFixed(1),
    updatedAt: new Date().toISOString()
  }
}

// Incident generator (rare events)
function maybeGenerateIncident(): any | null {
  // Only generate incident every 60+ seconds, with low probability
  if (Date.now() - lastIncidentTime < 60000) return null
  if (Math.random() > 0.1) return null // 10% chance per check
  
  lastIncidentTime = Date.now()
  
  const incidentTypes = [
    { type: 'leak_detected', severity: 'high', message: 'Potential leak detected via acoustic correlation' },
    { type: 'pressure_drop', severity: 'medium', message: 'Sudden pressure drop detected' },
    { type: 'high_night_flow', severity: 'medium', message: 'Elevated minimum night flow' },
    { type: 'valve_fault', severity: 'low', message: 'Valve actuator communication intermittent' }
  ]
  
  const dmas = ['Kabulonga', 'Roma', 'Chelstone', 'Matero', 'Woodlands', 'Chilenje']
  const incident = incidentTypes[Math.floor(Math.random() * incidentTypes.length)]
  
  return {
    id: `INC-${Date.now()}`,
    timestamp: new Date().toISOString(),
    type: incident.type,
    severity: incident.severity,
    message: incident.message,
    location: dmas[Math.floor(Math.random() * dmas.length)],
    autoResponseTriggered: true
  }
}

export async function GET(request: NextRequest) {
  const encoder = new TextEncoder()
  
  const stream = new ReadableStream({
    start(controller) {
      // Send initial connection message
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({
        type: 'connected',
        message: 'Connected to Autonomous Operations stream',
        timestamp: new Date().toISOString()
      })}\n\n`))
      
      // Periodic updates
      const intervals: NodeJS.Timeout[] = []
      
      // AI Decisions every 15-30 seconds
      intervals.push(setInterval(() => {
        const decision = generateAutonomousDecision()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'decision',
          data: decision
        })}\n\n`))
      }, 15000 + Math.random() * 15000))
      
      // Valve updates every 3-5 seconds
      intervals.push(setInterval(() => {
        const update = generateValveUpdate()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'valve_update',
          data: update
        })}\n\n`))
      }, 3000 + Math.random() * 2000))
      
      // Segment updates every 5-8 seconds
      intervals.push(setInterval(() => {
        const update = generateSegmentUpdate()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'segment_update',
          data: update
        })}\n\n`))
      }, 5000 + Math.random() * 3000))
      
      // Incident checks every 10 seconds
      intervals.push(setInterval(() => {
        const incident = maybeGenerateIncident()
        if (incident) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({
            type: 'incident',
            data: incident
          })}\n\n`))
        }
      }, 10000))
      
      // Heartbeat every 30 seconds
      intervals.push(setInterval(() => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString()
        })}\n\n`))
      }, 30000))
      
      // Cleanup on close
      request.signal.addEventListener('abort', () => {
        intervals.forEach(clearInterval)
        controller.close()
      })
    }
  })
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
