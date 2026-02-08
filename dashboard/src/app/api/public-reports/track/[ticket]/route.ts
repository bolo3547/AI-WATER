import { NextRequest, NextResponse } from 'next/server'
import { inMemoryReports, getMongoCollection } from '@/lib/report-store'

// Status labels
const STATUS_LABELS: Record<string, string> = {
  received: 'Report Received',
  under_review: 'Under Review',
  technician_assigned: 'Team Assigned',
  in_progress: 'Work In Progress',
  resolved: 'Issue Resolved',
  closed: 'Case Closed',
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ ticket: string }> }
) {
  try {
    const { ticket } = await params
    
    if (!ticket || ticket.length < 6) {
      return NextResponse.json(
        { error: 'Invalid ticket format' },
        { status: 400 }
      )
    }

    const cleanTicket = ticket.toUpperCase()
    console.log(`[TrackReport] Looking up ticket: ${cleanTicket}`)

    // Try MongoDB first
    const collection = await getMongoCollection()
    let report: Record<string, unknown> | null = null

    if (collection) {
      // Find the report by ticket_number (can also try 'ticket' for backwards compatibility)
      report = await collection.findOne({ ticket_number: cleanTicket })
      
      // Fallback: try 'ticket' field for older records
      if (!report) {
        report = await collection.findOne({ ticket: cleanTicket })
      }
    }

    // Fallback: check in-memory store
    if (!report) {
      const memReport = inMemoryReports.get(cleanTicket)
      if (memReport) {
        report = memReport as unknown as Record<string, unknown>
      }
    }

    if (!report) {
      console.log(`[TrackReport] Ticket not found: ${cleanTicket}`)
      return NextResponse.json(
        { error: 'Report not found' },
        { status: 404 }
      )
    }

    console.log(`[TrackReport] Found ticket ${cleanTicket} - status: ${report.status}`)

    const status = (report.status as string) || 'received'

    // Return tracking data (handle both field names)
    return NextResponse.json({
      ticket: (report.ticket_number as string) || (report.ticket as string),
      status,
      status_label: STATUS_LABELS[status] || status,
      category: report.category,
      area: (report.area_text as string) || (report.area as string) || 'Location not specified',
      description: report.description,
      severity: report.severity || 'medium',
      timeline: report.timeline || report.status_history || [],
      created_at: report.created_at,
      last_updated: report.updated_at || report.created_at,
      resolved_at: status === 'resolved' ? report.updated_at : null,
    })

  } catch (error) {
    console.error('[TrackReport] Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch report status' },
      { status: 500 }
    )
  }
}
