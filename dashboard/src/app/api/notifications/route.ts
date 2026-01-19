import { NextRequest, NextResponse } from 'next/server'

// Mock notifications database
const notifications = [
  {
    id: 'notif-1',
    type: 'alert',
    priority: 'high',
    title: 'Critical Leak Detected - Zone A4',
    message: 'Acoustic sensor detected high-frequency anomaly indicating probable main pipe burst. Estimated water loss: 45,000 L/hr.',
    timestamp: new Date().toISOString(),
    read: false,
    source: 'AI Leak Detection',
    actionUrl: '/actions'
  },
  {
    id: 'notif-2',
    type: 'warning',
    priority: 'high',
    title: 'Pipe Failure Prediction - Chilenje',
    message: 'AI predicts 87% probability of pipe failure within 14 days.',
    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    read: false,
    source: 'Predictive AI',
    actionUrl: '/predictions'
  }
]

// GET - Fetch notifications
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const unreadOnly = searchParams.get('unread') === 'true'
  const category = searchParams.get('category')
  const limit = parseInt(searchParams.get('limit') || '50')
  
  let filtered = [...notifications]
  
  if (unreadOnly) {
    filtered = filtered.filter(n => !n.read)
  }
  
  if (category && category !== 'all') {
    filtered = filtered.filter(n => 
      n.source?.toLowerCase().includes(category.toLowerCase())
    )
  }
  
  return NextResponse.json({
    success: true,
    notifications: filtered.slice(0, limit),
    total: filtered.length,
    unreadCount: notifications.filter(n => !n.read).length
  })
}

// POST - Create new notification
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const newNotification = {
      id: `notif-${Date.now()}`,
      type: body.type || 'info',
      priority: body.priority || 'medium',
      title: body.title,
      message: body.message,
      timestamp: new Date().toISOString(),
      read: false,
      source: body.source || 'System',
      actionUrl: body.actionUrl || '/notifications'
    }
    
    notifications.unshift(newNotification)
    
    // Keep only last 100 notifications
    while (notifications.length > 100) {
      notifications.pop()
    }
    
    return NextResponse.json({
      success: true,
      notification: newNotification
    })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to create notification'
    }, { status: 400 })
  }
}

// PATCH - Mark notification as read
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, action } = body
    
    if (action === 'markAllRead') {
      notifications.forEach(n => n.read = true)
      return NextResponse.json({ success: true, message: 'All notifications marked as read' })
    }
    
    if (action === 'markRead' && id) {
      const notification = notifications.find(n => n.id === id)
      if (notification) {
        notification.read = true
        return NextResponse.json({ success: true, notification })
      }
    }
    
    if (action === 'clearAll') {
      notifications.length = 0
      return NextResponse.json({ success: true, message: 'All notifications cleared' })
    }
    
    return NextResponse.json({
      success: false,
      error: 'Invalid action'
    }, { status: 400 })
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: 'Failed to update notification'
    }, { status: 400 })
  }
}
