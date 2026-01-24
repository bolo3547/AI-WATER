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
    
    const leakId = params.id
    
    // Try to find by _id (ObjectId) or by id field
    let leak = null
    if (ObjectId.isValid(leakId)) {
      leak = await db.collection('leaks').findOne({ _id: new ObjectId(leakId) })
    }
    if (!leak) {
      leak = await db.collection('leaks').findOne({ id: leakId })
    }
    
    if (!leak) {
      return NextResponse.json({ 
        success: false, 
        error: 'Leak not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      data: leak
    })
  } catch (error) {
    console.error('GET leak by id error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to fetch leak' 
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
    
    const leakId = params.id
    const now = new Date().toISOString()
    
    // Build update object
    const update: Record<string, any> = {}
    
    // Handle action-based updates
    if (body.action) {
      switch (body.action) {
        case 'acknowledge':
          update.status = 'acknowledged'
          update.acknowledged_by = body.user || 'Operator'
          update.acknowledged_at = now
          break
        case 'resolve':
          update.status = 'resolved'
          update.resolved_at = now
          update.resolution_notes = body.notes
          break
        case 'dispatch':
          update.status = 'dispatched'
          update.dispatched_at = now
          update.assigned_to = body.assigned_to
          break
        case 'investigate':
          update.status = 'investigating'
          update.investigation_started_at = now
          break
      }
    }
    
    // Allow direct field updates
    if (body.status) update.status = body.status
    if (body.notes) update.notes = body.notes
    if (body.assigned_to) update.assigned_to = body.assigned_to
    if (body.work_order_id) update.work_order_id = body.work_order_id
    
    update.updated_at = now
    
    // Try to update by _id or id field
    let result = null
    if (ObjectId.isValid(leakId)) {
      result = await db.collection('leaks').findOneAndUpdate(
        { _id: new ObjectId(leakId) },
        { $set: update },
        { returnDocument: 'after' }
      )
    }
    if (!result) {
      result = await db.collection('leaks').findOneAndUpdate(
        { id: leakId },
        { $set: update },
        { returnDocument: 'after' }
      )
    }
    
    if (!result) {
      return NextResponse.json({ 
        success: false, 
        error: 'Leak not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      data: result,
      message: body.action ? `Leak ${body.action}d successfully` : 'Leak updated successfully'
    })
  } catch (error) {
    console.error('PATCH leak error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to update leak' 
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
    
    const leakId = params.id
    
    // Try to delete by _id or id field
    let result = null
    if (ObjectId.isValid(leakId)) {
      result = await db.collection('leaks').deleteOne({ _id: new ObjectId(leakId) })
    }
    if (!result?.deletedCount) {
      result = await db.collection('leaks').deleteOne({ id: leakId })
    }
    
    if (!result?.deletedCount) {
      return NextResponse.json({ 
        success: false, 
        error: 'Leak not found' 
      }, { status: 404 })
    }
    
    return NextResponse.json({
      success: true,
      message: 'Leak deleted successfully'
    })
  } catch (error) {
    console.error('DELETE leak error:', error)
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to delete leak' 
    }, { status: 500 })
  }
}
