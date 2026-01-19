import { NextResponse } from 'next/server'

// Realistic LWSC pipe network data
const LUSAKA_DMAS = [
  { name: 'Kabulonga', zone: 'High Income', pipeKm: 45.2, avgAge: 35 },
  { name: 'Roma', zone: 'Commercial', pipeKm: 28.7, avgAge: 32 },
  { name: 'Chelstone', zone: 'Medium Density', pipeKm: 52.3, avgAge: 28 },
  { name: 'Matero', zone: 'Industrial', pipeKm: 38.9, avgAge: 42 },
  { name: 'Woodlands', zone: 'High Income', pipeKm: 31.5, avgAge: 25 },
  { name: 'Chilenje', zone: 'High Density', pipeKm: 48.6, avgAge: 38 },
  { name: 'Kalingalinga', zone: 'High Density', pipeKm: 22.4, avgAge: 45 },
  { name: 'Garden Compound', zone: 'Peri-Urban', pipeKm: 18.9, avgAge: 30 },
  { name: 'Kabwata', zone: 'Medium Density', pipeKm: 35.2, avgAge: 34 },
  { name: 'Northmead', zone: 'Commercial', pipeKm: 24.8, avgAge: 28 },
  { name: 'Longacres', zone: 'Institutional', pipeKm: 19.3, avgAge: 32 },
  { name: 'PHI', zone: 'Industrial', pipeKm: 42.1, avgAge: 48 },
  { name: 'Chawama', zone: 'High Density', pipeKm: 26.5, avgAge: 40 },
  { name: 'Mtendere', zone: 'Medium Density', pipeKm: 33.7, avgAge: 36 },
  { name: 'Avondale', zone: 'High Income', pipeKm: 21.4, avgAge: 22 },
]

const PIPE_MATERIALS = [
  { type: 'Cast Iron', avgLife: 50, failureRate: 0.15, description: 'Legacy infrastructure, prone to corrosion' },
  { type: 'Asbestos Cement', avgLife: 40, failureRate: 0.12, description: 'Common in older areas, brittle' },
  { type: 'Ductile Iron', avgLife: 60, failureRate: 0.08, description: 'Modern replacement, more durable' },
  { type: 'PVC', avgLife: 50, failureRate: 0.06, description: 'Used in medium pressure zones' },
  { type: 'HDPE', avgLife: 75, failureRate: 0.04, description: 'Newest installations, flexible' },
  { type: 'Galvanized Steel', avgLife: 35, failureRate: 0.18, description: 'Service connections, corrosion prone' },
]

const RISK_FACTORS = [
  { factor: 'Age >40 years', weight: 25, description: 'Infrastructure exceeds design life' },
  { factor: 'Age >30 years', weight: 18, description: 'Approaching end of service life' },
  { factor: 'Previous Repairs', weight: 15, description: 'History of failures in segment' },
  { factor: 'High Pressure Zone', weight: 12, description: 'Exceeds 60m head pressure' },
  { factor: 'Corrosion Detected', weight: 20, description: 'Wall thickness reduction >20%' },
  { factor: 'Soil Movement', weight: 10, description: 'Expansive or unstable soils' },
  { factor: 'Traffic Vibration', weight: 8, description: 'Heavy vehicle routes overhead' },
  { factor: 'Water Hammer Events', weight: 15, description: 'Pressure transients recorded' },
  { factor: 'Joint Weakness', weight: 12, description: 'Lead or mechanical joint degradation' },
  { factor: 'Chemical Exposure', weight: 10, description: 'Industrial contamination risk' },
  { factor: 'Temperature Stress', weight: 8, description: 'Thermal expansion cycles' },
  { factor: 'Root Intrusion Risk', weight: 6, description: 'Trees near pipe alignment' },
]

