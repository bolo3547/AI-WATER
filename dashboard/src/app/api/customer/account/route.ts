import { NextRequest, NextResponse } from 'next/server'

// In production, this would query Supabase
// For now, return realistic demo data or "not found"

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const accountNumber = searchParams.get('number')

  if (!accountNumber) {
    return NextResponse.json(
      { error: 'Account number is required' },
      { status: 400 }
    )
  }

  // Demo accounts for testing
  const demoAccounts: Record<string, any> = {
    'KAB/1/0001/2024': {
      accountNumber: 'KAB/1/0001/2024',
      customerName: 'John Mwanza',
      address: 'Plot 123, Kabwata, Lusaka',
      status: 'active',
      meterNumber: 'MTR-KAB-0001',
      balance: 450.00,
      dueDate: '2026-02-15',
      currentUsage: 18,
      avgUsage: 22,
      lastPayment: {
        amount: 320.00,
        date: '2026-01-10'
      },
      billingHistory: [
        { month: 'January 2026', amount: 320, usage: 20, paid: true },
        { month: 'December 2025', amount: 285, usage: 18, paid: true },
        { month: 'November 2025', amount: 340, usage: 22, paid: true }
      ]
    },
    'CHI/2/0042/2023': {
      accountNumber: 'CHI/2/0042/2023',
      customerName: 'Grace Tembo',
      address: 'House 42, Chilenje South, Lusaka',
      status: 'active',
      meterNumber: 'MTR-CHI-0042',
      balance: 0,
      dueDate: null,
      currentUsage: 15,
      avgUsage: 16,
      lastPayment: {
        amount: 280.00,
        date: '2026-01-25'
      },
      billingHistory: [
        { month: 'January 2026', amount: 280, usage: 16, paid: true },
        { month: 'December 2025', amount: 265, usage: 15, paid: true }
      ]
    },
    'MAT/3/0108/2024': {
      accountNumber: 'MAT/3/0108/2024',
      customerName: 'Peter Banda',
      address: 'Stand 108, Matero, Lusaka',
      status: 'disconnected',
      meterNumber: 'MTR-MAT-0108',
      balance: 1250.00,
      dueDate: '2026-01-01',
      currentUsage: 0,
      avgUsage: 28,
      lastPayment: {
        amount: 150.00,
        date: '2025-11-05'
      },
      billingHistory: [
        { month: 'January 2026', amount: 0, usage: 0, paid: false },
        { month: 'December 2025', amount: 420, usage: 28, paid: false },
        { month: 'November 2025', amount: 380, usage: 25, paid: false }
      ]
    }
  }

  // Check if account exists in demo data
  const account = demoAccounts[accountNumber.toUpperCase()]

  if (account) {
    return NextResponse.json(account)
  }

  // For unknown accounts, return 404
  return NextResponse.json(
    { error: 'Account not found' },
    { status: 404 }
  )
}
