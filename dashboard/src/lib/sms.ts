// SMS Notification Service for LWSC
// Supports Africa's Talking and Twilio

export interface SMSRequest {
  to: string | string[]  // Phone number(s) with country code
  message: string
  type?: 'alert' | 'bill' | 'payment' | 'reminder' | 'general'
}

export interface SMSResponse {
  success: boolean
  messageId?: string
  cost?: number
  status: string
  error?: string
}

// Africa's Talking Configuration (recommended for Zambia)
const AT_CONFIG = {
  apiKey: process.env.AFRICAS_TALKING_API_KEY || '',
  username: process.env.AFRICAS_TALKING_USERNAME || 'sandbox',
  senderId: process.env.AFRICAS_TALKING_SENDER_ID || 'LWSC',
  environment: process.env.AFRICAS_TALKING_ENV || 'sandbox'
}

// Twilio Configuration (alternative)
const TWILIO_CONFIG = {
  accountSid: process.env.TWILIO_ACCOUNT_SID || '',
  authToken: process.env.TWILIO_AUTH_TOKEN || '',
  phoneNumber: process.env.TWILIO_PHONE_NUMBER || ''
}

// Check which provider is configured
export const smsProviders = {
  africasTalking: !!AT_CONFIG.apiKey,
  twilio: !!(TWILIO_CONFIG.accountSid && TWILIO_CONFIG.authToken)
}

export const isConfigured = smsProviders.africasTalking || smsProviders.twilio

// Format Zambian phone numbers
function formatZambianPhone(phone: string): string {
  let cleaned = phone.replace(/\D/g, '')
  
  // Remove leading zeros
  cleaned = cleaned.replace(/^0+/, '')
  
  // Add country code if not present
  if (!cleaned.startsWith('260')) {
    cleaned = '260' + cleaned
  }
  
  return '+' + cleaned
}

// Africa's Talking SMS
async function sendViaAfricasTalking(request: SMSRequest): Promise<SMSResponse> {
  const recipients = Array.isArray(request.to) 
    ? request.to.map(formatZambianPhone) 
    : [formatZambianPhone(request.to)]
  
  try {
    const apiUrl = AT_CONFIG.environment === 'sandbox'
      ? 'https://api.sandbox.africastalking.com/version1/messaging'
      : 'https://api.africastalking.com/version1/messaging'
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'apiKey': AT_CONFIG.apiKey
      },
      body: new URLSearchParams({
        username: AT_CONFIG.username,
        to: recipients.join(','),
        message: request.message,
        from: AT_CONFIG.senderId
      })
    })
    
    const data = await response.json()
    
    if (data.SMSMessageData?.Recipients?.length > 0) {
      const recipient = data.SMSMessageData.Recipients[0]
      return {
        success: recipient.status === 'Success',
        messageId: recipient.messageId,
        cost: parseFloat(recipient.cost?.replace('ZMW ', '') || '0'),
        status: recipient.status
      }
    }
    
    throw new Error(data.SMSMessageData?.Message || 'Unknown error')
  } catch (error: any) {
    return {
      success: false,
      status: 'failed',
      error: error.message
    }
  }
}

// Twilio SMS
async function sendViaTwilio(request: SMSRequest): Promise<SMSResponse> {
  const recipients = Array.isArray(request.to) 
    ? request.to.map(formatZambianPhone) 
    : [formatZambianPhone(request.to)]
  
  try {
    const results = await Promise.all(recipients.map(async (to) => {
      const response = await fetch(
        `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_CONFIG.accountSid}/Messages.json`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Basic ${Buffer.from(`${TWILIO_CONFIG.accountSid}:${TWILIO_CONFIG.authToken}`).toString('base64')}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({
            To: to,
            From: TWILIO_CONFIG.phoneNumber,
            Body: request.message
          })
        }
      )
      
      return response.json()
    }))
    
    const firstResult = results[0]
    return {
      success: !firstResult.error_code,
      messageId: firstResult.sid,
      status: firstResult.status || 'sent',
      error: firstResult.error_message
    }
  } catch (error: any) {
    return {
      success: false,
      status: 'failed',
      error: error.message
    }
  }
}

// Main SMS send function
export async function sendSMS(request: SMSRequest): Promise<SMSResponse> {
  if (smsProviders.africasTalking) {
    return sendViaAfricasTalking(request)
  }
  
  if (smsProviders.twilio) {
    return sendViaTwilio(request)
  }
  
  return {
    success: false,
    status: 'not_configured',
    error: 'No SMS provider configured. Add AFRICAS_TALKING_* or TWILIO_* environment variables.'
  }
}

