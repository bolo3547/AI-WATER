import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'
import { notifyStaffResponse } from '@/lib/sms'

// GET - Get ticket details by ticket ID (public access)
export async function GET(
  request: NextRequest,
  { params }: { params: { ticketId: string } }
) {
  try {
    const ticketId = params.ticketId

    if (!ticketId) {
      return NextResponse.json(
        { success: false, message: 'Ticket ID is required' },
        { status: 400 }
      )
    }

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const reportsCollection = db.collection('public_reports')
    const messagesCollection = db.collection('ticket_messages')

    // Find the report by ticket number
    const report = await reportsCollection.findOne({ 
      ticket: ticketId.toUpperCase() 
    })

    if (!report) {
      return NextResponse.json(
        { success: false, message: 'Ticket not found' },
        { status: 404 }
      )
    }

    // Get messages for this ticket
    const messages = await messagesCollection
      .find({ ticket_id: ticketId.toUpperCase() })
      .sort({ created_at: 1 })
      .toArray()

    // Format response for the public ticket page
    const response = {
      ticketId: report.ticket,
      status: mapStatus(report.status),
      priority: mapPriority(report.severity),
      reportType: formatCategory(report.category),
      description: report.description || 'No description provided',
      location: report.area_text || formatLocation(report.latitude, report.longitude),
      createdAt: report.created_at,
      updatedAt: report.updated_at,
      assignedTo: report.assigned_to || null,
      estimatedResolution: getEstimatedResolution(report.status, report.severity),
      messages: [
        // System message from timeline
        ...report.timeline.map((entry: any, index: number) => ({
          id: `timeline-${index}`,
          sender: 'team' as const,
          senderName: 'LWSC System',
          content: entry.message,
          timestamp: entry.timestamp,
          read: true
        })),
        // Manual messages
        ...messages.map((msg: any) => ({
          id: msg._id.toString(),
          sender: msg.sender_type === 'staff' ? 'team' as const : 'user' as const,
          senderName: msg.sender_type === 'staff' ? (msg.sender_name || 'LWSC Support') : undefined,
          content: msg.content,
          timestamp: msg.created_at,
          read: msg.read || false
        }))
      ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }

    return NextResponse.json(response)

  } catch (error) {
    console.error('[Ticket] GET Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to fetch ticket' },
      { status: 500 }
    )
  }
}

// POST - Add a message to the ticket
export async function POST(
  request: NextRequest,
  { params }: { params: { ticketId: string } }
) {
  try {
    const ticketId = params.ticketId
    const body = await request.json()

    if (!ticketId) {
      return NextResponse.json(
        { success: false, message: 'Ticket ID is required' },
        { status: 400 }
      )
    }

    if (!body.content || !body.content.trim()) {
      return NextResponse.json(
        { success: false, message: 'Message content is required' },
        { status: 400 }
      )
    }

    // Connect to MongoDB
    const client = await clientPromise
    const db = client.db('lwsc')
    const reportsCollection = db.collection('public_reports')
    const messagesCollection = db.collection('ticket_messages')

    // Verify ticket exists
    const report = await reportsCollection.findOne({ 
      ticket: ticketId.toUpperCase() 
    })

    if (!report) {
      return NextResponse.json(
        { success: false, message: 'Ticket not found' },
        { status: 404 }
      )
    }

    // Check if ticket is closed
    if (report.status === 'closed') {
      return NextResponse.json(
        { success: false, message: 'Cannot add messages to a closed ticket' },
        { status: 400 }
      )
    }

    const now = new Date().toISOString()

    // Create the message
    const message = {
      ticket_id: ticketId.toUpperCase(),
      sender_type: body.sender_type || 'public', // 'public' or 'staff'
      sender_name: body.sender_name || null,
      sender_id: body.sender_id || null,
      content: body.content.trim(),
      created_at: now,
      read: false
    }

    await messagesCollection.insertOne(message)

    // Update the report's updated_at timestamp and add timeline entry
    const timelineEntry = {
      status: report.status,
      message: body.sender_type === 'staff' 
        ? `Staff response: ${body.content.substring(0, 50)}${body.content.length > 50 ? '...' : ''}`
        : 'Customer added a message',
      timestamp: now
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const updateOperation: any = {
      $set: { updated_at: now },
      $push: { timeline: timelineEntry }
    }

    await reportsCollection.updateOne(
      { ticket: ticketId.toUpperCase() },
      updateOperation
    )

    console.log(`[Ticket] Message added to ${ticketId} by ${body.sender_type || 'public'}`)

    // Send SMS notification to customer when staff responds
    if (body.sender_type === 'staff' && report.reporter_phone) {
      try {
        const smsResult = await notifyStaffResponse(
          report.reporter_phone,
          ticketId.toUpperCase()
        )
        if (smsResult.success) {
          console.log(`[Ticket] SMS notification sent to ${report.reporter_phone} for staff response on ${ticketId}`)
        } else {
          console.log(`[Ticket] SMS failed for ${ticketId}: ${smsResult.error || smsResult.status}`)
        }
      } catch (smsError) {
        // Don't fail the message if SMS fails
        console.error(`[Ticket] SMS error for ${ticketId}:`, smsError)
      }
    }

    return NextResponse.json({
      success: true,
      message: 'Message sent successfully',
      sms_sent: body.sender_type === 'staff' && report.reporter_phone ? true : false
    })

  } catch (error) {
    console.error('[Ticket] POST Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to send message' },
      { status: 500 }
    )
  }
}

// Helper functions
function mapStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'received': 'pending',
    'under_review': 'acknowledged',
    'technician_assigned': 'acknowledged',
    'in_progress': 'in-progress',
    'resolved': 'resolved',
    'closed': 'closed'
  }
  return statusMap[status] || status
}

function mapPriority(severity: string): string {
  const priorityMap: Record<string, string> = {
    'critical': 'critical',
    'high': 'high',
    'medium': 'medium',
    'low': 'low'
  }
  return priorityMap[severity] || 'medium'
}

function formatCategory(category: string): string {
  const categoryNames: Record<string, string> = {
    'leak': 'Water Leak',
    'burst': 'Burst Pipe',
    'no_water': 'No Water Supply',
    'low_pressure': 'Low Pressure',
    'illegal_connection': 'Illegal Connection',
    'overflow': 'Overflow/Flooding',
    'contamination': 'Water Contamination',
    'other': 'Other Issue'
  }
  return categoryNames[category] || category
}

function formatLocation(lat: number | null, lng: number | null): string {
  if (lat && lng) {
    return `GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)}`
  }
  return 'Location not specified'
}

function getEstimatedResolution(status: string, severity: string): string | null {
  if (status === 'resolved' || status === 'closed') {
    return null
  }
  
  const estimates: Record<string, string> = {
    'critical': '2-4 hours',
    'high': '4-12 hours',
    'medium': '24-48 hours',
    'low': '2-5 days'
  }
  
  return estimates[severity] || '24-48 hours'
}
