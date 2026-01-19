import { NextRequest, NextResponse } from 'next/server'

// USSD Integration API for basic phones
// Supports MTN, Airtel, and Zamtel USSD gateways

interface USSDRequest {
  sessionId: string
  phoneNumber: string
  serviceCode: string
  text: string
  networkCode?: string
}

interface USSDSession {
  phoneNumber: string
  stage: number
  data: Record<string, any>
  createdAt: number
}

// In-memory session store (use Redis in production)
const sessions = new Map<string, USSDSession>()

// Clean old sessions (older than 5 minutes)
const cleanOldSessions = () => {
  const now = Date.now()
  sessions.forEach((session, key) => {
    if (now - session.createdAt > 5 * 60 * 1000) {
      sessions.delete(key)
    }
  })
}

// USSD Menu Structure
const MENU = {
  MAIN: `CON Welcome to LWSC NRW Reporting
1. Report a Leak
2. Check Report Status
3. Water Bill Inquiry
4. Emergency Hotline
5. Change Language`,

  REPORT_LEAK: `CON Select Leak Type:
1. Burst Pipe (Water Gushing)
2. Leaking Valve/Joint
3. Damaged Meter
4. Illegal Connection
5. Other`,

  LEAK_LOCATION: `CON Enter Location:
Please enter the area/compound name and nearest landmark`,

  LEAK_SEVERITY: `CON How Severe?
1. Critical - Major flooding
2. High - Significant water loss
3. Medium - Moderate leak
4. Low - Small drip`,

  CONFIRM_REPORT: (data: any) => `CON Confirm Your Report:
Type: ${data.leakType}
Location: ${data.location}
Severity: ${data.severity}

1. Confirm & Submit
2. Cancel`,

  REPORT_SUCCESS: (ticketId: string) => `END Thank you for reporting!

Your Ticket: ${ticketId}

You will receive SMS updates.
Emergency: 0211-250001`,

  CHECK_STATUS: `CON Enter your Ticket Number:
(e.g., LRK-12345)`,

  STATUS_RESULT: (status: any) => `END Ticket: ${status.ticketId}
Status: ${status.status}
${status.assignedTo ? `Assigned to: ${status.assignedTo}` : ''}
${status.eta ? `ETA: ${status.eta}` : ''}

For updates, call 0211-250001`,

  BILL_INQUIRY: `CON Enter your Account Number:
(e.g., ACC-123456)`,

  BILL_RESULT: (bill: any) => `END Account: ${bill.accountNumber}
Name: ${bill.customerName}
Balance: K${bill.balance}
Due Date: ${bill.dueDate}

Pay via MTN/Airtel Money
or visit nearest LWSC office`,

  EMERGENCY: `END LWSC Emergency Contacts:

Main: 0211-250001
Burst Pipes: 0977-123456
Customer Care: 0211-250002

Your call is important to us!`,

  LANGUAGE: `CON Select Language:
1. English
2. Bemba (Chibemba)
3. Nyanja (Chinyanja)
4. Tonga (Chitonga)`,

  INVALID: `CON Invalid option. Please try again.
0. Back to Main Menu`,

  ERROR: `END An error occurred.
Please try again or call 0211-250001`
}

// Leak type mapping
const LEAK_TYPES: Record<string, string> = {
  '1': 'Burst Pipe',
  '2': 'Leaking Valve/Joint',
  '3': 'Damaged Meter',
  '4': 'Illegal Connection',
  '5': 'Other'
}

// Severity mapping
const SEVERITIES: Record<string, string> = {
  '1': 'Critical',
  '2': 'High',
  '3': 'Medium',
  '4': 'Low'
}

// Generate ticket ID
const generateTicketId = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
  const prefix = chars[Math.floor(Math.random() * chars.length)] + 
                 chars[Math.floor(Math.random() * chars.length)]
  const num = Math.floor(Math.random() * 90000) + 10000
  return `LRK-${prefix}${num}`
}

