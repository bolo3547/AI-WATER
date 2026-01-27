import { NextRequest, NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

// GET - Fetch billing data
export async function GET(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const search = searchParams.get('search')
    const limit = parseInt(searchParams.get('limit') || '50')
    
    // Build query
    const query: Record<string, any> = {}
    if (status && status !== 'all') {
      query.status = status
    }
    if (search) {
      query.$or = [
        { accountNumber: { $regex: search, $options: 'i' } },
        { name: { $regex: search, $options: 'i' } },
        { phone: { $regex: search, $options: 'i' } }
      ]
    }
    
    // Fetch customers with billing info
    const customers = await db.collection('billing_customers')
      .find(query)
      .sort({ updatedAt: -1 })
      .limit(limit)
      .toArray()
    
    // Fetch recent invoices
    const invoices = await db.collection('billing_invoices')
      .find({})
      .sort({ dueDate: -1 })
      .limit(20)
      .toArray()
    
    // Fetch recent payments
    const payments = await db.collection('billing_payments')
      .find({})
      .sort({ timestamp: -1 })
      .limit(20)
      .toArray()
    
    // Calculate statistics
    const stats = await db.collection('billing_customers').aggregate([
      {
        $group: {
          _id: null,
          totalCustomers: { $sum: 1 },
          totalBalance: { $sum: '$currentBalance' },
          overdueCount: { $sum: { $cond: [{ $eq: ['$status', 'overdue'] }, 1, 0] } },
          currentCount: { $sum: { $cond: [{ $eq: ['$status', 'current'] }, 1, 0] } },
          disconnectedCount: { $sum: { $cond: [{ $eq: ['$status', 'disconnected'] }, 1, 0] } }
        }
      }
    ]).toArray()
    
    const monthlyRevenue = await db.collection('billing_payments').aggregate([
      {
        $match: {
          status: 'completed',
          timestamp: { $gte: new Date(new Date().setDate(1)).toISOString() }
        }
      },
      {
        $group: {
          _id: null,
          total: { $sum: '$amount' }
        }
      }
    ]).toArray()
    
    return NextResponse.json({
      success: true,
      data: {
        customers,
        invoices,
        payments,
        stats: stats[0] || {
          totalCustomers: 0,
          totalBalance: 0,
          overdueCount: 0,
          currentCount: 0,
          disconnectedCount: 0
        },
        monthlyRevenue: monthlyRevenue[0]?.total || 0
      }
    })
    
  } catch (error) {
    console.error('[Billing API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch billing data'
    }, { status: 500 })
  }
}

// POST - Create invoice or record payment
export async function POST(request: NextRequest) {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    const body = await request.json()
    
    const { action } = body
    
    if (action === 'create_invoice') {
      const invoice = {
        id: `INV-${Date.now()}`,
        customerId: body.customerId,
        customerName: body.customerName,
        accountNumber: body.accountNumber,
        period: body.period,
        dueDate: body.dueDate,
        consumption: body.consumption,
        waterCharge: body.waterCharge,
        sewerCharge: body.sewerCharge || body.waterCharge * 0.3,
        arrears: body.arrears || 0,
        total: body.total,
        status: 'unpaid',
        paymentDate: null,
        createdAt: new Date().toISOString()
      }
      
      await db.collection('billing_invoices').insertOne(invoice)
      
      // Update customer balance
      await db.collection('billing_customers').updateOne(
        { id: body.customerId },
        { 
          $inc: { currentBalance: body.total },
          $set: { updatedAt: new Date().toISOString() }
        }
      )
      
      return NextResponse.json({ success: true, invoice })
    }
    
    if (action === 'record_payment') {
      const payment = {
        id: `PAY-${Date.now()}`,
        customerId: body.customerId,
        customerName: body.customerName,
        accountNumber: body.accountNumber,
        amount: body.amount,
        method: body.method,
        reference: body.reference || `REF-${Date.now()}`,
        status: 'completed',
        timestamp: new Date().toISOString()
      }
      
      await db.collection('billing_payments').insertOne(payment)
      
      // Update customer balance and last payment
      await db.collection('billing_customers').updateOne(
        { id: body.customerId },
        {
          $inc: { currentBalance: -body.amount },
          $set: {
            lastPayment: {
              amount: body.amount,
              date: new Date().toISOString().split('T')[0],
              method: body.method
            },
            status: 'current',
            updatedAt: new Date().toISOString()
          }
        }
      )
      
      return NextResponse.json({ success: true, payment })
    }
    
    if (action === 'add_customer') {
      const customer = {
        id: `CUS-${Date.now()}`,
        accountNumber: body.accountNumber || `LWSC-${new Date().getFullYear()}-${String(Date.now()).slice(-5)}`,
        name: body.name,
        phone: body.phone,
        email: body.email || '',
        address: body.address,
        dma: body.dma,
        meterNumber: body.meterNumber,
        tariffClass: body.tariffClass || 'residential',
        status: 'current',
        currentBalance: 0,
        lastPayment: null,
        lastReading: { value: 0, date: new Date().toISOString().split('T')[0] },
        avgMonthlyUsage: 0,
        connectionDate: new Date().toISOString().split('T')[0],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      
      await db.collection('billing_customers').insertOne(customer)
      
      return NextResponse.json({ success: true, customer })
    }
    
    return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 })
    
  } catch (error) {
    console.error('[Billing API] Error:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to process billing action'
    }, { status: 500 })
  }
}
