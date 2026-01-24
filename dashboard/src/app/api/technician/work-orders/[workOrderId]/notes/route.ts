import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase } from '@/lib/mongodb'

// =============================================================================
// NOTES API
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

// POST - Add note to work order
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ workOrderId: string }> }
) {
  try {
    await ensureInitialized()
    
    const { workOrderId } = await params
    const body = await request.json()
    
    const { note, addedAt, offline_action_id, offline_created_at } = body
    
    if (!note) {
      return NextResponse.json(
        { success: false, error: 'note is required' },
        { status: 400 }
      )
    }
    
    const collection = await getWorkOrdersCollection()
    
    // Get existing work order
    const existing = await collection.findOne({ id: workOrderId })
    
    if (!existing) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    // Format note with timestamp
    const timestamp = addedAt || new Date().toISOString()
    const formattedNote = `[${new Date(timestamp).toLocaleString()}] ${note}`
    
    // Build update
    const existingNotes = existing.notes || []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const update: any = {
      notes: [...existingNotes, formattedNote],
      updated_at: new Date().toISOString(),
    }
    
    // Track offline sync
    if (offline_action_id) {
      update.last_offline_sync = {
        action_id: offline_action_id,
        action_type: 'add_note',
        synced_at: new Date().toISOString(),
        offline_created_at,
      }
    }
    
    await collection.updateOne(
      { id: workOrderId },
      { $set: update }
    )
    
    console.log(`[Technician API] Note added to ${workOrderId}`)
    
    return NextResponse.json({
      success: true,
      message: 'Note added',
      workOrderId,
      note: formattedNote,
    })
    
  } catch (error) {
    console.error('[Technician API] Error adding note:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to add note' },
      { status: 500 }
    )
  }
}
