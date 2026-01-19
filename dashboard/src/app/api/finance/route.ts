import { NextResponse } from 'next/server'

// Finance API v2 - Real payment tracking
// In-memory storage for payments (in production, use a database)
// This will reset when the server restarts - perfect for demo
let payments: Payment[] = []
let invoices: Invoice[] = []

interface Payment {
  id: string
  invoiceId: string
  accountNumber: string
  customerName: string
  amount: number
  method: 'mobile_money' | 'bank_transfer' | 'cash' | 'card'
  reference: string
  timestamp: string
  dma: string
  status: 'completed' | 'pending' | 'failed'
}

interface Invoice {
  id: string
  accountNumber: string
  customerName: string
  dma: string
  amount: number
  consumption: number
  issueDate: string
  dueDate: string
  status: 'paid' | 'partial' | 'unpaid' | 'overdue'
  paidAmount: number
}

// Initialize with zero state - no fake data
function initializeState() {
  // Start fresh - no payments, no invoices paid
  // This represents the real state before any actual payments come in
  payments = []
  invoices = []
}

// Get current month's data
function getCurrentMonthData() {
  const now = new Date()
  const currentMonth = now.toISOString().slice(0, 7) // YYYY-MM
  
  const monthPayments = payments.filter(p => 
    p.timestamp.startsWith(currentMonth) && p.status === 'completed'
  )
  
  const totalCollected = monthPayments.reduce((sum, p) => sum + p.amount, 0)
  
  return {
    month: now.toLocaleString('default', { month: 'short' }),
    year: now.getFullYear(),
    collected: totalCollected,
    paymentCount: monthPayments.length,
    payments: monthPayments
  }
}

// Get historical data (last N months)
function getHistoricalData(months: number = 6) {
  const data = []
  const now = new Date()
  
  for (let i = months - 1; i >= 0; i--) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const monthKey = date.toISOString().slice(0, 7)
    const monthName = date.toLocaleString('default', { month: 'short' })
    
    const monthPayments = payments.filter(p => 
      p.timestamp.startsWith(monthKey) && p.status === 'completed'
    )
    
    const collected = monthPayments.reduce((sum, p) => sum + p.amount, 0)
    
    // Billed amount is 0 until we have real billing data
    // In real system, this would come from billing system
    const billed = 0
    
    data.push({
      month: monthName,
      monthKey,
      billed,
      collected,
      nrwLoss: 0, // Calculated from actual NRW measurements
      recovered: 0, // Recovered through leak repairs
      paymentCount: monthPayments.length
    })
  }
  
  return data
}

// Calculate totals
function calculateTotals() {
  const allCompleted = payments.filter(p => p.status === 'completed')
  const totalCollected = allCompleted.reduce((sum, p) => sum + p.amount, 0)
  
  // Today's payments
  const today = new Date().toISOString().slice(0, 10)
  const todayPayments = allCompleted.filter(p => p.timestamp.startsWith(today))
  
  return {
    totalBilled: 0, // No billing yet
    totalCollected,
    collectionRate: 0, // No billing means 0% rate
    paymentCount: allCompleted.length,
    todayPayments: todayPayments.length,
    averagePayment: allCompleted.length > 0 ? totalCollected / allCompleted.length : 0,
    byMethod: getPaymentMethodBreakdown(),
    byDMA: getDMABreakdown()
  }
}

// DMA breakdown
function getDMABreakdown() {
  const dmaData: Record<string, { count: number; total: number }> = {}
  
  payments.filter(p => p.status === 'completed').forEach(p => {
    if (!dmaData[p.dma]) {
      dmaData[p.dma] = { count: 0, total: 0 }
    }
    dmaData[p.dma].count++
    dmaData[p.dma].total += p.amount
  })
  
  return dmaData
}