// Process USSD request
const processUSSD = (request: USSDRequest): string => {
  const { sessionId, phoneNumber, text } = request
  
  cleanOldSessions()
  
  // Get or create session
  let session = sessions.get(sessionId)
  if (!session) {
    session = {
      phoneNumber,
      stage: 0,
      data: {},
      createdAt: Date.now()
    }
    sessions.set(sessionId, session)
  }
  
  const input = text.split('*').pop() || ''
  const inputs = text.split('*')
  
  // Empty input = new session
  if (text === '') {
    session.stage = 0
    return MENU.MAIN
  }
  
  // Parse navigation through menu
  const firstChoice = inputs[0]
  
  // Main menu selection
  if (inputs.length === 1) {
    switch (firstChoice) {
      case '1':
        session.stage = 1
        return MENU.REPORT_LEAK
      case '2':
        session.stage = 10
        return MENU.CHECK_STATUS
      case '3':
        session.stage = 20
        return MENU.BILL_INQUIRY
      case '4':
        return MENU.EMERGENCY
      case '5':
        return MENU.LANGUAGE
      default:
        return MENU.INVALID
    }
  }
  
  // Report Leak Flow
  if (firstChoice === '1') {
    if (inputs.length === 2) {
      // Selected leak type
      const leakType = LEAK_TYPES[inputs[1]]
      if (!leakType) return MENU.INVALID
      session.data.leakType = leakType
      return MENU.LEAK_LOCATION
    }
    
    if (inputs.length === 3) {
      // Entered location
      session.data.location = inputs[2]
      return MENU.LEAK_SEVERITY
    }
    
    if (inputs.length === 4) {
      // Selected severity
      const severity = SEVERITIES[inputs[3]]
      if (!severity) return MENU.INVALID
      session.data.severity = severity
      return MENU.CONFIRM_REPORT(session.data)
    }
    
    if (inputs.length === 5) {
      // Confirmation
      if (inputs[4] === '1') {
        // Submit report
        const ticketId = generateTicketId()
        
        // In production: Save to database, send SMS, notify operators
        console.log('New leak report:', {
          ticketId,
          phoneNumber: session.phoneNumber,
          ...session.data
        })
        
        sessions.delete(sessionId)
        return MENU.REPORT_SUCCESS(ticketId)
      } else {
        sessions.delete(sessionId)
        return `END Report cancelled.
        
Call 0211-250001 for assistance.`
      }
    }
  }
  
  // Check Status Flow
  if (firstChoice === '2') {
    if (inputs.length === 2) {
      const ticketId = inputs[1].toUpperCase()
      
      // Mock status lookup (in production: query database)
      const mockStatus = {
        ticketId,
        status: 'In Progress',
        assignedTo: 'Bwalya M.',
        eta: '2 hours'
      }
      
      sessions.delete(sessionId)
      return MENU.STATUS_RESULT(mockStatus)
    }
  }
  
  // Bill Inquiry Flow
  if (firstChoice === '3') {
    if (inputs.length === 2) {
      const accountNumber = inputs[1].toUpperCase()
      
      // Mock bill lookup (in production: query billing system)
      const mockBill = {
        accountNumber,
        customerName: 'John Mwale',
        balance: '245.50',
        dueDate: '15 Feb 2026'
      }
      
      sessions.delete(sessionId)
      return MENU.BILL_RESULT(mockBill)
    }
  }
  
  // Language Selection
  if (firstChoice === '5') {
    if (inputs.length === 2) {
      const languages: Record<string, string> = {
        '1': 'English',
        '2': 'Bemba',
        '3': 'Nyanja',
        '4': 'Tonga'
      }
      const lang = languages[inputs[1]]
      if (lang) {
        session.data.language = lang
        return `END Language set to ${lang}.

Dial *123*LEAK# again to continue.`
      }
    }
  }
  
  return MENU.INVALID
}

// POST handler for USSD gateway
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Support different USSD gateway formats
    const ussdRequest: USSDRequest = {
      sessionId: body.sessionId || body.SessionId || body.session_id || '',
      phoneNumber: body.phoneNumber || body.PhoneNumber || body.msisdn || '',
      serviceCode: body.serviceCode || body.ServiceCode || body.service_code || '*123*LEAK#',
      text: body.text || body.Text || body.ussd_string || '',
      networkCode: body.networkCode || body.NetworkCode || ''
    }
    
    if (!ussdRequest.sessionId || !ussdRequest.phoneNumber) {
      return NextResponse.json(
        { error: 'Missing required fields: sessionId, phoneNumber' },
        { status: 400 }
      )
    }
    
    const response = processUSSD(ussdRequest)
    
    // Return in format expected by USSD gateway
    // Adjust based on your specific gateway (Africa's Talking, Hubtel, etc.)
    return new NextResponse(response, {
      headers: {
        'Content-Type': 'text/plain'
      }
    })
    
  } catch (error) {
    console.error('USSD Error:', error)
    return new NextResponse(MENU.ERROR, {
      headers: {
        'Content-Type': 'text/plain'
      }
    })
  }
}

// GET handler for testing
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  
  const ussdRequest: USSDRequest = {
    sessionId: searchParams.get('sessionId') || 'test-session',
    phoneNumber: searchParams.get('phoneNumber') || '+260971234567',
    serviceCode: searchParams.get('serviceCode') || '*123*LEAK#',
    text: searchParams.get('text') || ''
  }
  
  const response = processUSSD(ussdRequest)
  
  return new NextResponse(response, {
    headers: {
      'Content-Type': 'text/plain'
    }
  })
}
