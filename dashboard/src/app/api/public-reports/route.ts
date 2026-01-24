import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'

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

// In-memory store for demo (would use database in production)
const reportsStore: Map<string, PublicReport> = new Map()

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

// Rate limiting (simple in-memory)
const rateLimitStore: Map<string, { count: number; resetAt: number }> = new Map()

function checkRateLimit(ip: string): boolean {
  const now = Date.now()
  const limit = rateLimitStore.get(ip)
  
  if (!limit || now > limit.resetAt) {
    rateLimitStore.set(ip, { count: 1, resetAt: now + 3600000 }) // 1 hour
    return true
  }
  
  if (limit.count >= 5) {
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

    // Generate ticket
    let ticket = generateTicket()
    while (reportsStore.has(ticket)) {
      ticket = generateTicket()
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

    // Store report
    reportsStore.set(ticket, report)

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
  const { searchParams } = new URL(request.url)
  const tenantId = searchParams.get('tenant_id') || 'lwsc-zambia'
  const status = searchParams.get('status')
  const category = searchParams.get('category')
  const page = parseInt(searchParams.get('page') || '1')
  const pageSize = parseInt(searchParams.get('page_size') || '20')

  // Filter reports
  let reports = Array.from(reportsStore.values())
    .filter(r => r.tenant_id === tenantId)

  if (status) {
    reports = reports.filter(r => r.status === status)
  }

  if (category) {
    reports = reports.filter(r => r.category === category)
  }

  // Sort by created_at desc
  reports.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  // Paginate
  const total = reports.length
  const totalPages = Math.ceil(total / pageSize)
  const start = (page - 1) * pageSize
  const paginatedReports = reports.slice(start, start + pageSize)

  return NextResponse.json({
    items: paginatedReports,
    total,
    page,
    page_size: pageSize,
    total_pages: totalPages,
  })
}
