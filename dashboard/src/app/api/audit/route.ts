import { NextRequest, NextResponse } from 'next/server'
import { getAuditLogs, createAuditLog as createAuditLogEntry } from '@/lib/audit'

export const dynamic = 'force-dynamic'

// GET - Fetch audit logs
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const entity_type = searchParams.get('entity_type') || undefined
    const entity_id = searchParams.get('entity_id') || undefined
    const user_id = searchParams.get('user_id') || undefined
    const limit = parseInt(searchParams.get('limit') || '100')
    const offset = parseInt(searchParams.get('offset') || '0')

    const { logs, total } = await getAuditLogs({
      entity_type,
      entity_id,
      user_id,
      limit,
      offset
    })

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

    await createAuditLogEntry(
      body.action,
      body.entity_type,
      body.entity_id,
      body.user_id || 'system',
      body.user_name || 'System',
      body.user_role || 'system',
      body.details || {},
      body.tenant_id || 'default'
    )

    return NextResponse.json({
      success: true,
      message: 'Audit log created',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('[Audit API] Error creating log:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to create audit log'
    }, { status: 500 })
  }
}
