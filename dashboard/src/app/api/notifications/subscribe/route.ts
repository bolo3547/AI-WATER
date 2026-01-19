import { NextRequest, NextResponse } from 'next/server'

// In-memory storage for push subscriptions (use database in production)
const pushSubscriptions: Map<string, any> = new Map()

// POST - Subscribe to push notifications
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { subscription, userId } = body
    
    if (!subscription || !subscription.endpoint) {
      return NextResponse.json({
        success: false,
        error: 'Invalid subscription'
      }, { status: 400 })
    }
    
    // Store subscription (in production, save to database)
    const subscriptionId = `sub-${Date.now()}`
    pushSubscriptions.set(subscriptionId, {
      ...subscription,
      userId: userId || 'anonymous',
      subscribedAt: new Date().toISOString()
    })
    
    console.log('Push subscription registered:', subscriptionId)
    
    return NextResponse.json({
      success: true,
      subscriptionId,
      message: 'Push notifications enabled'
    })
  } catch (error) {
    console.error('Push subscription failed:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to subscribe'
    }, { status: 500 })
  }
}

// DELETE - Unsubscribe from push notifications
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const subscriptionId = searchParams.get('id')
    
    if (subscriptionId && pushSubscriptions.has(subscriptionId)) {
      pushSubscriptions.delete(subscriptionId)
      return NextResponse.json({
        success: true,
        message: 'Unsubscribed from push notifications'
      })
    }
    
    return NextResponse.json({
      success: false,
      error: 'Subscription not found'
    }, { status: 404 })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to unsubscribe'
    }, { status: 500 })
  }
}

// GET - Get subscription status
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const userId = searchParams.get('userId')
  
  // Find subscriptions for user
  const userSubscriptions = Array.from(pushSubscriptions.entries())
    .filter(([_, sub]) => sub.userId === userId)
    .map(([id, sub]) => ({
      id,
      subscribedAt: sub.subscribedAt
    }))
  
  return NextResponse.json({
    success: true,
    subscribed: userSubscriptions.length > 0,
    subscriptions: userSubscriptions,
    totalSubscriptions: pushSubscriptions.size
  })
}
