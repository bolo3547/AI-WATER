import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

// GET - Fetch security data (API keys, sessions, audit logs)
export async function GET(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { searchParams } = new URL(request.url)
    const type = searchParams.get('type') || 'all'
    const limit = parseInt(searchParams.get('limit') || '50')
    
    const result: Record<string, any> = {}
    
    // API Keys
    if (type === 'all' || type === 'apikeys') {
      const apiKeys = await db.collection('api_keys')
        .find({})
        .sort({ createdAt: -1 })
        .limit(20)
        .toArray()
      result.apiKeys = apiKeys
    }
    
    // Active Sessions
    if (type === 'all' || type === 'sessions') {
      const sessions = await db.collection('active_sessions')
        .find({})
        .sort({ lastActivity: -1 })
        .limit(20)
        .toArray()
      result.sessions = sessions
    }
    
    // Audit Logs
    if (type === 'all' || type === 'audit') {
      const auditLogs = await db.collection('audit_logs')
        .find({})
        .sort({ timestamp: -1 })
        .limit(limit)
        .toArray()
      result.auditLogs = auditLogs
    }
    
    // Security Settings
    if (type === 'all' || type === 'settings') {
      const settings = await db.collection('security_settings').findOne({ type: 'main' })
      result.settings = settings || {
        sessionTimeout: 30,
        maxFailedAttempts: 5,
        lockoutDuration: 15,
        requireTwoFactor: false,
        passwordMinLength: 8,
        requireUppercase: true,
        requireNumbers: true,
        requireSpecialChars: false,
        passwordExpiry: 90,
        ipWhitelist: [],
        alertOnFailedLogin: true,
        alertOnNewDevice: true
      }
    }
    
    // Security Statistics
    const now = new Date()
    const today = new Date(now.setHours(0, 0, 0, 0))
    const thisWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    
    const [totalApiKeys, activeApiKeys, failedLogins, activeSessions] = await Promise.all([
      db.collection('api_keys').countDocuments(),
      db.collection('api_keys').countDocuments({ status: 'active' }),
      db.collection('audit_logs').countDocuments({ 
        action: 'login_failed',
        timestamp: { $gte: today.toISOString() }
      }),
      db.collection('active_sessions').countDocuments()
    ])
    
    result.stats = {
      totalApiKeys,
      activeApiKeys,
      failedLoginsToday: failedLogins,
      activeSessions
    }
    
    return NextResponse.json({
      success: true,
      data: result
    })
    
  } catch (error) {
    console.error('[Security API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch security data'
    }, { status: 500 })
  }
}

// POST - Security actions
export async function POST(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    const { action } = body
    
    // Generate API Key
    if (action === 'generate_api_key') {
      const keyString = `aqw_sk_live_${generateRandomString(20)}`
      
      const apiKey = {
        id: `key-${Date.now()}`,
        name: body.name,
        key: keyString,
        status: 'active',
        createdAt: new Date().toISOString(),
        lastUsed: null,
        permissions: body.permissions || ['read'],
        usageCount: 0
      }
      
      await db.collection('api_keys').insertOne(apiKey)
      
      // Log audit event
      await logAuditEvent(db, {
        user: body.user || 'System',
        role: 'admin',
        action: 'api_key_created',
        resource: apiKey.name,
        status: 'success',
        details: `New API key created: ${apiKey.name}`
      })
      
      return NextResponse.json({ success: true, apiKey })
    }
    
    // Revoke API Key
    if (action === 'revoke_api_key') {
      await db.collection('api_keys').updateOne(
        { id: body.keyId },
        { $set: { status: 'revoked' } }
      )
      
      await logAuditEvent(db, {
        user: body.user || 'System',
        role: 'admin',
        action: 'api_key_revoked',
        resource: body.keyId,
        status: 'success'
      })
      
      return NextResponse.json({ success: true })
    }
    
    // Terminate Session
    if (action === 'terminate_session') {
      await db.collection('active_sessions').deleteOne({ id: body.sessionId })
      
      await logAuditEvent(db, {
        user: body.user || 'System',
        role: 'admin',
        action: 'session_terminated',
        resource: body.sessionId,
        status: 'success'
      })
      
      return NextResponse.json({ success: true })
    }
    
    // Update Security Settings
    if (action === 'update_settings') {
      await db.collection('security_settings').updateOne(
        { type: 'main' },
        { 
          $set: {
            ...body.settings,
            updatedAt: new Date().toISOString()
          }
        },
        { upsert: true }
      )
      
      await logAuditEvent(db, {
        user: body.user || 'System',
        role: 'admin',
        action: 'security_settings_updated',
        resource: 'security_settings',
        status: 'success'
      })
      
      return NextResponse.json({ success: true })
    }
    
    // Log Login Event
    if (action === 'log_login') {
      await logAuditEvent(db, {
        user: body.user,
        role: body.role || 'user',
        action: body.success ? 'login_success' : 'login_failed',
        resource: 'authentication',
        status: body.success ? 'success' : 'failed',
        ip: body.ip || 'Unknown',
        device: body.device || 'Unknown',
        details: body.details
      })
      
      // Create session if successful
      if (body.success) {
        const session = {
          id: `sess-${Date.now()}`,
          user: body.user,
          role: body.role || 'user',
          device: body.device || 'Unknown',
          browser: body.browser || 'Unknown',
          ip: body.ip || 'Unknown',
          location: body.location || 'Unknown',
          loginTime: new Date().toISOString(),
          lastActivity: new Date().toISOString(),
          current: true
        }
        
        await db.collection('active_sessions').insertOne(session)
      }
      
      return NextResponse.json({ success: true })
    }
    
    return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 })
    
  } catch (error) {
    console.error('[Security API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to process security action'
    }, { status: 500 })
  }
}

// Helper function to generate random string
function generateRandomString(length: number): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// Helper function to log audit events
async function logAuditEvent(db: any, event: {
  user: string
  role: string
  action: string
  resource: string
  status: 'success' | 'failed' | 'warning'
  ip?: string
  device?: string
  details?: string
}) {
  await db.collection('audit_logs').insertOne({
    id: `audit-${Date.now()}`,
    ...event,
    ip: event.ip || '127.0.0.1',
    location: 'Lusaka, ZM',
    device: event.device || 'Web Browser',
    timestamp: new Date().toISOString()
  })
}
