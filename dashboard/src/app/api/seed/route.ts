import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

// POST - Seed initial data
export async function POST(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { collection } = await request.json()
    
    // Seed Billing Customers
    if (!collection || collection === 'billing') {
      const customersCount = await db.collection('billing_customers').countDocuments()
      
      if (customersCount === 0) {
        const customers = [
          {
            id: 'CUS-001',
            accountNumber: 'LWSC-2024-00145',
            name: 'Peter Tembo',
            phone: '+260 97 123 4567',
            email: 'peter.tembo@email.com',
            address: 'Plot 45, Leopards Hill Road, Kabulonga',
            dma: 'Kabulonga',
            meterNumber: 'ZM-R-KAB-00123',
            tariffClass: 'residential',
            status: 'current',
            currentBalance: 0,
            lastPayment: { amount: 450, date: '2026-01-15', method: 'mtn-momo' },
            lastReading: { value: 12456, date: '2026-01-18' },
            avgMonthlyUsage: 15.2,
            connectionDate: '2022-03-15',
            createdAt: new Date().toISOString()
          },
          {
            id: 'CUS-002',
            accountNumber: 'LWSC-2024-00289',
            name: 'Mwila Trading Ltd',
            phone: '+260 96 555 7890',
            email: 'accounts@mwilatrading.co.zm',
            address: 'Plot 78, Cairo Road, City Centre',
            dma: 'CBD',
            meterNumber: 'ZM-C-CBD-00456',
            tariffClass: 'commercial',
            status: 'overdue',
            currentBalance: 2850,
            lastPayment: { amount: 1500, date: '2025-12-10', method: 'bank' },
            lastReading: { value: 45678, date: '2026-01-17' },
            avgMonthlyUsage: 125.8,
            connectionDate: '2019-08-22',
            createdAt: new Date().toISOString()
          },
          {
            id: 'CUS-003',
            accountNumber: 'LWSC-2024-00567',
            name: 'Grace Banda',
            phone: '+260 95 234 5678',
            email: 'grace.banda@gmail.com',
            address: 'House 23, Twin Palm Road, Roma',
            dma: 'Roma',
            meterNumber: 'ZM-R-ROM-00789',
            tariffClass: 'residential',
            status: 'pending',
            currentBalance: 380,
            lastPayment: null,
            lastReading: { value: 8934, date: '2026-01-16' },
            avgMonthlyUsage: 12.5,
            connectionDate: '2025-01-10',
            createdAt: new Date().toISOString()
          },
          {
            id: 'CUS-004',
            accountNumber: 'LWSC-2024-00891',
            name: 'University of Zambia',
            phone: '+260 21 129 5000',
            email: 'estates@unza.zm',
            address: 'Great East Road Campus',
            dma: 'UNZA',
            meterNumber: 'ZM-I-UNZ-00001',
            tariffClass: 'institutional',
            status: 'current',
            currentBalance: 0,
            lastPayment: { amount: 45000, date: '2026-01-12', method: 'bank' },
            lastReading: { value: 987654, date: '2026-01-18' },
            avgMonthlyUsage: 2500,
            connectionDate: '1965-07-12',
            createdAt: new Date().toISOString()
          },
          {
            id: 'CUS-005',
            accountNumber: 'LWSC-2024-00234',
            name: 'Joseph Mumba',
            phone: '+260 97 987 6543',
            email: 'jmumba@yahoo.com',
            address: 'Plot 12, Matero Main Road',
            dma: 'Matero',
            meterNumber: 'ZM-R-MAT-00567',
            tariffClass: 'residential',
            status: 'disconnected',
            currentBalance: 1250,
            lastPayment: { amount: 200, date: '2025-10-25', method: 'cash' },
            lastReading: { value: 5678, date: '2025-11-15' },
            avgMonthlyUsage: 8.3,
            connectionDate: '2021-05-20',
            createdAt: new Date().toISOString()
          }
        ]
        
        await db.collection('billing_customers').insertMany(customers)
        
        // Seed invoices
        const invoices = [
          {
            id: 'INV-2026-0145',
            customerId: 'CUS-001',
            customerName: 'Peter Tembo',
            accountNumber: 'LWSC-2024-00145',
            period: 'January 2026',
            dueDate: '2026-02-15',
            consumption: 14.5,
            waterCharge: 362.50,
            sewerCharge: 72.50,
            arrears: 0,
            total: 435,
            status: 'unpaid',
            paymentDate: null,
            createdAt: new Date().toISOString()
          },
          {
            id: 'INV-2026-0289',
            customerId: 'CUS-002',
            customerName: 'Mwila Trading Ltd',
            accountNumber: 'LWSC-2024-00289',
            period: 'January 2026',
            dueDate: '2026-02-15',
            consumption: 132.4,
            waterCharge: 3310,
            sewerCharge: 662,
            arrears: 2850,
            total: 6822,
            status: 'overdue',
            paymentDate: null,
            createdAt: new Date().toISOString()
          }
        ]
        
        await db.collection('billing_invoices').insertMany(invoices)
        
        // Seed payments
        const payments = [
          {
            id: 'PAY-001',
            customerId: 'CUS-001',
            customerName: 'Peter Tembo',
            accountNumber: 'LWSC-2024-00145',
            amount: 450,
            method: 'mtn-momo',
            reference: 'MTN-789456123',
            status: 'completed',
            timestamp: '2026-01-15T10:30:00',
            createdAt: new Date().toISOString()
          },
          {
            id: 'PAY-002',
            customerId: 'CUS-004',
            customerName: 'University of Zambia',
            accountNumber: 'LWSC-2024-00891',
            amount: 45000,
            method: 'bank',
            reference: 'ZNBS-2026-0112',
            status: 'completed',
            timestamp: '2026-01-12T14:22:00',
            createdAt: new Date().toISOString()
          }
        ]
        
        await db.collection('billing_payments').insertMany(payments)
      }
    }
    
    // Seed Shift Handovers
    if (!collection || collection === 'shift-handover') {
      const handoversCount = await db.collection('shift_handovers').countDocuments()
      
      if (handoversCount === 0) {
        const shiftChecklist = [
          'All pump stations operational and remote monitored',
          'Reservoir levels within normal range (60-85%)',
          'SCADA system functioning normally',
          'All DMA meters transmitting data',
          'Control room equipment functional',
          'Emergency contact list updated',
          'Vehicle inspection completed',
          'Safety equipment checked',
          'Logbook entries up to date',
          'Chemical stock levels adequate',
        ]
        
        const handovers = [
          {
            id: 'SH-2847',
            shiftType: 'day',
            date: new Date().toISOString().split('T')[0],
            startTime: '06:00',
            endTime: '18:00',
            outgoingOperator: 'John Mwale',
            incomingOperator: 'Grace Banda',
            status: 'completed',
            systemStatus: {
              pumpsOperational: 8,
              pumpsTotal: 10,
              reservoirLevels: [
                { name: 'Matero', level: 72 },
                { name: 'Kabulonga', level: 85 },
                { name: 'Chilenje', level: 65 },
              ],
              activeAlerts: 3,
              activeLeaks: 2,
              ongoingWorks: 4,
            },
            checklist: shiftChecklist.map((item, i) => ({ 
              item, 
              checked: true, 
              notes: i === 1 ? 'Matero slightly low due to high demand' : '' 
            })),
            incidents: [
              { 
                time: '09:30', 
                description: 'Pump #3 at Iolanda tripped due to power fluctuation', 
                action: 'Reset manually, monitoring closely', 
                resolved: true 
              },
            ],
            notes: 'Pump #2 showing minor vibration - scheduled for maintenance next week.',
            criticalItems: ['Monitor Pump #3 closely'],
            pendingTasks: [
              { task: 'Follow up on Garden pressure issue', priority: 'high' },
            ],
            submittedAt: new Date().toISOString(),
            acknowledgedAt: new Date().toISOString(),
            createdAt: new Date().toISOString()
          },
          {
            id: 'SH-2848',
            shiftType: 'night',
            date: new Date().toISOString().split('T')[0],
            startTime: '18:00',
            endTime: '06:00',
            outgoingOperator: 'Grace Banda',
            incomingOperator: null,
            status: 'in-progress',
            systemStatus: {
              pumpsOperational: 8,
              pumpsTotal: 10,
              reservoirLevels: [
                { name: 'Matero', level: 68 },
                { name: 'Kabulonga', level: 82 },
                { name: 'Chilenje', level: 71 },
              ],
              activeAlerts: 2,
              activeLeaks: 2,
              ongoingWorks: 1,
            },
            checklist: shiftChecklist.map((item, i) => ({ 
              item, 
              checked: i < 6, 
              notes: '' 
            })),
            incidents: [],
            notes: '',
            criticalItems: [],
            pendingTasks: [],
            submittedAt: null,
            acknowledgedAt: null,
            createdAt: new Date().toISOString()
          }
        ]
        
        await db.collection('shift_handovers').insertMany(handovers)
      }
    }
    
    // Seed Security data
    if (!collection || collection === 'security') {
      const apiKeysCount = await db.collection('api_keys').countDocuments()
      
      if (apiKeysCount === 0) {
        const apiKeys = [
          {
            id: 'key-1',
            name: 'Production API',
            key: 'aqw_sk_live_7x8k2m9n4p5q6r3s1t0u',
            status: 'active',
            createdAt: '2026-01-01T08:00:00Z',
            lastUsed: new Date().toISOString(),
            permissions: ['read', 'write', 'admin'],
            usageCount: 15420
          },
          {
            id: 'key-2',
            name: 'Dashboard Integration',
            key: 'aqw_sk_live_3a4b5c6d7e8f9g0h1i2j',
            status: 'active',
            createdAt: '2026-01-10T10:30:00Z',
            lastUsed: new Date(Date.now() - 3600000).toISOString(),
            permissions: ['read'],
            usageCount: 8934
          }
        ]
        
        await db.collection('api_keys').insertMany(apiKeys)
        
        // Seed audit logs
        const auditLogs = [
          { id: '1', user: 'admin', role: 'Administrator', action: 'Login', resource: 'Auth', ip: '192.168.8.100', location: 'Lusaka, ZM', device: 'Chrome/Windows', timestamp: new Date().toISOString(), status: 'success' },
          { id: '2', user: 'operator', role: 'Operator', action: 'View Dashboard', resource: 'Dashboard', ip: '192.168.8.101', location: 'Lusaka, ZM', device: 'Firefox/Linux', timestamp: new Date(Date.now() - 300000).toISOString(), status: 'success' },
          { id: '3', user: 'system', role: 'System', action: 'Backup Completed', resource: 'Database', ip: '127.0.0.1', location: 'Local', device: 'System', timestamp: new Date(Date.now() - 7200000).toISOString(), status: 'success' },
        ]
        
        await db.collection('audit_logs').insertMany(auditLogs)
        
        // Seed active sessions
        const sessions = [
          { id: 'sess-1', user: 'admin', role: 'Administrator', device: 'Desktop', browser: 'Chrome 120', ip: '192.168.8.100', location: 'Lusaka, ZM', loginTime: new Date(Date.now() - 3600000).toISOString(), lastActivity: new Date().toISOString(), current: true },
        ]
        
        await db.collection('active_sessions').insertMany(sessions)
      }
    }
    
    return NextResponse.json({
      success: true,
      message: 'Database seeded successfully'
    })
    
  } catch (error) {
    console.error('[Seed API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to seed database'
    }, { status: 500 })
  }
}

// GET - Check seed status
export async function GET() {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const [customersCount, handoversCount, apiKeysCount] = await Promise.all([
      db.collection('billing_customers').countDocuments(),
      db.collection('shift_handovers').countDocuments(),
      db.collection('api_keys').countDocuments()
    ])
    
    return NextResponse.json({
      success: true,
      data: {
        billing: customersCount,
        shiftHandover: handoversCount,
        security: apiKeysCount,
        needsSeed: customersCount === 0 || handoversCount === 0 || apiKeysCount === 0
      }
    })
    
  } catch (error) {
    console.error('[Seed API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to check seed status'
    }, { status: 500 })
  }
}
