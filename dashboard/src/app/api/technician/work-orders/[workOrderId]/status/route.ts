import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase } from '@/lib/mongodb'

// =============================================================================
// STATUS UPDATE API
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

// PATCH - Update work order status
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ workOrderId: string }> }
) {
  try {
    await ensureInitialized()
    
    const { workOrderId } = await params
    const body = await request.json()
    
    const { newStatus, note, updatedAt, offline_action_id, offline_created_at } = body
    
    if (!newStatus) {
      return NextResponse.json(
        { success: false, error: 'newStatus is required' },
        { status: 400 }
      )
    }
    
    const validStatuses = ['pending', 'assigned', 'in-progress', 'completed', 'cancelled']
    if (!validStatuses.includes(newStatus)) {
      return NextResponse.json(
        { success: false, error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` },
        { status: 400 }
      )
    }
    
    const collection = await getWorkOrdersCollection()
    
    // Build update
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const update: any = {
      status: newStatus,
      updated_at: updatedAt || new Date().toISOString(),
    }
    
    // Add completion timestamp if completing
    if (newStatus === 'completed') {
      update.completed_at = update.updated_at
    }
    
    // Track offline sync
    if (offline_action_id) {
      update.last_offline_sync = {
        action_id: offline_action_id,
        action_type: 'status_update',
        synced_at: new Date().toISOString(),
        offline_created_at,
      }
    }
    
    // If note provided, add it
    if (note) {
      const existing = await collection.findOne({ id: workOrderId })
      const existingNotes = existing?.notes || []
      update.notes = [...existingNotes, `[${new Date().toLocaleString()}] Status → ${newStatus}: ${note}`]
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
    
    console.log(`[Technician API] Status updated for ${workOrderId}: ${newStatus}`)
    
    return NextResponse.json({
      success: true,
      message: `Status updated to ${newStatus}`,
      workOrderId,
      newStatus,
    })
    
  } catch (error) {
    console.error('[Technician API] Error updating status:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to update status' },
      { status: 500 }
    )
  }
}
