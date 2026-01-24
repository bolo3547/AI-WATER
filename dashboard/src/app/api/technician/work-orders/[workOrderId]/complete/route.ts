import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase } from '@/lib/mongodb'

// =============================================================================
// COMPLETE WORK ORDER API
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

// POST - Complete work order
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ workOrderId: string }> }
) {
  try {
    await ensureInitialized()
    
    const { workOrderId } = await params
    const body = await request.json()
    
    const { 
      actualDuration, 
      completionNote, 
      completedAt,
      offline_action_id, 
      offline_created_at 
    } = body
    
    const collection = await getWorkOrdersCollection()
    
    // Get existing work order
    const existing = await collection.findOne({ id: workOrderId })
    
    if (!existing) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    const now = completedAt || new Date().toISOString()
    
    // Build update
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const update: any = {
      status: 'completed',
      completed_at: now,
      updated_at: now,
    }
    
    if (actualDuration !== undefined) {
      update.actual_duration = actualDuration
      update.actualDuration = actualDuration
    }
    
    // Add completion note if provided
    if (completionNote) {
      const existingNotes = existing.notes || []
      update.notes = [
        ...existingNotes, 
        `[${new Date(now).toLocaleString()}] ✅ COMPLETED: ${completionNote}`
      ]
    }
    
    // Track offline sync
    if (offline_action_id) {
      update.last_offline_sync = {
        action_id: offline_action_id,
        action_type: 'complete_order',
        synced_at: new Date().toISOString(),
        offline_created_at,
      }
    }
    
    await collection.updateOne(
      { id: workOrderId },
      { $set: update }
    )
    
    console.log(`[Technician API] Work order completed: ${workOrderId}`)
    
    return NextResponse.json({
      success: true,
      message: 'Work order completed',
      workOrderId,
      completedAt: now,
      actualDuration,
    })
    
  } catch (error) {
    console.error('[Technician API] Error completing work order:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to complete work order' },
      { status: 500 }
    )
  }
}
