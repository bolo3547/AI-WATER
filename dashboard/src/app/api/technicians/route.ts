import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const skill = searchParams.get('skill')
    
    // Build query
    const query: Record<string, any> = { role: { $in: ['technician', 'engineer', 'field_crew'] } }
    if (status) query.status = status
    if (skill) query.skills = { $in: [skill] }
    
    // First try users collection
    let technicians = await db.collection('users')
      .find(query)
      .project({
        password: 0,
        password_hash: 0
      })
      .toArray()
    
    // If no technicians in users, check technicians collection
    if (technicians.length === 0) {
      const techQuery: Record<string, any> = {}
      if (status) techQuery.status = status
      if (skill) techQuery.skills = { $in: [skill] }
      
      technicians = await db.collection('technicians').find(techQuery).toArray()
    }
    
    // Get current work order assignments
    const workOrders = await db.collection('work_orders')
      .find({ status: { $in: ['assigned', 'in_progress'] } })
      .project({ assigned_to: 1, id: 1 })
      .toArray()
    
    const assignmentMap = new Map()
    workOrders.forEach(wo => {
      if (wo.assigned_to) {
        assignmentMap.set(wo.assigned_to, wo.id)
      }
    })
    
    // Enrich technicians with assignment info
    const enrichedTechnicians = technicians.map(tech => ({
      _id: tech._id,
      user_id: tech.user_id || tech._id.toString(),
      name: tech.name || tech.username || 'Unknown',
      email: tech.email || '',
      phone: tech.phone || '',
      role: tech.role || 'technician',
      status: assignmentMap.has(tech.name) ? 'busy' : (tech.status || 'available'),
      skills: tech.skills || ['general_maintenance'],
      current_work_order: assignmentMap.get(tech.name) || null,
      completed_today: tech.completed_today || 0,
      location: tech.location || null
    }))

    // If no technicians found, provide demo data
    if (enrichedTechnicians.length === 0) {
      const demoTechnicians = [
        {
          _id: 'demo-1',
          user_id: 'TECH-001',
          name: 'Bwalya Mulenga',
          phone: '+260 971 234 567',
          role: 'senior_technician',
          status: 'available',
          skills: ['leak_detection', 'pipe_repair', 'pressure_systems'],
          current_work_order: null,
          completed_today: 3,
          location: 'Lusaka Central'
        },
        {
          _id: 'demo-2',
          user_id: 'TECH-002',
          name: 'Chanda Mutale',
          phone: '+260 965 432 109',
          role: 'technician',
          status: 'available',
          skills: ['general_maintenance', 'meter_reading'],
          current_work_order: null,
          completed_today: 2,
          location: 'Woodlands'
        },
        {
          _id: 'demo-3',
          user_id: 'TECH-003',
          name: 'Musonda Banda',
          phone: '+260 977 654 321',
          role: 'field_crew',
          status: 'busy',
          skills: ['excavation', 'pipe_installation'],
          current_work_order: 'WO-2024-001',
          completed_today: 1,
          location: 'Matero'
        },
        {
          _id: 'demo-4',
          user_id: 'TECH-004',
          name: 'Chilufya Tembo',
          phone: '+260 968 111 222',
          role: 'engineer',
          status: 'available',
          skills: ['water_quality', 'system_design', 'pressure_management'],
          current_work_order: null,
          completed_today: 0,
          location: 'Head Office'
        }
      ]
      
      return NextResponse.json({
        success: true,
        technicians: demoTechnicians,
        total: demoTechnicians.length,
        hasData: true,
        isDemo: true
      })
    }
    
    return NextResponse.json({
      success: true,
      technicians: enrichedTechnicians,
      total: enrichedTechnicians.length,
      hasData: enrichedTechnicians.length > 0
    })
  } catch (error) {
    console.error('GET technicians error:', error)
    
    // Return empty state, not error
    return NextResponse.json({
      success: true,
      technicians: [],
      total: 0,
      hasData: false,
      message: 'No technicians found. Add team members in Admin settings.'
    })
  }
}

export async function POST(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    if (!body.name) {
      return NextResponse.json({
        success: false,
        error: 'Name is required'
      }, { status: 400 })
    }
    
    // Generate unique ID
    const techId = `TECH-${Date.now()}-${Math.random().toString(36).substring(2, 7).toUpperCase()}`
    
    const newTechnician = {
      user_id: techId,
      name: body.name,
      email: body.email || '',
      phone: body.phone || '',
      role: body.role || 'technician',
      status: 'available',
      skills: body.skills || ['general_maintenance'],
      location: body.location || '',
      completed_today: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    
    const result = await db.collection('technicians').insertOne(newTechnician)
    
    console.log(`[Technicians] Added new team member: ${body.name} (${techId})`)
    
    return NextResponse.json({
      success: true,
      data: { ...newTechnician, _id: result.insertedId },
      message: 'Team member added successfully'
    }, { status: 201 })
  } catch (error) {
    console.error('POST technician error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to add team member'
    }, { status: 500 })
  }
}

// PUT - Update a team member
export async function PUT(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    if (!body.user_id && !body._id) {
      return NextResponse.json({
        success: false,
        error: 'Team member ID is required'
      }, { status: 400 })
    }
    
    const filter = body._id 
      ? { _id: new (await import('mongodb')).ObjectId(body._id) }
      : { user_id: body.user_id }
    
    const updateData: Record<string, any> = {
      updated_at: new Date().toISOString()
    }
    
    // Only update provided fields
    if (body.name) updateData.name = body.name
    if (body.email !== undefined) updateData.email = body.email
    if (body.phone !== undefined) updateData.phone = body.phone
    if (body.role) updateData.role = body.role
    if (body.status) updateData.status = body.status
    if (body.skills) updateData.skills = body.skills
    if (body.location !== undefined) updateData.location = body.location
    
    const result = await db.collection('technicians').updateOne(
      filter,
      { $set: updateData }
    )
    
    if (result.matchedCount === 0) {
      return NextResponse.json({
        success: false,
        error: 'Team member not found'
      }, { status: 404 })
    }
    
    console.log(`[Technicians] Updated team member: ${body.user_id || body._id}`)
    
    return NextResponse.json({
      success: true,
      message: 'Team member updated successfully'
    })
  } catch (error) {
    console.error('PUT technician error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to update team member'
    }, { status: 500 })
  }
}

// DELETE - Remove a team member
export async function DELETE(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id')
    const id = searchParams.get('id')
    
    if (!userId && !id) {
      return NextResponse.json({
        success: false,
        error: 'Team member ID is required'
      }, { status: 400 })
    }
    
    let filter: Record<string, any>
    if (id) {
      const { ObjectId } = await import('mongodb')
      filter = { _id: new ObjectId(id) }
    } else {
      filter = { user_id: userId }
    }
    
    const result = await db.collection('technicians').deleteOne(filter)
    
    if (result.deletedCount === 0) {
      return NextResponse.json({
        success: false,
        error: 'Team member not found'
      }, { status: 404 })
    }
    
    console.log(`[Technicians] Deleted team member: ${userId || id}`)
    
    return NextResponse.json({
      success: true,
      message: 'Team member removed successfully'
    })
  } catch (error) {
    console.error('DELETE technician error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to remove team member'
    }, { status: 500 })
  }
}