const LUSAKA_LOCATIONS = [
  'Main Road near Market', 'Shopping Centre Area', 'School Junction', 'Hospital Access Road',
  'Industrial Park Entry', 'Residential Block A', 'Commercial District', 'Government Complex',
  'Near Water Tank', 'Transmission Main', 'Distribution Network', 'Service Connection Zone',
  'Pressure Zone Boundary', 'Metering Point', 'Valve Chamber Area', 'Intersection Point'
]

function generatePipeId(dma: string, index: number): string {
  const prefix = dma.substring(0, 3).toUpperCase()
  const sequence = String(1000 + index).substring(1)
  return `PIPE-${prefix}-${sequence}`
}

function calculateFailureProbability(age: number, material: typeof PIPE_MATERIALS[0], riskFactors: string[]): number {
  // Base probability from age relative to material life expectancy
  const ageRatio = age / material.avgLife
  let probability = Math.min(95, Math.max(5, ageRatio * 50 + material.failureRate * 100))
  
  // Add risk factor contributions
  riskFactors.forEach(rf => {
    const factor = RISK_FACTORS.find(f => f.factor === rf)
    if (factor) {
      probability += factor.weight * 0.8
    }
  })
  
  // Cap at 98%
  return Math.min(98, Math.round(probability))
}

function predictFailureDate(probability: number): string {
  // Higher probability = sooner failure
  const daysAhead = Math.max(7, Math.round(365 * (1 - probability / 100) + Math.random() * 60))
  const date = new Date()
  date.setDate(date.getDate() + daysAhead)
  return date.toISOString().split('T')[0]
}

function generatePredictions() {
  const predictions: any[] = []
  let globalIndex = 0
  
  LUSAKA_DMAS.forEach(dma => {
    // Generate 2-5 predictions per DMA based on pipe network size
    const predictionCount = Math.floor(Math.random() * 4) + 2
    
    for (let i = 0; i < predictionCount; i++) {
      globalIndex++
      
      // Select material based on DMA age
      const materialIndex = dma.avgAge > 35 ? 
        Math.floor(Math.random() * 3) : // Older materials
        Math.floor(Math.random() * 3) + 2 // Newer materials
      const material = PIPE_MATERIALS[Math.min(materialIndex, PIPE_MATERIALS.length - 1)]
      
      // Pipe age with variation
      const pipeAge = Math.max(5, Math.round(dma.avgAge + (Math.random() - 0.5) * 20))
      
      // Select risk factors (2-5 factors)
      const factorCount = Math.floor(Math.random() * 4) + 2
      const selectedFactors: string[] = []
      
      // Add age-based factor
      if (pipeAge > 40) selectedFactors.push('Age >40 years')
      else if (pipeAge > 30) selectedFactors.push('Age >30 years')
      
      // Add random factors
      while (selectedFactors.length < factorCount) {
        const factor = RISK_FACTORS[Math.floor(Math.random() * RISK_FACTORS.length)]
        if (!selectedFactors.includes(factor.factor) && !factor.factor.includes('Age')) {
          selectedFactors.push(factor.factor)
        }
      }
      
      const failureProbability = calculateFailureProbability(pipeAge, material, selectedFactors)
      const predictedDate = predictFailureDate(failureProbability)
      
      // Estimated water loss (m³/day) based on pipe size and DMA
      const estimatedLoss = Math.round((dma.zone.includes('Industrial') ? 400 : 
        dma.zone.includes('Commercial') ? 250 : 120) * (0.5 + Math.random()))
      
      // Repair cost based on material and location
      const repairCost = Math.round((material.type.includes('Iron') ? 15000 : 8000) * 
        (dma.zone.includes('Commercial') ? 1.3 : 1) * (0.8 + Math.random() * 0.4))
      
      // Priority based on probability
      const priority = failureProbability >= 80 ? 'critical' :
        failureProbability >= 60 ? 'high' :
        failureProbability >= 40 ? 'medium' : 'low'
      
      // Trend
      const trend = failureProbability >= 70 ? 'increasing' :
        Math.random() > 0.5 ? 'stable' : 'decreasing'
      
      // Location description
      const location = `${dma.name} ${LUSAKA_LOCATIONS[Math.floor(Math.random() * LUSAKA_LOCATIONS.length)]}`
      
      // Last inspection date (random within past 18 months)
      const inspectionDaysAgo = Math.floor(Math.random() * 540) + 30
      const lastInspection = new Date(Date.now() - inspectionDaysAgo * 24 * 60 * 60 * 1000)
        .toISOString().split('T')[0]
      
      // Lusaka coordinates
      const baseLat = -15.4167
      const baseLng = 28.2833
      const latOffset = (Math.random() - 0.5) * 0.15
      const lngOffset = (Math.random() - 0.5) * 0.15
      
      predictions.push({
        id: `PRED-${String(globalIndex).padStart(3, '0')}`,
        pipeId: generatePipeId(dma.name, i),
        location,
        dma: dma.name,
        zone: dma.zone,
        failureProbability,
        predictedDate,
        riskFactors: selectedFactors,
        pipeAge,
        pipeMaterial: material.type,
        pipeLength: Math.round(50 + Math.random() * 450), // 50-500m segments
        pipeDiameter: [100, 150, 200, 250, 300, 400][Math.floor(Math.random() * 6)], // mm
        lastInspection,
        estimatedLoss,
        repairCost,
        priority,
        trend,
        coordinates: {
          lat: Math.round((baseLat + latOffset) * 10000) / 10000,
          lng: Math.round((baseLng + lngOffset) * 10000) / 10000
        },
        confidence: Math.round(75 + Math.random() * 20), // AI confidence 75-95%
        modelVersion: 'LWSC-AI-v2.4',
        lastUpdated: new Date().toISOString()
      })
    }
  })
  
  // Sort by failure probability (highest first)
  return predictions.sort((a, b) => b.failureProbability - a.failureProbability)
}

