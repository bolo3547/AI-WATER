import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'
import { notifyReportStatusChange } from '@/lib/sms'

// Status messages for timeline
const STATUS_MESSAGES: Record<string, string> = {
  received: 'Your report has been received. Thank you for helping improve water services.',
  under_review: 'Your report is being reviewed by our team.',
  technician_assigned: 'A team has been assigned to investigate this issue.',
  in_progress: 'Work is in progress to resolve this issue.',
  resolved: 'The reported issue has been resolved. Thank you for your patience.',
  closed: 'This case has been closed.',
}

// GET - Get a single report by ticket number
export async function GET(
  request: NextRequest,
  { params }: { params: { ticket: string } }
) {
  try {
    const ticket = params.ticket?.toUpperCase()

    if (!ticket) {
      return NextResponse.json(
        { success: false, message: 'Ticket number is required' },
        { status: 400 }
      )
    }

    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    const report = await collection.findOne({ ticket })

    if (!report) {
      return NextResponse.json(
        { success: false, message: 'Report not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(report)

  } catch (error) {
    console.error('[PublicReport] GET Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to fetch report' },
      { status: 500 }
    )
  }
}

// PATCH - Update report status
export async function PATCH(
  request: NextRequest,
  { params }: { params: { ticket: string } }
) {
  try {
    const ticket = params.ticket?.toUpperCase()
    const body = await request.json()

    if (!ticket) {
      return NextResponse.json(
        { success: false, message: 'Ticket number is required' },
        { status: 400 }
      )
    }

    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    // Find the report
    const report = await collection.findOne({ ticket })

    if (!report) {
      return NextResponse.json(
        { success: false, message: 'Report not found' },
        { status: 404 }
      )
    }

    const now = new Date().toISOString()
    const updates: Record<string, unknown> = {
      updated_at: now
    }

    // Update status if provided
    if (body.status) {
      const validStatuses = ['received', 'under_review', 'technician_assigned', 'in_progress', 'resolved', 'closed']
      if (!validStatuses.includes(body.status)) {
        return NextResponse.json(
          { success: false, message: `Invalid status. Must be one of: ${validStatuses.join(', ')}` },
          { status: 400 }
        )
      }
      updates.status = body.status
    }

    // Update severity if provided
    if (body.severity) {
      const validSeverities = ['low', 'medium', 'high', 'critical']
      if (!validSeverities.includes(body.severity)) {
        return NextResponse.json(
          { success: false, message: `Invalid severity. Must be one of: ${validSeverities.join(', ')}` },
          { status: 400 }
        )
      }
      updates.severity = body.severity
    }

    // Update assigned_to if provided
    if (body.assigned_to !== undefined) {
      updates.assigned_to = body.assigned_to
    }

    // Update verification if provided
    if (body.verification) {
      updates.verification = body.verification
    }

    // Create timeline entry for status change
    const timelineEntry = body.status ? {
      status: body.status,
      message: body.status_message || STATUS_MESSAGES[body.status] || `Status changed to ${body.status}`,
      timestamp: now,
      updated_by: body.updated_by || 'staff'
    } : null

    // Perform the update
    const updateQuery: Record<string, unknown> = { $set: updates }
    if (timelineEntry) {
      updateQuery.$push = { timeline: timelineEntry }
    }

    await collection.updateOne({ ticket }, updateQuery)

    console.log(`[PublicReport] Updated ${ticket}: ${JSON.stringify(updates)}`)

    // Send SMS notification to reporter if status changed and phone exists
    if (body.status && report.reporter_phone) {
      try {
        const smsResult = await notifyReportStatusChange(
          report.reporter_phone,
          ticket,
          body.status
        )
        if (smsResult.success) {
          console.log(`[PublicReport] SMS notification sent to ${report.reporter_phone} for ${ticket} status: ${body.status}`)
        } else {
          console.log(`[PublicReport] SMS failed for ${ticket}: ${smsResult.error || smsResult.status}`)
        }
      } catch (smsError) {
        // Don't fail the update if SMS fails
        console.error(`[PublicReport] SMS error for ${ticket}:`, smsError)
      }
    }

    return NextResponse.json({
      success: true,
      message: 'Report updated successfully',
      ticket,
      sms_sent: body.status && report.reporter_phone ? true : false
    })

  } catch (error) {
    console.error('[PublicReport] PATCH Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to update report' },
      { status: 500 }
    )
  }
}

// DELETE - Delete a report (admin only)
export async function DELETE(
  request: NextRequest,
  { params }: { params: { ticket: string } }
) {
  try {
    const ticket = params.ticket?.toUpperCase()

    if (!ticket) {
      return NextResponse.json(
        { success: false, message: 'Ticket number is required' },
        { status: 400 }
      )
    }

    const client = await clientPromise
    const db = client.db('lwsc')
    const collection = db.collection('public_reports')

    const result = await collection.deleteOne({ ticket })

    if (result.deletedCount === 0) {
      return NextResponse.json(
        { success: false, message: 'Report not found' },
        { status: 404 }
      )
    }

    // Also delete associated messages
    const messagesCollection = db.collection('ticket_messages')
    await messagesCollection.deleteMany({ ticket_id: ticket })

    console.log(`[PublicReport] Deleted ${ticket}`)

    return NextResponse.json({
      success: true,
      message: 'Report deleted successfully'
    })

  } catch (error) {
    console.error('[PublicReport] DELETE Error:', error)
    return NextResponse.json(
      { success: false, message: 'Failed to delete report' },
      { status: 500 }
    )
  }
}
