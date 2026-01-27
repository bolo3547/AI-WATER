import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

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

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    // Find the report by ticket_number (can also try 'ticket' for backwards compatibility)
    let report = await collection.findOne({ ticket_number: cleanTicket })
    
    // Fallback: try 'ticket' field for older records
    if (!report) {
      report = await collection.findOne({ ticket: cleanTicket })
    }

    if (!report) {
      console.log(`[TrackReport] Ticket not found: ${cleanTicket}`)
      return NextResponse.json(
        { error: 'Report not found' },
        { status: 404 }
      )
    }

    console.log(`[TrackReport] Found ticket ${cleanTicket} - status: ${report.status}`)

    // Return tracking data (handle both field names)
    return NextResponse.json({
      ticket: report.ticket_number || report.ticket,
      status: report.status || 'received',
      status_label: STATUS_LABELS[report.status] || report.status || 'Received',
      category: report.category,
      area: report.area_text || report.area || 'Location not specified',
      description: report.description,
      severity: report.severity || 'medium',
      timeline: report.timeline || report.status_history || [],
      created_at: report.created_at,
      last_updated: report.updated_at || report.created_at,
      resolved_at: report.status === 'resolved' ? report.updated_at : null,
    })

  } catch (error) {
    console.error('[TrackReport] Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch report status' },
      { status: 500 }
    )
  }
}
