import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

// GET - Fetch shift handover data
export async function GET(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const date = searchParams.get('date')
    const limit = parseInt(searchParams.get('limit') || '20')
    
    // Build query
    const query: Record<string, any> = {}
    if (status && status !== 'all') {
      query.status = status
    }
    if (date) {
      query.date = date
    }
    
    // Fetch shift handovers
    const handovers = await db.collection('shift_handovers')
      .find(query)
      .sort({ date: -1, startTime: -1 })
      .limit(limit)
      .toArray()
    
    // Get current system status for new handover
    const [activeAlerts, activeLeaks, ongoingWorks, sensors] = await Promise.all([
      db.collection('alerts').countDocuments({ status: 'active' }),
      db.collection('leaks').countDocuments({ status: { $in: ['new', 'investigating'] } }),
      db.collection('work_orders').countDocuments({ status: { $in: ['pending', 'in_progress'] } }),
      db.collection('sensors').find({ type: 'pump' }).toArray()
    ])
    
    // Calculate pump status from sensors
    const pumpsOperational = sensors.filter((s: any) => s.status === 'online').length
    const pumpsTotal = sensors.length || 10
    
    return NextResponse.json({
      success: true,
      data: {
        handovers,
        currentSystemStatus: {
          pumpsOperational,
          pumpsTotal,
          activeAlerts,
          activeLeaks,
          ongoingWorks
        }
      }
    })
    
  } catch (error) {
    console.error('[Shift Handover API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch shift handover data'
    }, { status: 500 })
  }
}

// POST - Create or update shift handover
export async function POST(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    const { action } = body
    
    if (action === 'create') {
      // Get current system status
      const [activeAlerts, activeLeaks, ongoingWorks] = await Promise.all([
        db.collection('alerts').countDocuments({ status: 'active' }),
        db.collection('leaks').countDocuments({ status: { $in: ['new', 'investigating'] } }),
        db.collection('work_orders').countDocuments({ status: { $in: ['pending', 'in_progress'] } })
      ])
      
      const handover = {
        id: `SH-${Date.now()}`,
        shiftType: body.shiftType || 'day',
        date: body.date || new Date().toISOString().split('T')[0],
        startTime: body.startTime || (body.shiftType === 'night' ? '18:00' : '06:00'),
        endTime: body.endTime || (body.shiftType === 'night' ? '06:00' : '18:00'),
        outgoingOperator: body.outgoingOperator,
        incomingOperator: null,
        status: 'in-progress',
        systemStatus: {
          pumpsOperational: body.pumpsOperational || 8,
          pumpsTotal: body.pumpsTotal || 10,
          reservoirLevels: body.reservoirLevels || [],
          activeAlerts,
          activeLeaks,
          ongoingWorks
        },
        checklist: body.checklist || [],
        incidents: [],
        notes: '',
        criticalItems: [],
        pendingTasks: [],
        submittedAt: null,
        acknowledgedAt: null,
        createdAt: new Date().toISOString()
      }
      
      await db.collection('shift_handovers').insertOne(handover)
      
      return NextResponse.json({ success: true, handover })
    }
    
    if (action === 'update') {
      const updates: Record<string, any> = {
        updatedAt: new Date().toISOString()
      }
      
      if (body.checklist) updates.checklist = body.checklist
      if (body.incidents) updates.incidents = body.incidents
      if (body.notes !== undefined) updates.notes = body.notes
      if (body.criticalItems) updates.criticalItems = body.criticalItems
      if (body.pendingTasks) updates.pendingTasks = body.pendingTasks
      if (body.systemStatus) updates.systemStatus = body.systemStatus
      
      await db.collection('shift_handovers').updateOne(
        { id: body.id },
        { $set: updates }
      )
      
      return NextResponse.json({ success: true })
    }
    
    if (action === 'submit') {
      await db.collection('shift_handovers').updateOne(
        { id: body.id },
        {
          $set: {
            status: 'pending-review',
            submittedAt: new Date().toISOString(),
            notes: body.notes || '',
            criticalItems: body.criticalItems || [],
            pendingTasks: body.pendingTasks || []
          }
        }
      )
      
      return NextResponse.json({ success: true })
    }
    
    if (action === 'acknowledge') {
      await db.collection('shift_handovers').updateOne(
        { id: body.id },
        {
          $set: {
            status: 'completed',
            incomingOperator: body.incomingOperator,
            acknowledgedAt: new Date().toISOString()
          }
        }
      )
      
      return NextResponse.json({ success: true })
    }
    
    if (action === 'add_incident') {
      const incidentUpdate = {
        $push: {
          incidents: {
            time: body.incident.time || new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
            description: body.incident.description,
            action: body.incident.action,
            resolved: body.incident.resolved || false
          }
        }
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      await db.collection('shift_handovers').updateOne({ id: body.id }, incidentUpdate as any)
      
      return NextResponse.json({ success: true })
    }
    
    return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 })
    
  } catch (error) {
    console.error('[Shift Handover API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to process shift handover'
    }, { status: 500 })
  }
}
