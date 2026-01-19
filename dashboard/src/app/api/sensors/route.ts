import { NextResponse } from 'next/server'

function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export async function GET() {
  const now = new Date()
  const sensors = []

  for (let i = 1; i <= 26; i++) {
    const dma = `DMA-00${(i % 5) + 1}`
    const sensorType = i % 2 === 0 ? 'pressure' : 'flow'
    const value = sensorType === 'pressure'
      ? parseFloat((3.0 + randomFloat(-0.5, 0.5)).toFixed(1))
      : Math.round(50 + randomFloat(-10, 10))

    sensors.push({
      id: `${sensorType === 'pressure' ? 'PRESS' : 'FLOW'}-${String(i).padStart(3, '0')}`,
      type: sensorType,
      dma: dma,
      value: value,
      unit: sensorType === 'pressure' ? 'bar' : 'm³/h',
      status: Math.random() < 0.08 ? 'offline' : 'online',
      battery: randomInt(60, 100),
      last_reading: new Date(now.getTime() - randomInt(1, 15) * 60 * 1000).toISOString()
    })
  }

  return NextResponse.json(sensors)
}