// Pre-built message templates
export const smsTemplates = {
  // Leak Alerts
  leakDetected: (location: string, severity: string) => 
    `LWSC ALERT: ${severity.toUpperCase()} leak detected at ${location}. Crew dispatched. Updates to follow.`,
  
  leakResolved: (location: string, duration: string) =>
    `LWSC UPDATE: Leak at ${location} has been repaired. Duration: ${duration}. Thank you for your patience.`,
  
  // Billing
  billReady: (account: string, amount: number, dueDate: string) =>
    `LWSC BILL: Your water bill for account ${account} is ready. Amount: K${amount.toLocaleString()}. Due: ${dueDate}. Pay via *123# or LWSC app.`,
  
  paymentReminder: (account: string, amount: number, daysOverdue: number) =>
    `LWSC REMINDER: Your bill of K${amount.toLocaleString()} for account ${account} is ${daysOverdue} days overdue. Pay now to avoid disconnection.`,
  
  paymentReceived: (amount: number, reference: string) =>
    `LWSC PAYMENT: K${amount.toLocaleString()} received. Ref: ${reference}. Thank you for your payment!`,
  
  // Service
  maintenanceScheduled: (area: string, date: string, duration: string) =>
    `LWSC NOTICE: Scheduled maintenance in ${area} on ${date}. Expected duration: ${duration}. Water supply may be affected.`,
  
  serviceRestored: (area: string) =>
    `LWSC UPDATE: Water service has been restored in ${area}. Thank you for your patience.`,
  
  // Customer Reports - Basic
  reportReceived: (reportId: string) =>
    `LWSC: Thank you for your report. Reference: ${reportId}. We'll investigate and update you soon.`,
  
  reportResolved: (reportId: string) =>
    `LWSC: Your report ${reportId} has been resolved. Thank you for helping improve our service.`,

  // Customer Reports - Detailed Status Updates
  publicReport: {
    received: (ticket: string, category: string) =>
      `LWSC AquaWatch: Your ${category} report received! Ticket: ${ticket}. Track at lwsc.co.zm/ticket?id=${ticket}. Thank you for reporting!`,
    
    underReview: (ticket: string) =>
      `LWSC Update [${ticket}]: Your report is now under review by our team. We'll update you on progress.`,
    
    technicianAssigned: (ticket: string) =>
      `LWSC Update [${ticket}]: Great news! A technician has been assigned to investigate your reported issue.`,
    
    inProgress: (ticket: string) =>
      `LWSC Update [${ticket}]: Work is now in progress to resolve your issue. We appreciate your patience.`,
    
    resolved: (ticket: string) =>
      `LWSC Update [${ticket}]: Your reported issue has been RESOLVED. Thank you for helping improve water services in Lusaka!`,
    
    closed: (ticket: string) =>
      `LWSC Update [${ticket}]: Your report has been closed. For new issues, report at lwsc.co.zm/report. Thank you!`,
    
    staffResponse: (ticket: string) =>
      `LWSC [${ticket}]: You have a new message from our team. View at lwsc.co.zm/ticket?id=${ticket}`
  }
}

// Bulk SMS for area notifications
export async function sendBulkSMS(
  phoneNumbers: string[],
  message: string,
  batchSize: number = 100
): Promise<{ sent: number; failed: number }> {
  let sent = 0
  let failed = 0
  
  // Send in batches
  for (let i = 0; i < phoneNumbers.length; i += batchSize) {
    const batch = phoneNumbers.slice(i, i + batchSize)
    const result = await sendSMS({ to: batch, message })
    
    if (result.success) {
      sent += batch.length
    } else {
      failed += batch.length
    }
    
    // Rate limiting - wait between batches
    if (i + batchSize < phoneNumbers.length) {
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
  
  return { sent, failed }
}

// Send alert to all affected customers in a DMA
export async function notifyDMACustomers(
  dma: string,
  message: string,
  customerPhones: string[]
): Promise<{ sent: number; failed: number }> {
  if (customerPhones.length === 0) {
    return { sent: 0, failed: 0 }
  }
  
  return sendBulkSMS(customerPhones, message)
}

// Category display names
const categoryDisplayNames: Record<string, string> = {
  'leak': 'water leak',
  'burst': 'burst pipe',
  'no_water': 'no water supply',
  'low_pressure': 'low pressure',
  'illegal_connection': 'illegal connection',
  'overflow': 'overflow/flooding',
  'contamination': 'water quality',
  'other': 'water issue'
}

/**
 * Send SMS notification when a public report is submitted
 */
export async function notifyReportSubmission(
  phone: string,
  ticket: string,
  category: string
): Promise<SMSResponse> {
  if (!phone) {
    return { success: false, status: 'skipped', error: 'No phone number provided' }
  }

  const categoryName = categoryDisplayNames[category] || category
  const message = smsTemplates.publicReport.received(ticket, categoryName)
  
  console.log(`[SMS] Sending report confirmation to ${phone} for ticket ${ticket}`)
  return sendSMS({ to: phone, message, type: 'general' })
}

/**
 * Send SMS notification when report status changes
 */
export async function notifyReportStatusChange(
  phone: string,
  ticket: string,
  status: string,
  customMessage?: string
): Promise<SMSResponse> {
  if (!phone) {
    return { success: false, status: 'skipped', error: 'No phone number provided' }
  }

  let message: string

  switch (status) {
    case 'under_review':
      message = smsTemplates.publicReport.underReview(ticket)
      break
    case 'technician_assigned':
      message = smsTemplates.publicReport.technicianAssigned(ticket)
      break
    case 'in_progress':
      message = smsTemplates.publicReport.inProgress(ticket)
      break
    case 'resolved':
      message = smsTemplates.publicReport.resolved(ticket)
      break
    case 'closed':
      message = smsTemplates.publicReport.closed(ticket)
      break
    case 'staff_response':
      message = smsTemplates.publicReport.staffResponse(ticket)
      break
    default:
      message = customMessage || `LWSC Update [${ticket}]: Your report status has been updated to ${status}.`
  }

  console.log(`[SMS] Sending status update to ${phone} for ticket ${ticket}: ${status}`)
  return sendSMS({ to: phone, message, type: 'general' })
}

/**
 * Send SMS when staff responds to a ticket
 */
export async function notifyStaffResponse(
  phone: string,
  ticket: string
): Promise<SMSResponse> {
  if (!phone) {
    return { success: false, status: 'skipped', error: 'No phone number provided' }
  }

  const message = smsTemplates.publicReport.staffResponse(ticket)
  
  console.log(`[SMS] Sending staff response notification to ${phone} for ticket ${ticket}`)
  return sendSMS({ to: phone, message, type: 'general' })
}
