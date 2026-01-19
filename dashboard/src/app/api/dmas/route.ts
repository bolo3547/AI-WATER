import { NextResponse } from 'next/server'

function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

export async function GET() {
  const dmas = [
    {
      dma_id: "dma-001",
      name: "Kabulonga North",
      nrw_percent: parseFloat((45.2 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 87,
      status: "critical" as const,
      trend: "up" as const,
      connections: 1250,
      pressure: parseFloat((2.1 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 1250,
      consumption: 685,
      real_losses: 565,
      leak_count: 3,
      confidence: 92,
      last_updated: new Date().toISOString()
    },
    {
      dma_id: "dma-002",
      name: "Roma Industrial",
      nrw_percent: parseFloat((38.7 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 72,
      status: "warning" as const,
      trend: "stable" as const,
      connections: 2100,
      pressure: parseFloat((2.8 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 980,
      consumption: 600,
      real_losses: 380,
      leak_count: 2,
      confidence: 88,
      last_updated: new Date().toISOString()
    },
    {
      dma_id: "dma-003",
      name: "Longacres",
      nrw_percent: parseFloat((31.5 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 58,
      status: "warning" as const,
      trend: "down" as const,
      connections: 450,
      pressure: parseFloat((3.2 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 720,
      consumption: 490,
      real_losses: 230,
      leak_count: 1,
      confidence: 91,
      last_updated: new Date().toISOString()
    },
    {
      dma_id: "dma-004",
      name: "Chelstone East",
      nrw_percent: parseFloat((28.3 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 45,
      status: "healthy" as const,
      trend: "down" as const,
      connections: 1800,
      pressure: parseFloat((3.5 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 850,
      consumption: 610,
      real_losses: 240,
      leak_count: 0,
      confidence: 95,
      last_updated: new Date().toISOString()
    },
    {
      dma_id: "dma-005",
      name: "Woodlands Central",
      nrw_percent: parseFloat((35.8 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 65,
      status: "warning" as const,
      trend: "stable" as const,
      connections: 980,
      pressure: parseFloat((3.0 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 920,
      consumption: 590,
      real_losses: 330,
      leak_count: 2,
      confidence: 89,
      last_updated: new Date().toISOString()
    },
    {
      dma_id: "dma-006",
      name: "Chilenje South",
      nrw_percent: parseFloat((22.1 + randomFloat(-2, 2)).toFixed(1)),
      priority_score: 32,
      status: "healthy" as const,
      trend: "down" as const,
      connections: 1450,
      pressure: parseFloat((3.4 + randomFloat(-0.2, 0.2)).toFixed(1)),
      inflow: 680,
      consumption: 530,
      real_losses: 150,
      leak_count: 0,
      confidence: 96,
      last_updated: new Date().toISOString()
    }
  ]

  return NextResponse.json(dmas)
}