// Customer segments - start empty
function getCustomerSegments() {
  // Group payments by DMA to show where revenue is coming from
  const dmaRevenue: Record<string, { count: number, revenue: number }> = {}
  
  payments.filter(p => p.status === 'completed').forEach(p => {
    if (!dmaRevenue[p.dma]) {
      dmaRevenue[p.dma] = { count: 0, revenue: 0 }
    }
    dmaRevenue[p.dma].count++
    dmaRevenue[p.dma].revenue += p.amount
  })
  
  // Convert to array
  return Object.entries(dmaRevenue).map(([dma, data]) => ({
    dma,
    paymentCount: data.count,
    revenue: data.revenue
  }))
}

// Payment methods breakdown
function getPaymentMethodBreakdown() {
  const methods: Record<string, { count: number, total: number }> = {
    mobile_money: { count: 0, total: 0 },
    bank_transfer: { count: 0, total: 0 },
    cash: { count: 0, total: 0 },
    card: { count: 0, total: 0 }
  }
  
  payments.filter(p => p.status === 'completed').forEach(p => {
    methods[p.method].count++
    methods[p.method].total += p.amount
  })
  
  return methods
}

// Recent payments
function getRecentPayments(limit: number = 10) {
  return payments
    .filter(p => p.status === 'completed')
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit)
}

// GET endpoint
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const type = searchParams.get('type') || 'summary'
  const months = parseInt(searchParams.get('months') || '6')
  
  const totals = calculateTotals()
  const currentMonth = getCurrentMonthData()
  
  if (type === 'summary') {
    return NextResponse.json({
      status: 'active',
      message: payments.length === 0 
        ? 'No payments received yet. Revenue data will appear when customers make payments.'
        : `${totals.paymentCount} payments received totaling K${totals.totalCollected.toLocaleString()}`,
      totals: {
        ...totals,
        currency: 'ZMW',
        symbol: 'K'
      },
      currentMonth,
      recentPayments: getRecentPayments(5),
      paymentMethods: getPaymentMethodBreakdown(),
      lastUpdated: new Date().toISOString()
    })
  }
  
  if (type === 'history') {
    return NextResponse.json({
      revenueData: getHistoricalData(months),
      totals,
      lastUpdated: new Date().toISOString()
    })
  }
  
  if (type === 'segments') {
    return NextResponse.json({
      segments: getCustomerSegments(),
      lastUpdated: new Date().toISOString()
    })
  }
  
  if (type === 'payments') {
    const limit = parseInt(searchParams.get('limit') || '50')
    return NextResponse.json({
      payments: getRecentPayments(limit),
      total: payments.filter(p => p.status === 'completed').length,
      lastUpdated: new Date().toISOString()
    })
  }
  
  // Default: return everything
  return NextResponse.json({
    status: 'active',
    message: payments.length === 0 
      ? 'System ready. No payments received yet.'
      : `${totals.paymentCount} payments processed.`,
    totals,
    currentMonth,
    revenueData: getHistoricalData(months),
    segments: getCustomerSegments(),
    paymentMethods: getPaymentMethodBreakdown(),
    recentPayments: getRecentPayments(10),
    predictions: {
      // AI predictions based on actual data (empty until we have data)
      estimatedMonthlyPotential: 0,
      collectionEfficiency: 0,
      trendDirection: 'neutral'
    },
    lastUpdated: new Date().toISOString()
  })
}

// POST endpoint - Record a new payment
export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    const {
      accountNumber,
      customerName,
      amount,
      method = 'mobile_money',
      reference,
      dma = 'Unknown'
    } = body
    
    if (!accountNumber || !amount) {
      return NextResponse.json(
        { error: 'Account number and amount are required' },
        { status: 400 }
      )
    }
    
    const payment: Payment = {
      id: `PAY-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      invoiceId: body.invoiceId || '',
      accountNumber,
      customerName: customerName || 'Customer',
      amount: parseFloat(amount),
      method,
      reference: reference || `REF-${Date.now()}`,
      timestamp: new Date().toISOString(),
      dma,
      status: 'completed'
    }
    
    payments.push(payment)
    
    return NextResponse.json({
      success: true,
      message: `Payment of K${amount.toLocaleString()} recorded successfully`,
      payment,
      newTotal: calculateTotals().totalCollected
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to process payment' },
      { status: 500 }
    )
  }
}
