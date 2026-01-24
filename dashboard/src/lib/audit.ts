/**
 * Audit logging utility for AquaWatch NRW System
 * 
 * Provides centralized audit logging for all system activities.
 */

import clientPromise from '@/lib/mongodb'

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

/**
 * Create an audit log entry
 * 
 * @param action - The action performed (e.g., 'created', 'updated', 'deleted')
 * @param entityType - The type of entity affected
 * @param entityId - The ID of the entity
 * @param userId - The ID of the user performing the action
 * @param userName - The name of the user
 * @param userRole - The role of the user
 * @param details - Additional details about the action
 * @param tenantId - The tenant ID (default: 'default')
 */
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

/**
 * Fetch audit logs with filtering
 */
export async function getAuditLogs(
  options: {
    entity_type?: string
    entity_id?: string
    user_id?: string
    tenant_id?: string
    limit?: number
    offset?: number
  } = {}
): Promise<{ logs: AuditLog[]; total: number }> {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const collection = db.collection<AuditLog>('audit_logs')

    const query: Record<string, unknown> = {}
    if (options.entity_type) query.entity_type = options.entity_type
    if (options.entity_id) query.entity_id = options.entity_id
    if (options.user_id) query.user_id = options.user_id
    if (options.tenant_id) query.tenant_id = options.tenant_id

    const [logs, total] = await Promise.all([
      collection
        .find(query)
        .sort({ timestamp: -1 })
        .skip(options.offset || 0)
        .limit(options.limit || 100)
        .toArray(),
      collection.countDocuments(query)
    ])

    return { logs, total }
  } catch (error) {
    console.error('[Audit] Failed to fetch audit logs:', error)
    return { logs: [], total: 0 }
  }
}
