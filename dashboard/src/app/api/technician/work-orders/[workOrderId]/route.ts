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
    const workOrder = await collection.findOne({ id: workOrderId })
    
    if (!workOrder) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    // Map to expected format
    const mapped = {
      id: workOrder.id,
      title: workOrder.title,
      type: workOrder.type || 'inspection',
      description: workOrder.description || '',
      location: workOrder.location || workOrder.address || '',
      dma: workOrder.dma,
      lat: workOrder.lat || workOrder.latitude || -15.4,
      lng: workOrder.lng || workOrder.longitude || 28.3,
      priority: workOrder.priority || 'medium',
      status: workOrder.status,
      createdAt: workOrder.created_at || workOrder.createdAt,
      scheduledDate: workOrder.scheduled_date || workOrder.scheduledDate,
      assignedTo: workOrder.assignee || workOrder.assigned_to || null,
      assignedToId: workOrder.assigned_to_id || workOrder.assignedToId || null,
      assignedTeam: workOrder.team || workOrder.assigned_team || null,
      estimatedDuration: workOrder.estimated_duration || workOrder.estimatedDuration || 2,
      actualDuration: workOrder.actual_duration || workOrder.actualDuration || null,
      materials: workOrder.materials || [],
      notes: workOrder.notes || [],
      photos: workOrder.photos || [],
      customerContact: workOrder.customer_contact || workOrder.customerContact || null,
      customerPhone: workOrder.customer_phone || workOrder.customerPhone || null,
      leakId: workOrder.leak_id || workOrder.leakId || null,
      completedAt: workOrder.completed_at || workOrder.completedAt || null,
    }
    
    return NextResponse.json({
      success: true,
      workOrder: mapped,
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