// GET endpoint
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const dma = searchParams.get('dma')
  const priority = searchParams.get('priority')
  const limit = parseInt(searchParams.get('limit') || '50')
  
  let predictions = generatePredictions()
  
  // Apply filters
  if (dma) {
    predictions = predictions.filter(p => p.dma === dma)
  }
  if (priority) {
    predictions = predictions.filter(p => p.priority === priority)
  }
  
  // Limit results
  predictions = predictions.slice(0, limit)
  
  // Calculate summary stats
  const stats = {
    totalPredictions: predictions.length,
    critical: predictions.filter(p => p.priority === 'critical').length,
    high: predictions.filter(p => p.priority === 'high').length,
    medium: predictions.filter(p => p.priority === 'medium').length,
    low: predictions.filter(p => p.priority === 'low').length,
    totalEstimatedLoss: Math.round(predictions.reduce((sum, p) => sum + p.estimatedLoss, 0)),
    totalRepairCost: predictions.reduce((sum, p) => sum + p.repairCost, 0),
    avgProbability: Math.round(predictions.reduce((sum, p) => sum + p.failureProbability, 0) / predictions.length),
    next30Days: predictions.filter(p => {
      const date = new Date(p.predictedDate)
      const now = new Date()
      const diff = (date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
      return diff <= 30
    }).length,
    byDMA: LUSAKA_DMAS.map(d => ({
      name: d.name,
      count: predictions.filter(p => p.dma === d.name).length,
      critical: predictions.filter(p => p.dma === d.name && p.priority === 'critical').length
    })),
    byMaterial: PIPE_MATERIALS.map(m => ({
      type: m.type,
      count: predictions.filter(p => p.pipeMaterial === m.type).length,
      avgProbability: Math.round(
        predictions.filter(p => p.pipeMaterial === m.type)
          .reduce((sum, p) => sum + p.failureProbability, 0) / 
        (predictions.filter(p => p.pipeMaterial === m.type).length || 1)
      )
    }))
  }
  
  return NextResponse.json({
    predictions,
    stats,
    riskFactors: RISK_FACTORS,
    lastUpdated: new Date().toISOString()
  })
}
