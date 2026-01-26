import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'
import clientPromise from '@/lib/mongodb'

// Types
interface PublicReport {
  id: string
  ticket: string
  tenant_id: string
  category: string
  description: string | null
  latitude: number | null
  longitude: number | null
  area_text: string | null
  source: string
  severity: string
  reporter_name: string | null
  reporter_phone: string | null
  reporter_email: string | null
  reporter_consent: boolean
  status: string
  verification: string
  spam_flag: boolean
  quarantine: boolean
  created_at: string
  updated_at: string
  timeline: TimelineEntry[]
}

interface TimelineEntry {
  status: string
  message: string
  timestamp: string
}

// Status messages
const STATUS_MESSAGES: Record<string, string> = {
  received: 'Your report has been received. Thank you for helping improve water services.',
  under_review: 'Your report is being reviewed by our team.',
  technician_assigned: 'A team has been assigned to investigate this issue.',
  in_progress: 'Work is in progress to resolve this issue.',
  resolved: 'The reported issue has been resolved. Thank you for your patience.',
  closed: 'This case has been closed.',
}

// Generate short ticket ID
function generateTicket(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = 'TKT-'
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// Rate limiting (simple in-memory for edge runtime)
const rateLimitStore: Map<string, { count: number; resetAt: number }> = new Map()

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const limit = rateLimitStore.get(ip)
  
  if (!limit || now > limit.resetAt) {
    rateLimitStore.set(ip, { count: 1, resetAt: now + 3600000 }) // 1 hour
    return true
  }
  
  if (limit.count >= 10) { // Allow 10 reports per hour
    return false
  }
  
  limit.count++
  return true
}

// POST - Create new report
export async function POST(request: NextRequest) {
  try {
    // Rate limiting
    const ip = request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || 'unknown'
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { success: false, message: 'Rate limit exceeded. Please try again later.' },
        { status: 429 }
      )
    }

    const body = await request.json()
    
    // Validate required fields
    if (!body.category) {
      return NextResponse.json(
        { success: false, message: 'Category is required' },
        { status: 400 }
      )
    }
    
    // Valid categories
    const validCategories = ['leak', 'burst', 'no_water', 'low_pressure', 'illegal_connection', 'overflow', 'contamination', 'other']
    if (!validCategories.includes(body.category)) {
      return NextResponse.json(
        { success: false, message: `Invalid category. Must be one of: ${validCategories.join(', ')}` },
        { status: 400 }
      )
    }

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    // Generate unique ticket
    let ticket = generateTicket()
    let attempts = 0
    while (await collection.findOne({ ticket }) && attempts < 10) {
      ticket = generateTicket()
      attempts++
    }

    const now = new Date().toISOString()

    // Create report
    const report: PublicReport = {
      id: uuidv4(),
      ticket,
      tenant_id: body.tenant_id || 'lwsc-zambia',
      category: body.category,
      description: body.description || null,
      latitude: body.latitude || null,
      longitude: body.longitude || null,
      area_text: body.area_text || null,
      source: body.source || 'web',
      severity: body.severity || 'medium',
      reporter_name: body.reporter_name || null,
      reporter_phone: body.reporter_phone || null,
      reporter_email: body.reporter_email || null,
      reporter_consent: body.reporter_consent || false,
      status: 'received',
      verification: 'pending',
      spam_flag: false,
      quarantine: false,
      created_at: now,
      updated_at: now,
      timeline: [
        {
          status: 'received',
          message: STATUS_MESSAGES.received,
          timestamp: now,
        }
      ]
    }

    // Simple spam detection
    if (!body.latitude && !body.longitude && !body.area_text && !body.description) {
      report.spam_flag = true
      report.quarantine = true
    }

    // Store report in MongoDB
    await collection.insertOne(report)

    console.log(`[PublicReport] Created: ${ticket} (category=${body.category}, source=${body.source || 'web'})`)

    return NextResponse.json({
      success: true,
      ticket,
      message: 'Your report has been submitted successfully.',
      tracking_url: `/track/${ticket}`,
    })

  } catch (error) {
    console.error('[PublicReport] Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to submit report. Please try again.' },
      { status: 500 }
    )
  }
}

// GET - List reports (for admin)
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const tenantId = searchParams.get('tenant_id') || 'lwsc-zambia'
    const status = searchParams.get('status')
    const category = searchParams.get('category')
    const page = parseInt(searchParams.get('page') || '1')
    const pageSize = parseInt(searchParams.get('page_size') || '20')

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    // Build query
    const query: Record<string, unknown> = { tenant_id: tenantId }
    
    if (status) {
      query.status = status
    }
    
    if (category) {
      query.category = category
    }

    // Get total count
    const total = await collection.countDocuments(query)

    // Get paginated results
    const reports = await collection
      .find(query)
      .sort({ created_at: -1 })
      .skip((page - 1) * pageSize)
      .limit(pageSize)
      .toArray()

    const totalPages = Math.ceil(total / pageSize)

    return NextResponse.json({
      items: reports,
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    })
  } catch (error) {
    console.error('[PublicReport] GET Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to fetch reports.' },
      { status: 500 }
    )
  }
}
