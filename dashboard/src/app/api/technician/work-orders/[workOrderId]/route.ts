import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase } from '@/lib/mongodb'

// =============================================================================
// TECHNICIAN WORK ORDER DETAIL API
// =============================================================================
// Endpoints for single work order operations
// - GET: Fetch single work order
// - PATCH: Update work order fields
// =============================================================================

let initialized = false

async function ensureInitialized() {
  if (!initialized) {
    try {
      await initializeDatabase()
      initialized = true
    } catch (error) {
      console.error('[Technician API] Failed to initialize database:', error)
    }
  }
}

// GET - Fetch single work order
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ workOrderId: string }> }
) {
  try {
    await ensureInitialized()
    
    const { workOrderId } = await params
    
    const collection = await getWorkOrdersCollection()
    const workOrder = await collection.findOne({ id: workOrderId }) as any
    
    if (!workOrder) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    // Map to expected format
    const raw = workOrder as unknown as Record<string, any>

    const mappedOrder = {
      id: raw.id || raw._id?.toString(),
      title: raw.title || 'Work Order',
      type: raw.type || 'inspection',
      description: raw.description || '',
      location: raw.location || raw.address || '',
      dma: raw.dma,
      lat: raw.lat || raw.latitude || -15.4,
      lng: raw.lng || raw.longitude || 28.3,
      priority: raw.priority || 'medium',
      status: raw.status,
      createdAt: raw.created_at || raw.createdAt,
      scheduledDate: raw.scheduled_date || raw.scheduledDate,
      assignedTo: raw.assignee || raw.assigned_to || null,
      assignedToId: raw.assigned_to_id || raw.assignedToId || null,
      assignedTeam: raw.team || raw.assigned_team || null,
      estimatedDuration: raw.estimated_duration || raw.estimatedDuration || 2,
      actualDuration: raw.actual_duration || raw.actualDuration || null,
      materials: raw.materials || [],
      notes: raw.notes || [],
      photos: raw.photos || [],
      customerContact: raw.customer_contact || raw.customerContact || null,
      customerPhone: raw.customer_phone || raw.customerPhone || null,
      leakId: raw.leak_id || raw.leakId || null,
      completedAt: raw.completed_at || raw.completedAt || null,
    }
    
    return NextResponse.json({
      success: true,
      workOrder: mappedOrder,
    })
    
  } catch (error) {
    console.error('[Technician API] Error fetching work order:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch work order' },
      { status: 500 }
    )
  }
}

// PATCH - Update work order
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ workOrderId: string }> }
) {
  try {
    await ensureInitialized()
    
    const { workOrderId } = await params
    const body = await request.json()
    
    const collection = await getWorkOrdersCollection()
    
    // Build update object
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const update: any = {
      updated_at: new Date().toISOString(),
    }
    
    // Allowed fields for technician updates
    const allowedFields = [
      'status',
      'actual_duration',
      'actualDuration',
      'notes',
      'photos',
      'materials',
      'completed_at',
      'completedAt',
    ]
    
    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        update[field] = body[field]
      }
    }
    
    // Track offline sync metadata
    if (body.offline_action_id) {
      update.last_offline_sync = {
        action_id: body.offline_action_id,
        synced_at: new Date().toISOString(),
        offline_created_at: body.offline_created_at,
      }
    }
    
    const result = await collection.updateOne(
      { id: workOrderId },
      { $set: update }
    )
    
    if (result.matchedCount === 0) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    // Fetch updated work order
    const updated = await collection.findOne({ id: workOrderId })
    
    console.log(`[Technician API] Updated work order ${workOrderId}`)
    
    return NextResponse.json({
      success: true,
      message: 'Work order updated',
      workOrder: updated,
    })
    
  } catch (error) {
    console.error('[Technician API] Error updating work order:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to update work order' },
      { status: 500 }
    )
  }
}
