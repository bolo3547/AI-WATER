import { NextRequest, NextResponse } from 'next/server'
import { getWorkOrdersCollection, initializeDatabase } from '@/lib/mongodb'

// =============================================================================
// TECHNICIAN WORK ORDERS API
// =============================================================================
// Endpoints for technician mobile experience
// - GET: Fetch work orders assigned to technician
// - All updates require technician authentication
// =============================================================================

// Initialize database on first request
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

// Verify technician role from auth header
function verifyTechnicianRole(request: NextRequest): { 
  valid: boolean
  userId?: string
  error?: string 
} {
  const authHeader = request.headers.get('authorization')
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return { valid: false, error: 'Missing or invalid authorization header' }
  }
  
  // In production, decode JWT and verify role
  // For now, accept any valid token format
  const token = authHeader.substring(7)
  
  if (!token) {
    return { valid: false, error: 'Invalid token' }
  }
  
  // Try to decode user from localStorage data passed in header
  const userHeader = request.headers.get('x-user-id')
  const roleHeader = request.headers.get('x-user-role')
  
  // Allow technician, engineer, admin, operator roles
  const allowedRoles = ['technician', 'engineer', 'admin', 'operator', 'field_technician']
  
  if (roleHeader && !allowedRoles.includes(roleHeader.toLowerCase())) {
    return { valid: false, error: 'Insufficient permissions. Technician role required.' }
  }
  
  return { valid: true, userId: userHeader || 'unknown' }
}

// GET - Fetch work orders assigned to the technician
export async function GET(request: NextRequest) {
  try {
    const auth = verifyTechnicianRole(request)
    if (!auth.valid) {
      return NextResponse.json(
        { success: false, error: auth.error },
        { status: 401 }
      )
    }
    
    await ensureInitialized()
    
    const { searchParams } = new URL(request.url)
    const assignedTo = searchParams.get('assigned_to') || auth.userId
    const status = searchParams.get('status')
    const includeCompleted = searchParams.get('include_completed') === 'true'
    
    const collection = await getWorkOrdersCollection()
    
    // Build query filter
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filter: any = {}
    
    // Filter by assigned technician (case-insensitive partial match)
    if (assignedTo && assignedTo !== 'all') {
      filter.$or = [
        { assignee: { $regex: assignedTo, $options: 'i' } },
        { assigned_to_id: assignedTo },
        { assignedToId: assignedTo },
      ]
    }
    
    // Status filter
    if (status && status !== 'all') {
      filter.status = status
    } else if (!includeCompleted) {
      // By default, exclude completed and cancelled
      filter.status = { $nin: ['completed', 'cancelled'] }
    }
    
    // Fetch from MongoDB
    const workOrders = await collection
      .find(filter)
      .sort({ 
        // Sort by priority then scheduled date
        priority: 1, // critical first
        scheduled_date: 1,
        created_at: -1 
      })
      .toArray()
    
    // Map to expected format
    const mappedOrders = workOrders.map(wo => ({
      id: wo.id,
      title: wo.title,
      type: wo.type || 'inspection',
      description: wo.description || '',
      location: wo.location || wo.address || '',
      dma: wo.dma,
      lat: wo.lat || wo.latitude || -15.4,
      lng: wo.lng || wo.longitude || 28.3,
      priority: wo.priority || 'medium',
      status: wo.status,
      createdAt: wo.created_at || wo.createdAt,
      scheduledDate: wo.scheduled_date || wo.scheduledDate || wo.created_at,
      assignedTo: wo.assignee || wo.assigned_to || null,
      assignedToId: wo.assigned_to_id || wo.assignedToId || null,
      assignedTeam: wo.team || wo.assigned_team || null,
      estimatedDuration: wo.estimated_duration || wo.estimatedDuration || 2,
      actualDuration: wo.actual_duration || wo.actualDuration || null,
      materials: wo.materials || [],
      notes: wo.notes || [],
      photos: wo.photos || [],
      customerContact: wo.customer_contact || wo.customerContact || null,
      customerPhone: wo.customer_phone || wo.customerPhone || null,
      leakId: wo.leak_id || wo.leakId || null,
      completedAt: wo.completed_at || wo.completedAt || null,
    }))
    
    console.log(`[Technician API] Fetched ${mappedOrders.length} work orders for ${assignedTo}`)
    
    return NextResponse.json({
      success: true,
      workOrders: mappedOrders,
      total: mappedOrders.length,
      lastUpdated: new Date().toISOString(),
    })
    
  } catch (error) {
    console.error('[Technician API] Error fetching work orders:', error)
    return NextResponse.json({
      success: true,
      workOrders: [],
      total: 0,
      lastUpdated: new Date().toISOString(),
      message: 'Failed to fetch work orders',
    })
  }
}
