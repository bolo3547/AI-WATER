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

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    // Find the report by ticket
    const report = await collection.findOne({ ticket: cleanTicket })

    if (!report) {
      return NextResponse.json(
        { error: 'Report not found' },
        { status: 404 }
      )
    }

    // Return tracking data
    return NextResponse.json({
      ticket: report.ticket,
      status: report.status,
      status_label: STATUS_LABELS[report.status] || report.status,
      category: report.category,
      area: report.area_text || 'Location not specified',
      description: report.description,
      severity: report.severity || 'medium',
      timeline: report.timeline || [],
      created_at: report.created_at,
      last_updated: report.updated_at,
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
