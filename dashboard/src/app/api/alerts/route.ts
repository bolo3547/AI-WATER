import { NextRequest, NextResponse } from 'next/server'
import { getAlertsCollection, initializeDatabase, Alert } from '@/lib/mongodb'

// Initialize database on first request
let initialized = false

async function ensureInitialized() {
  if (!initialized) {
    try {
      await initializeDatabase()
      initialized = true
    } catch (error) {
      console.error('[Alerts API] Failed to initialize database:', error)
    }
  }
}

// GET - Fetch all alerts from MongoDB
export async function GET(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const severity = searchParams.get('severity')
    const type = searchParams.get('type')
    
    const collection = await getAlertsCollection()
    
    // Build query filter
    const filter: any = {}
    if (status && status !== 'all') {
      filter.status = status
    }
    if (severity) {
      filter.severity = severity
    }
    if (type) {
      filter.type = type
    }
    
    // Fetch from MongoDB, sorted by created_at descending
    const alerts = await collection
      .find(filter)
      .sort({ created_at: -1 })
      .toArray()
    
    console.log(`[Alerts API] Fetched ${alerts.length} alerts from MongoDB`)
    
    return NextResponse.json({
      success: true,
      data: alerts,
      total: alerts.length,
      source: 'mongodb',
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('[Alerts API] Error fetching alerts:', error)
    // Return mock data as fallback
    const now = new Date()
    return NextResponse.json({
      success: true,
      data: [
        {
          id: "ALERT-001",
          type: "leak",
          severity: "critical",
          title: "Major Leak Detected",
          message: "Potential leak detected in Kabulonga North",
          dma: "Kabulonga North",
          created_at: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString(),
          status: "active"
        },
        {
          id: "ALERT-002",
          type: "pressure",
          severity: "warning",
          title: "Low Pressure Alert",
          message: "Low pressure warning in Roma Industrial",
          dma: "Roma Industrial",
          created_at: new Date(now.getTime() - 5 * 60 * 60 * 1000).toISOString(),
          status: "acknowledged"
        }
      ],
      source: 'fallback'
    })
  }
}

// POST - Create new alert
export async function POST(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    
    const collection = await getAlertsCollection()
    
    // Generate unique ID
    const count = await collection.countDocuments()
    const newId = `alert-${String(count + 1).padStart(3, '0')}`
    
    const newAlert: Alert = {
      id: newId,
      type: body.type || 'system',
      severity: body.severity || 'info',
      title: body.title || 'System Alert',
      message: body.message,
      location: body.location,
      dma: body.dma,
      sensor_id: body.sensor_id,
      created_at: new Date().toISOString(),
      status: 'active'
    }
    
    // Insert into MongoDB
    const result = await collection.insertOne(newAlert as any)
    
    console.log(`[Alerts API] Created alert: ${newId}`)
    
    return NextResponse.json({
      success: true,
      data: { ...newAlert, _id: result.insertedId },
      message: 'Alert created successfully',
      source: 'mongodb'
    }, { status: 201 })
    
  } catch (error) {
    console.error('[Alerts API] Error creating alert:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to create alert'
    }, { status: 500 })
  }
}

// PUT - Update alert (acknowledge/resolve)
export async function PUT(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    const { id, action, user } = body
    
    if (!id || !action) {
      return NextResponse.json(
        { success: false, error: 'Alert ID and action are required' },
        { status: 400 }
      )
    }
    
    const collection = await getAlertsCollection()
    
    let updateData: any = {}
    
    if (action === 'acknowledge') {
      updateData = {
        status: 'acknowledged',
        acknowledged_at: new Date().toISOString(),
        acknowledged_by: user || 'Operator'
      }
    } else if (action === 'resolve') {
      updateData = {
        status: 'resolved',
        resolved_at: new Date().toISOString(),
        resolved_by: user || 'Operator'
      }
    }
    
    // Update in MongoDB
    const result = await collection.findOneAndUpdate(
      { id: id },
      { $set: updateData },
      { returnDocument: 'after' }
    )
    
    if (!result) {
      return NextResponse.json(
        { success: false, error: 'Alert not found' },
        { status: 404 }
      )
    }
    
    console.log(`[Alerts API] Updated alert: ${id} (${action})`)
    
    return NextResponse.json({
      success: true,
      data: result,
      message: `Alert ${action}d successfully`,
      source: 'mongodb'
    })
    
  } catch (error) {
    console.error('[Alerts API] Error updating alert:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to update alert'
    }, { status: 500 })
  }
}
