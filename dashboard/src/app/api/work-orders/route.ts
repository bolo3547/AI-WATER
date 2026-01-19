import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase, WorkOrder } from '@/lib/mongodb'

// Initialize database on first request
let initialized = false

async function ensureInitialized() {
  if (!initialized) {
    try {
      await initializeDatabase()
      initialized = true
    } catch (error) {
      console.error('[Work Orders API] Failed to initialize database:', error)
    }
  }
}

// GET - Fetch all work orders from MongoDB
export async function GET(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const assignee = searchParams.get('assignee')
    const dma = searchParams.get('dma')
    
    const collection = await getWorkOrdersCollection()
    
    // Build query filter
    const filter: any = {}
    if (status && status !== 'all') {
      filter.status = status
    }
    if (assignee) {
      filter.assignee = { $regex: assignee, $options: 'i' }
    }
    if (dma) {
      filter.dma = dma
    }
    
    // Fetch from MongoDB, sorted by created_at descending
    const workOrders = await collection
      .find(filter)
      .sort({ created_at: -1 })
      .toArray()
    
    console.log(`[Work Orders API] Fetched ${workOrders.length} work orders from MongoDB`)
    
    return NextResponse.json({
      success: true,
      data: workOrders,
      total: workOrders.length,
      source: 'mongodb',
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('[Work Orders API] Error fetching work orders:', error)
    // Return empty array instead of error - no MongoDB means no work orders
    return NextResponse.json({
      success: true,
      data: [],
      total: 0,
      source: 'fallback',
      message: 'No work orders. Create one to get started.',
      timestamp: new Date().toISOString()
    })
  }
}

// POST - Create new work order in MongoDB
export async function POST(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    
    // Validate required fields
    if (!body.title || !body.dma) {
      return NextResponse.json(
        { success: false, error: 'Title and DMA are required' },
        { status: 400 }
      )
    }
    
    const collection = await getWorkOrdersCollection()
    
    // Generate unique ID
    const year = new Date().getFullYear()
    const count = await collection.countDocuments()
    const newId = `WO-${year}-${String(count + 1).padStart(4, '0')}`
    
    const newWorkOrder: WorkOrder = {
      id: newId,
      title: body.title,
      dma: body.dma,
      priority: body.priority || 'medium',
      status: 'pending',
      assignee: body.assignee || 'Unassigned',
      created_at: new Date().toISOString(),
      due_date: body.due_date || new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
      estimated_loss: body.estimated_loss || 0,
      source: body.source || 'Manual Entry',
      description: body.description || '',
      created_by: body.created_by || 'Admin'
    }
    
    // Insert into MongoDB
    const result = await collection.insertOne(newWorkOrder as any)
    
    console.log(`[Work Orders API] Created work order: ${newId} (MongoDB ID: ${result.insertedId})`)
    
    return NextResponse.json({
      success: true,
      data: { ...newWorkOrder, _id: result.insertedId },
      message: 'Work order created successfully',
      source: 'mongodb'
    }, { status: 201 })
    
  } catch (error) {
    console.error('[Work Orders API] Error creating work order:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to create work order',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

// PUT - Update work order in MongoDB
export async function PUT(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    const { id, ...updates } = body
    
    if (!id) {
      return NextResponse.json(
        { success: false, error: 'Work order ID is required' },
        { status: 400 }
      )
    }
    
    const collection = await getWorkOrdersCollection()
    
    // Prepare update
    const updateData: any = { ...updates }
    
    // Auto-set completed_at if status changed to completed
    if (updates.status === 'completed') {
      updateData.completed_at = new Date().toISOString()
    }
    
    // Update in MongoDB
    const result = await collection.findOneAndUpdate(
      { id: id },
      { $set: updateData },
      { returnDocument: 'after' }
    )
    
    if (!result) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    console.log(`[Work Orders API] Updated work order: ${id}`)
    
    return NextResponse.json({
      success: true,
      data: result,
      message: 'Work order updated successfully',
      source: 'mongodb'
    })
    
  } catch (error) {
    console.error('[Work Orders API] Error updating work order:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to update work order',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}

// DELETE - Delete work order from MongoDB
export async function DELETE(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')
    
    if (!id) {
      return NextResponse.json(
        { success: false, error: 'Work order ID is required' },
        { status: 400 }
      )
    }
    
    const collection = await getWorkOrdersCollection()
    
    // Delete from MongoDB
    const result = await collection.findOneAndDelete({ id: id })
    
    if (!result) {
      return NextResponse.json(
        { success: false, error: 'Work order not found' },
        { status: 404 }
      )
    }
    
    console.log(`[Work Orders API] Deleted work order: ${id}`)
    
    return NextResponse.json({
      success: true,
      data: result,
      message: 'Work order deleted successfully',
      source: 'mongodb'
    })
    
  } catch (error) {
    console.error('[Work Orders API] Error deleting work order:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to delete work order',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}
