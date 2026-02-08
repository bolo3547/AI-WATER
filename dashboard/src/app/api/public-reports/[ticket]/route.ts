import { NextRequest, NextResponse } from 'next/server'
import { notifyReportStatusChange } from '@/lib/sms'
import { inMemoryReports, getMongoCollection } from '@/lib/report-store'

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

    // Try MongoDB
    const collection = await getMongoCollection()
    let report: Record<string, unknown> | null = null

    if (collection) {
      report = await collection.findOne({ ticket })
    }

    // Fallback: check in-memory store
    if (!report) {
      const memReport = inMemoryReports.get(ticket)
      if (memReport) {
        report = memReport as unknown as Record<string, unknown>
      }
    }

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

    // Try MongoDB
    const collection = await getMongoCollection()
    let report: Record<string, unknown> | null = null

    if (collection) {
      report = await collection.findOne({ ticket })
    }

    // Fallback: check in-memory store
    let isInMemory = false
    if (!report) {
      const memReport = inMemoryReports.get(ticket)
      if (memReport) {
        report = memReport as unknown as Record<string, unknown>
        isInMemory = true
      }
    }

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

    if (collection && !isInMemory) {
      // Perform MongoDB update
      const updateQuery: Record<string, unknown> = { $set: updates }
      if (timelineEntry) {
        updateQuery.$push = { timeline: timelineEntry }
      }
      await collection.updateOne({ ticket }, updateQuery)
    } else if (isInMemory) {
      // Update in-memory report
      const memReport = inMemoryReports.get(ticket)
      if (memReport) {
        Object.assign(memReport, updates)
        if (timelineEntry) {
          memReport.timeline.push(timelineEntry)
        }
      }
    }

    console.log(`[PublicReport] Updated ${ticket}: ${JSON.stringify(updates)}`)

    // Send SMS notification to reporter if status changed and phone exists
    const reporterPhone = report.reporter_phone as string | null
    if (body.status && reporterPhone) {
      try {
        const smsResult = await notifyReportStatusChange(
          reporterPhone,
          ticket,
          body.status
        )
        if (smsResult.success) {
          console.log(`[PublicReport] SMS notification sent to ${reporterPhone} for ${ticket} status: ${body.status}`)
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
      sms_sent: body.status && reporterPhone ? true : false
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

    // Try MongoDB
    const collection = await getMongoCollection()

    if (collection) {
      const result = await collection.deleteOne({ ticket })

      if (result.deletedCount === 0) {
        // Check in-memory before returning 404
        if (inMemoryReports.delete(ticket)) {
          return NextResponse.json({ success: true, message: 'Report deleted successfully' })
        }
        return NextResponse.json(
          { success: false, message: 'Report not found' },
          { status: 404 }
        )
      }

      // Also delete associated messages
      try {
        const { default: clientPromise } = await import('@/lib/mongodb')
        const client = await clientPromise
        const db = client.db('lwsc')
        const messagesCollection = db.collection('ticket_messages')
        await messagesCollection.deleteMany({ ticket_id: ticket })
      } catch {
        // ignore message cleanup failure
      }
    } else {
      // In-memory fallback
      if (!inMemoryReports.delete(ticket)) {
        return NextResponse.json(
          { success: false, message: 'Report not found' },
          { status: 404 }
        )
      }
    }

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
