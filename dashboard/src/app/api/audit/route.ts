import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

export interface AuditLog {
  _id?: string
  id: string
  timestamp: string
  action: string
  entity_type: 'leak' | 'work_order' | 'user' | 'sensor' | 'dma' | 'system'
  entity_id: string
  user_id: string
  user_name: string
  user_role: string
  tenant_id: string
  details: Record<string, unknown>
  ip_address?: string
  user_agent?: string
}

// GET - Fetch audit logs
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const entity_type = searchParams.get('entity_type')
    const entity_id = searchParams.get('entity_id')
    const user_id = searchParams.get('user_id')
    const limit = parseInt(searchParams.get('limit') || '100')
    const offset = parseInt(searchParams.get('offset') || '0')

    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const collection = db.collection<AuditLog>('audit_logs')

    // Build query
    const query: Record<string, unknown> = {}
    if (entity_type) query.entity_type = entity_type
    if (entity_id) query.entity_id = entity_id
    if (user_id) query.user_id = user_id

    const [logs, total] = await Promise.all([
      collection
        .find(query)
        .sort({ timestamp: -1 })
        .skip(offset)
        .limit(limit)
        .toArray(),
      collection.countDocuments(query)
    ])

    return NextResponse.json({
      success: true,
      data: logs,
      total,
      limit,
      offset,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('[Audit API] Error fetching logs:', error)
    return NextResponse.json({
      success: false,
      data: [],
      error: 'Failed to fetch audit logs'
    }, { status: 500 })
  }
}

// POST - Create audit log entry
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validate required fields
    if (!body.action || !body.entity_type || !body.entity_id) {
      return NextResponse.json(
        { success: false, error: 'action, entity_type, and entity_id are required' },
        { status: 400 }
      )
    }

    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const collection = db.collection<AuditLog>('audit_logs')

    const auditLog: AuditLog = {
      id: `audit-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      action: body.action,
      entity_type: body.entity_type,
      entity_id: body.entity_id,
      user_id: body.user_id || 'system',
      user_name: body.user_name || 'System',
      user_role: body.user_role || 'system',
      tenant_id: body.tenant_id || 'default',
      details: body.details || {},
      ip_address: body.ip_address,
      user_agent: body.user_agent
    }

    await collection.insertOne(auditLog)

    return NextResponse.json({
      success: true,
      data: auditLog,
      message: 'Audit log created'
    })

  } catch (error) {
    console.error('[Audit API] Error creating log:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to create audit log'
    }, { status: 500 })
  }
}

// Helper function to create audit log (for use in other API routes)
export async function createAuditLog(
  action: string,
  entityType: AuditLog['entity_type'],
  entityId: string,
  userId: string,
  userName: string,
  userRole: string,
  details: Record<string, unknown> = {},
  tenantId: string = 'default'
): Promise<void> {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const collection = db.collection<AuditLog>('audit_logs')

    await collection.insertOne({
      id: `audit-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      action,
      entity_type: entityType,
      entity_id: entityId,
      user_id: userId,
      user_name: userName,
      user_role: userRole,
      tenant_id: tenantId,
      details
    })
  } catch (error) {
    console.error('[Audit] Failed to create audit log:', error)
  }
}
