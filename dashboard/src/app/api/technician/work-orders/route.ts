import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'
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
    const mappedOrders = workOrders.map((wo) => {
      const raw = wo as unknown as Record<string, any>

      return {
        id: raw.id || raw._id?.toString(),
        title: raw.title || 'Work Order',
        type: raw.type || 'inspection',
        description: raw.description || '',
        location: raw.location || raw.address || '',
        dma: raw.dma,
        lat: raw.lat || raw.latitude || -15.4,
        lng: raw.lng || raw.longitude || 28.3,
        priority: raw.priority || 'medium',
        status: raw.status,
        createdAt: raw.created_at || raw.createdAt,
        scheduledDate: raw.scheduled_date || raw.scheduledDate || raw.created_at,
        assignedTo: raw.assignee || raw.assigned_to || null,
        assignedToId: raw.assigned_to_id || raw.assignedToId || null,
        assignedTeam: raw.team || raw.assigned_team || null,
        estimatedDuration: raw.estimated_duration || raw.estimatedDuration || 2,
        actualDuration: raw.actual_duration || raw.actualDuration || null,
        materials: raw.materials || [],
        notes: raw.notes || [],
        photos: raw.photos || [],
        customerContact: raw.customer_contact || raw.customerContact || null,
        customerPhone: raw.customer_phone || raw.customerPhone || null,
        leakId: raw.leak_id || raw.leakId || null,
        completedAt: raw.completed_at || raw.completedAt || null,
      }
    })
    
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
