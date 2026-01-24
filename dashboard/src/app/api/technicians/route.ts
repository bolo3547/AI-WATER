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
    
    if (!body.name || !body.email) {
      return NextResponse.json({
        success: false,
        error: 'Name and email are required'
      }, { status: 400 })
    }
    
    const newTechnician = {
      user_id: `TECH-${Date.now()}`,
      name: body.name,
      email: body.email,
      phone: body.phone || '',
      role: body.role || 'technician',
      status: 'available',
      skills: body.skills || ['general_maintenance'],
      completed_today: 0,
      created_at: new Date().toISOString()
    }
    
    const result = await db.collection('technicians').insertOne(newTechnician)
    
    return NextResponse.json({
      success: true,
      data: { ...newTechnician, _id: result.insertedId },
      message: 'Technician added successfully'
    }, { status: 201 })
  } catch (error) {
    console.error('POST technician error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to add technician'
    }, { status: 500 })
  }
}
