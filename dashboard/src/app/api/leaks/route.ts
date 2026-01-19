import { NextRequest, NextResponse } from 'next/server'
import { MongoClient } from 'mongodb'

// MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || ''
let cachedClient: MongoClient | null = null

async function getDb() {
  if (!MONGODB_URI) return null
  try {
    if (!cachedClient) {
      cachedClient = new MongoClient(MONGODB_URI)
      await cachedClient.connect()
    }
    return cachedClient.db('lwsc_nrw')
  } catch (error) {
    console.error('MongoDB connection error:', error)
    return null
  }
}

interface Leak {
  id: string
  location: string
  dma_id: string
  estimated_loss: number
  priority: 'high' | 'medium' | 'low'
  confidence: number
  detected_at: string
  status: 'new' | 'acknowledged' | 'dispatched' | 'resolved'
  acknowledged_by?: string
  acknowledged_at?: string
  dispatched_at?: string
  resolved_at?: string
  notes?: string
}

// Fallback in-memory store
let leaksStore: Leak[] = []

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status')
  
  try {
    const db = await getDb()
    
    if (db) {
      const query: Record<string, unknown> = {}
      if (status && status !== 'all') query.status = status
      
      const leaks = await db.collection('leaks').find(query).sort({ detected_at: -1 }).toArray()
      
      return NextResponse.json({
        success: true,
        data: leaks,
        total: leaks.length,
        source: 'mongodb',
        message: leaks.length === 0 ? 'No active leaks detected.' : `${leaks.length} leak alert(s)`,
        timestamp: new Date().toISOString()
      })
    }
    
    // Fallback to memory
    let leaks = [...leaksStore]
    if (status && status !== 'all') leaks = leaks.filter(l => l.status === status)
    
    return NextResponse.json({
      success: true,
      data: leaks,
      total: leaks.length,
      source: 'memory',
      message: leaks.length === 0 ? 'No active leaks detected.' : `${leaks.length} leak alert(s)`,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    console.error('GET leaks error:', error)
    return NextResponse.json({ success: false, data: [], error: 'Failed to fetch leaks' }, { status: 500 })
  }
}

// POST - Create new leak
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const newLeak: Leak = {
      id: `LEAK-${Date.now()}`,
      location: body.location || 'Unknown Location',
      dma_id: body.dma_id || 'DMA-001',
      estimated_loss: body.estimated_loss || 0,
      priority: body.priority || 'medium',
      confidence: body.confidence || 75,
      detected_at: body.detected_at || new Date().toISOString(),
      status: 'new',
      notes: body.notes
    }
    
    const db = await getDb()
    if (db) {
      await db.collection('leaks').insertOne(newLeak)
    } else {
      leaksStore.unshift(newLeak)
    }
    
    return NextResponse.json({ success: true, data: newLeak, message: 'Leak alert created' })
  } catch (error) {
    console.error('POST leak error:', error)
    return NextResponse.json({ success: false, error: 'Failed to create leak' }, { status: 400 })
  }
}

// PATCH - Update leak status
export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, action, user } = body
    const now = new Date().toISOString()
    
    const update: Record<string, unknown> = {}
    switch (action) {
      case 'acknowledge':
        update.status = 'acknowledged'
        update.acknowledged_by = user || 'Operator'
        update.acknowledged_at = now
        break
      case 'dispatch':
        update.status = 'dispatched'
        update.dispatched_at = now
        break
      case 'resolve':
        update.status = 'resolved'
        update.resolved_at = now
        break
      default:
        return NextResponse.json({ success: false, error: 'Invalid action' }, { status: 400 })
    }
    
    const db = await getDb()
    if (db) {
      const result = await db.collection('leaks').findOneAndUpdate(
        { id },
        { $set: update },
        { returnDocument: 'after' }
      )
      if (result) {
        return NextResponse.json({ success: true, data: result, message: `Leak ${action}d` })
      }
    } else {
      const idx = leaksStore.findIndex(l => l.id === id)
      if (idx !== -1) {
        leaksStore[idx] = { ...leaksStore[idx], ...update } as Leak
        return NextResponse.json({ success: true, data: leaksStore[idx], message: `Leak ${action}d` })
      }
    }
    
    return NextResponse.json({ success: false, error: 'Leak not found' }, { status: 404 })
  } catch (error) {
    console.error('PATCH leak error:', error)
    return NextResponse.json({ success: false, error: 'Failed to update leak' }, { status: 500 })
  }
}

// DELETE - Remove leak
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const id = searchParams.get('id')
    
    if (!id) return NextResponse.json({ success: false, error: 'Leak ID required' }, { status: 400 })
    
    const db = await getDb()
    if (db) {
      await db.collection('leaks').deleteOne({ id })
    } else {
      leaksStore = leaksStore.filter(l => l.id !== id)
    }
    
    return NextResponse.json({ success: true, message: 'Leak deleted' })
  } catch (error) {
    console.error('DELETE leak error:', error)
    return NextResponse.json({ success: false, error: 'Failed to delete leak' }, { status: 500 })
  }
}
