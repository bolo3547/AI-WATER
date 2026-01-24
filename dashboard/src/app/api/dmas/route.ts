import { NextResponse } from 'next/server'
import clientPromise from '@/lib/mongodb'

export const dynamic = 'force-dynamic'

interface DMA {
  dma_id: string
  name: string
  nrw_percent: number | null
  priority_score: number | null
  status: 'critical' | 'warning' | 'healthy' | 'unknown'
  trend: 'up' | 'down' | 'stable' | 'unknown'
  connections: number
  pressure: number | null
  inflow: number | null
  consumption: number | null
  real_losses: number | null
  leak_count: number
  confidence: number | null
  last_updated: string | null
}

export async function GET() {
  try {
    const client = await clientPromise
    const db = client.db('lwsc_nrw')
    
    // Fetch real DMAs from database
    const dmas = await db.collection('dmas').find({}).toArray()
    
    if (dmas.length === 0) {
      // Return empty state - no fake data
      return NextResponse.json({
        success: true,
        data: [],
        data_available: false,
        message: 'No DMAs configured. Add DMAs in the admin panel to begin monitoring.',
        timestamp: new Date().toISOString()
      })
    }

    // Get latest sensor readings and leak counts for each DMA
    const enrichedDmas: DMA[] = await Promise.all(dmas.map(async (dma) => {
      // Count active leaks for this DMA
      const leakCount = await db.collection('leaks').countDocuments({
        dma_id: dma.dma_id,
        status: { $ne: 'resolved' }
      })

      // Get latest pressure reading for this DMA
      const latestReading = await db.collection('sensor_readings').findOne(
        { dma: dma.dma_id },
        { sort: { timestamp: -1 } }
      )

      // Determine status based on NRW percentage
      let status: DMA['status'] = 'unknown'
      if (dma.nrw_percent !== null && dma.nrw_percent !== undefined) {
        if (dma.nrw_percent > 40) status = 'critical'
        else if (dma.nrw_percent > 25) status = 'warning'
        else status = 'healthy'
      }

      return {
        dma_id: dma.dma_id || dma.id,
        name: dma.name || 'Unnamed DMA',
        nrw_percent: dma.nrw_percent ?? null,
        priority_score: dma.priority_score ?? null,
        status,
        trend: dma.trend || 'unknown',
        connections: dma.connections || 0,
        pressure: latestReading?.pressure ?? dma.pressure ?? null,
        inflow: dma.inflow ?? null,
        consumption: dma.consumption ?? null,
        real_losses: dma.real_losses ?? null,
        leak_count: leakCount,
        confidence: dma.confidence ?? null,
        last_updated: latestReading?.timestamp || dma.last_updated || null
      }
    }))

    return NextResponse.json({
      success: true,
      data: enrichedDmas,
      data_available: true,
      total: enrichedDmas.length,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('[DMAs API] Error:', error)
    return NextResponse.json({
      success: true,
      data: [],
      data_available: false,
      message: 'Database unavailable. Connect to MongoDB to see DMA data.',
      timestamp: new Date().toISOString()
    })
  }
}
