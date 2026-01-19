import { NextRequest, NextResponse } from 'next/server'
import { getMessagesCollection, initializeDatabase, Message } from '@/lib/mongodb'

// Initialize database on first request
let initialized = false

async function ensureInitialized() {
  if (!initialized) {
    try {
      await initializeDatabase()
      initialized = true
    } catch (error) {
      console.error('[Messages API] Failed to initialize database:', error)
    }
  }
}

// GET - Fetch messages
export async function GET(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user')
    const workOrderId = searchParams.get('work_order')
    
    const collection = await getMessagesCollection()
    
    // Build query filter
    const filter: any = {}
    if (userId) {
      filter.$or = [
        { from_user: userId },
        { to_user: userId }
      ]
    }
    if (workOrderId) {
      filter.work_order_id = workOrderId
    }
    
    // Fetch from MongoDB, sorted by timestamp descending
    const messages = await collection
      .find(filter)
      .sort({ timestamp: -1 })
      .limit(100)
      .toArray()
    
    console.log(`[Messages API] Fetched ${messages.length} messages from MongoDB`)
    
    return NextResponse.json({
      success: true,
      data: messages,
      total: messages.length,
      source: 'mongodb',
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('[Messages API] Error fetching messages:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to fetch messages',
      data: []
    }, { status: 500 })
  }
}

// POST - Send new message
export async function POST(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    
    // Validate required fields
    if (!body.content || !body.from_user || !body.to_user) {
      return NextResponse.json(
        { success: false, error: 'Content, from_user, and to_user are required' },
        { status: 400 }
      )
    }
    
    const collection = await getMessagesCollection()
    
    // Generate unique ID
    const newId = `msg-${Date.now()}-${Math.random().toString(36).substring(7)}`
    
    const newMessage: Message = {
      id: newId,
      from_user: body.from_user,
      from_role: body.from_role || 'user',
      to_user: body.to_user,
      to_role: body.to_role || 'user',
      content: body.content,
      work_order_id: body.work_order_id,
      timestamp: new Date().toISOString(),
      read: false
    }
    
    // Insert into MongoDB
    const result = await collection.insertOne(newMessage as any)
    
    console.log(`[Messages API] Sent message: ${newId} from ${body.from_user} to ${body.to_user}`)
    
    return NextResponse.json({
      success: true,
      data: { ...newMessage, _id: result.insertedId },
      message: 'Message sent successfully',
      source: 'mongodb'
    }, { status: 201 })
    
  } catch (error) {
    console.error('[Messages API] Error sending message:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to send message'
    }, { status: 500 })
  }
}

// PUT - Mark messages as read
export async function PUT(request: NextRequest) {
  try {
    await ensureInitialized()
    
    const body = await request.json()
    const { messageIds, userId } = body
    
    const collection = await getMessagesCollection()
    
    let filter: any = {}
    
    if (messageIds && messageIds.length > 0) {
      // Mark specific messages as read
      filter = { id: { $in: messageIds } }
    } else if (userId) {
      // Mark all messages to this user as read
      filter = { to_user: userId, read: false }
    } else {
      return NextResponse.json(
        { success: false, error: 'messageIds or userId required' },
        { status: 400 }
      )
    }
    
    // Update in MongoDB
    const result = await collection.updateMany(
      filter,
      { $set: { read: true } }
    )
    
    console.log(`[Messages API] Marked ${result.modifiedCount} messages as read`)
    
    return NextResponse.json({
      success: true,
      modifiedCount: result.modifiedCount,
      message: 'Messages marked as read',
      source: 'mongodb'
    })
    
  } catch (error) {
    console.error('[Messages API] Error updating messages:', error)
    return NextResponse.json({
      success: false,
      error: 'Failed to update messages'
    }, { status: 500 })
  }
}
