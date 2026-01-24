import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'
import { ObjectId } from 'mongodb'

export const dynamic = 'force-dynamic'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const workOrderId = params.id
    
    // Try to find by _id (ObjectId) or by id field
    let workOrder = null
    if (ObjectId.isValid(workOrderId)) {
      workOrder = await db.collection('work_orders').findOne({ _id: new ObjectId(workOrderId) })
    }
    if (!workOrder) {
      workOrder = await db.collection('work_orders').findOne({ id: workOrderId })
    }
    
    if (!workOrder) {
      return NextResponse.json({ 
        success: false, 
        error: 'Work order not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      data: workOrder
    })
  } catch (error) {
    console.error('GET work order by id error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to fetch work order' 
    }, { status: 500 })
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    const workOrderId = params.id
    const now = new Date().toISOString()
    
    // Build update object
    const update: Record<string, any> = {}
    
    // Handle action-based updates
    if (body.action) {
      switch (body.action) {
        case 'assign':
          update.status = 'assigned'
          update.assigned_to = body.assigned_to
          update.assigned_crew = body.assigned_crew
          update.assigned_at = now
          break
        case 'start':
          update.status = 'in_progress'
          update.started_at = now
          break
        case 'complete':
          update.status = 'completed'
          update.completed_at = now
          update.actual_duration_hours = body.actual_duration_hours
          update.actual_cost = body.actual_cost
          update.completion_notes = body.notes
          break
        case 'cancel':
          update.status = 'cancelled'
          update.cancelled_at = now
          update.cancellation_reason = body.notes
          break
        case 'pause':
          update.status = 'paused'
          update.paused_at = now
          break
        case 'resume':
          update.status = 'in_progress'
          update.resumed_at = now
          break
      }
    }
    
    // Allow direct field updates
    if (body.status) update.status = body.status
    if (body.assigned_to) update.assigned_to = body.assigned_to
    if (body.assigned_crew) update.assigned_crew = body.assigned_crew
    if (body.notes) update.notes = body.notes
    if (body.priority) update.priority = body.priority
    if (body.scheduled_for) update.scheduled_for = body.scheduled_for
    if (body.estimated_duration_hours) update.estimated_duration_hours = body.estimated_duration_hours
    if (body.materials_used) update.materials_used = body.materials_used
    
    update.updated_at = now
    
    // Try to update by _id or id field
    let result = null
    if (ObjectId.isValid(workOrderId)) {
      result = await db.collection('work_orders').findOneAndUpdate(
        { _id: new ObjectId(workOrderId) },
        { $set: update },
        { returnDocument: 'after' }
      )
    }
    if (!result) {
      result = await db.collection('work_orders').findOneAndUpdate(
        { id: workOrderId },
        { $set: update },
        { returnDocument: 'after' }
      )
    }
    
    if (!result) {
      return NextResponse.json({ 
        success: false, 
        error: 'Work order not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      data: result,
      message: body.action ? `Work order ${body.action}ed successfully` : 'Work order updated successfully'
    })
  } catch (error) {
    console.error('PATCH work order error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to update work order' 
    }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const workOrderId = params.id
    
    // Try to delete by _id or id field
    let result = null
    if (ObjectId.isValid(workOrderId)) {
      result = await db.collection('work_orders').deleteOne({ _id: new ObjectId(workOrderId) })
    }
    if (!result?.deletedCount) {
      result = await db.collection('work_orders').deleteOne({ id: workOrderId })
    }
    
    if (!result?.deletedCount) {
      return NextResponse.json({ 
        success: false, 
        error: 'Work order not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      message: 'Work order deleted successfully'
    })
  } catch (error) {
    console.error('DELETE work order error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to delete work order' 
    }, { status: 500 })
  }
}
