import { NextRequest, NextResponse } from 'next/server'

// Status labels
const STATUS_LABELS: Record<string, string> = {
  received: 'Report Received',
  under_review: 'Under Review',
  technician_assigned: 'Team Assigned',
  in_progress: 'Work In Progress',
  resolved: 'Issue Resolved',
  closed: 'Case Closed',
}

// Mock data store (shared with main route in real implementation)
// For demo, we'll generate mock responses
function getMockTracking(ticket: string) {
  // Simulate different statuses based on ticket
  const now = new Date()
  const statuses = ['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved']
  const statusIndex = ticket.charCodeAt(ticket.length - 1) % 5
  const currentStatus = statuses[statusIndex]

  const timeline = []
  
  // Build timeline up to current status
  for (let i = 0; i <= statusIndex; i++) {
    const status = statuses[i]
    const timestamp = new Date(now.getTime() - (statusIndex - i) * 3600000) // 1 hour apart
    
    timeline.push({
      status,
      message: getStatusMessage(status),
      timestamp: timestamp.toISOString(),
    })
  }

  return {
    ticket: ticket.toUpperCase(),
    status: currentStatus,
    status_label: STATUS_LABELS[currentStatus],
    category: 'leak',
    area: 'Central Business District',
    timeline,
    created_at: timeline[0].timestamp,
    last_updated: timeline[timeline.length - 1].timestamp,
    resolved_at: currentStatus === 'resolved' ? timeline[timeline.length - 1].timestamp : null,
  }
}

function getStatusMessage(status: string): string {
  const messages: Record<string, string> = {
    received: 'Your report has been received. Thank you for helping improve water services.',
    under_review: 'Your report is being reviewed by our team.',
    technician_assigned: 'A team has been assigned to investigate this issue.',
    in_progress: 'Work is in progress to resolve this issue.',
    resolved: 'The reported issue has been resolved. Thank you for your patience.',
    closed: 'This case has been closed.',
  }
  return messages[status] || 'Status update'
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

    // In production, this would query the database
    // For demo, return mock data
    
    // Simulate not found for certain tickets
    if (cleanTicket.startsWith('XXX')) {
      return NextResponse.json(
        { error: 'Report not found' },
        { status: 404 }
      )
    }

    const trackingData = getMockTracking(cleanTicket)

    return NextResponse.json(trackingData)

  } catch (error) {
    console.error('[TrackReport] Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch report status' },
      { status: 500 }
    )
  }
}
