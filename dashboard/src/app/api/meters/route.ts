import { NextResponse } from 'next/server'

// Realistic LWSC DMAs with their characteristics
const LUSAKA_DMAS = [
  { name: 'Kabulonga', zone: 'High Income Residential', avgConsumption: 45, customerCount: 2847 },
  { name: 'Roma', zone: 'Commercial/Residential', avgConsumption: 380, customerCount: 1923 },
  { name: 'Chelstone', zone: 'Medium Density', avgConsumption: 28, customerCount: 4521 },
  { name: 'Matero', zone: 'Industrial/Commercial', avgConsumption: 720, customerCount: 3156 },
  { name: 'Woodlands', zone: 'High Income Residential', avgConsumption: 52, customerCount: 1876 },
  { name: 'Chilenje', zone: 'High Density', avgConsumption: 22, customerCount: 5234 },
  { name: 'Kalingalinga', zone: 'High Density', avgConsumption: 18, customerCount: 6842 },
  { name: 'Garden Compound', zone: 'Peri-Urban', avgConsumption: 15, customerCount: 8921 },
  { name: 'Kabwata', zone: 'Medium Density', avgConsumption: 32, customerCount: 3567 },
  { name: 'Northmead', zone: 'Commercial', avgConsumption: 285, customerCount: 1245 },
  { name: 'Longacres', zone: 'Commercial/Institutional', avgConsumption: 420, customerCount: 892 },
  { name: 'Chawama', zone: 'High Density', avgConsumption: 12, customerCount: 9234 },
  { name: 'Mandevu', zone: 'High Density', avgConsumption: 16, customerCount: 7123 },
  { name: 'Mtendere', zone: 'Medium Density', avgConsumption: 24, customerCount: 4892 },
  { name: 'PHI', zone: 'Industrial', avgConsumption: 1250, customerCount: 456 },
]

// Realistic Zambian business/customer names
const CUSTOMER_NAMES = {
  residential: [
    'Mutale Family', 'Mwansa Household', 'Banda Residence', 'Phiri Estate', 'Tembo Family',
    'Ng\'andu Apartment', 'Chanda Home', 'Mulenga House', 'Lungu Residence', 'Zulu Family',
    'Bwalya Compound', 'Musonda House', 'Kaunda Residence', 'Mumba Family', 'Siame Home'
  ],
  commercial: [
    'Shoprite Kabulonga', 'Melisa Supermarket', 'Zambeef Cold Storage', 'Trade Kings Ltd',
    'Mukuba Hotel', 'Intercontinental Lusaka', 'Manda Hill Shopping', 'Arcades Shopping Centre',
    'Levy Junction', 'Cairo Road Traders', 'Comesa Market', 'Garden City Mall',
    'Woodlands Mall', 'East Park Mall', 'University Teaching Hospital'
  ],
  industrial: [
    'Zambia Breweries', 'National Milling', 'Lafarge Zambia', 'Trade Kings Factory',
    'Zambia Sugar Depot', 'Nitrogen Chemicals', 'Metal Fabricators', 'Chilanga Cement Depot',
    'Bata Shoe Factory', 'Zambia Bottlers', 'ZESCO Substation', 'Water Treatment Plant'
  ],
  institutional: [
    'University of Zambia', 'Mulungushi Conference', 'Parliament Buildings', 'Cabinet Office',
    'Ministry of Health HQ', 'Zambia Revenue Authority', 'NAPSA House', 'Development House',
    'Levy Mwanawasa Hospital', 'Cancer Diseases Hospital', 'Chainama Hospital', 'CBU Campus'
  ]
}

// Generate realistic meter serial numbers
function generateMeterSerial(dma: string, index: number): string {
  const prefix = dma.substring(0, 3).toUpperCase()
  const year = '24' // Installation year
  const sequence = String(index + 1).padStart(5, '0')
  return `LWSC-${prefix}-${year}-${sequence}`
}

// Generate realistic account numbers
function generateAccountNumber(dma: string, index: number): string {
  const dmaCode = dma.substring(0, 3).toUpperCase()
  const areaCode = Math.floor(Math.random() * 9) + 1
  const sequence = String(10000 + index).substring(1)
  return `${dmaCode}/${areaCode}/${sequence}/2024`
}

// Simulate realistic consumption patterns based on time of day and customer type
function getCurrentConsumption(baseConsumption: number, customerType: string): number {
  const hour = new Date().getHours()
  let multiplier = 1.0
  
  // Time-based consumption patterns
  if (customerType === 'residential') {
    if (hour >= 6 && hour <= 9) multiplier = 1.8 // Morning peak
    else if (hour >= 18 && hour <= 21) multiplier = 1.6 // Evening peak
    else if (hour >= 0 && hour <= 5) multiplier = 0.3 // Night low
    else multiplier = 0.8
  } else if (customerType === 'commercial') {
    if (hour >= 8 && hour <= 17) multiplier = 1.5 // Business hours
    else if (hour >= 18 && hour <= 20) multiplier = 1.2 // Extended hours
    else multiplier = 0.2 // Closed
  } else if (customerType === 'industrial') {
    // Industrial operates mostly 24/7 with slight variation
    if (hour >= 6 && hour <= 22) multiplier = 1.2
    else multiplier = 0.8
  }
  
  // Add some random variation (±15%)
  const variation = (Math.random() * 0.3) - 0.15
  return Math.max(0, baseConsumption * multiplier * (1 + variation))
}

// Generate realistic smart meters
function generateMeters() {
  const meters: any[] = []
  let globalIndex = 0
  
  LUSAKA_DMAS.forEach(dma => {
    // Generate 3-8 meters per DMA for demo
    const meterCount = Math.floor(Math.random() * 6) + 3
    
    for (let i = 0; i < meterCount; i++) {
      globalIndex++
      
      // Determine customer type based on DMA zone
      let customerType: 'residential' | 'commercial' | 'industrial' | 'institutional'
      if (dma.zone.includes('Industrial')) customerType = 'industrial'
      else if (dma.zone.includes('Commercial')) customerType = Math.random() > 0.3 ? 'commercial' : 'institutional'
      else if (dma.zone.includes('High Income') || dma.zone.includes('Medium')) customerType = 'residential'
      else customerType = 'residential'
      
      // Get random customer name
      const names = CUSTOMER_NAMES[customerType]
      const customerName = names[Math.floor(Math.random() * names.length)] + 
        (customerType === 'residential' ? ` - ${dma.name}` : '')
      
      // Calculate base consumption with DMA characteristics
      const baseConsumption = dma.avgConsumption * (0.5 + Math.random())
      
      // Determine meter status (realistic distribution)
      const statusRand = Math.random()
      let status: 'online' | 'offline' | 'warning' | 'tampered'
      if (statusRand < 0.78) status = 'online'
      else if (statusRand < 0.88) status = 'warning'
      else if (statusRand < 0.95) status = 'offline'
      else status = 'tampered'
      
      // Generate meter reading (cumulative since installation)
      const monthsActive = Math.floor(Math.random() * 24) + 6 // 6-30 months
      const totalConsumption = baseConsumption * 30 * monthsActive
      const lastReading = Math.round(totalConsumption * 100) / 100
      
      // Today's consumption
      const consumption = status === 'offline' ? 0 : 
        Math.round(getCurrentConsumption(baseConsumption, customerType) * 100) / 100
      
      // Previous reading (yesterday)
      const previousReading = Math.round((lastReading - consumption) * 100) / 100
      
      // Battery and signal based on status
      const battery = status === 'offline' ? Math.floor(Math.random() * 20) :
        status === 'warning' ? Math.floor(Math.random() * 30) + 40 :
        Math.floor(Math.random() * 30) + 70
      
      const signalStrength = status === 'offline' ? 0 :
        status === 'warning' ? Math.floor(Math.random() * 2) + 2 :
        Math.floor(Math.random() * 2) + 4
      
      // Last contact time
      const lastContactMinutes = status === 'online' ? Math.floor(Math.random() * 15) :
        status === 'warning' ? Math.floor(Math.random() * 60) + 30 :
        status === 'offline' ? Math.floor(Math.random() * 4320) + 1440 : // 1-4 days
        Math.floor(Math.random() * 180) + 60
      
      const lastContact = lastContactMinutes < 60 ? 
        `${lastContactMinutes} min ago` :
        lastContactMinutes < 1440 ? 
        `${Math.floor(lastContactMinutes / 60)} hours ago` :
        `${Math.floor(lastContactMinutes / 1440)} days ago`
      
      // Generate alerts based on status
      const alerts: string[] = []
      if (status === 'warning') {
        const warningAlerts = ['High consumption detected', 'Low battery warning', 'Pressure fluctuation', 'Unusual pattern detected']
        alerts.push(warningAlerts[Math.floor(Math.random() * warningAlerts.length)])
      } else if (status === 'offline') {
        alerts.push('No communication')
        if (battery < 15) alerts.push('Battery critical')
      } else if (status === 'tampered') {
        const tamperAlerts = ['Reverse flow detected', 'Magnetic interference', 'Meter bypass suspected', 'Seal broken alert']
        alerts.push(tamperAlerts[Math.floor(Math.random() * tamperAlerts.length)])
        alerts.push('Investigation required')
      }
      
      // Meter type based on customer type and consumption
      const meterType = baseConsumption > 500 ? 'electromagnetic' :
        baseConsumption > 100 ? 'ultrasonic' :
        customerType === 'residential' && Math.random() > 0.7 ? 'mechanical' : 'amr'
      
      // Calculate anomaly score
      let anomalyScore = 5
      if (status === 'tampered') anomalyScore = 85 + Math.floor(Math.random() * 15)
      else if (status === 'offline') anomalyScore = 60 + Math.floor(Math.random() * 20)
      else if (status === 'warning') anomalyScore = 40 + Math.floor(Math.random() * 30)
      else anomalyScore = Math.floor(Math.random() * 25)
      
      // Lusaka coordinates with variation per DMA
      const baseLat = -15.4167
      const baseLng = 28.2833
      const latOffset = (Math.random() - 0.5) * 0.15
      const lngOffset = (Math.random() - 0.5) * 0.15
      
      meters.push({
        id: generateMeterSerial(dma.name, i),
        accountNumber: generateAccountNumber(dma.name, globalIndex),
        customerName,
        customerType,
        location: `${dma.name} Area, Lusaka`,
        dma: dma.name,
        zone: dma.zone,
        meterType,
        status,
        lastReading,
        previousReading,
        consumption,
        avgConsumption: Math.round(baseConsumption * 100) / 100,
        battery,
        signalStrength,
        lastContact,
        alerts,
        anomalyScore,
        coordinates: {
          lat: Math.round((baseLat + latOffset) * 10000) / 10000,
          lng: Math.round((baseLng + lngOffset) * 10000) / 10000
        },
        installedDate: new Date(Date.now() - monthsActive * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        lastMaintenance: new Date(Date.now() - Math.floor(Math.random() * 90) * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      })
    }
  })
  
  return meters.sort((a, b) => b.anomalyScore - a.anomalyScore)
}

// Generate consumption anomalies
function generateAnomalies(meters: any[]) {
  const anomalies: any[] = []
  
  meters.filter(m => m.status !== 'online' || m.anomalyScore > 30).forEach(meter => {
    let anomalyType: string
    let severity: string
    
    if (meter.status === 'tampered') {
      anomalyType = Math.random() > 0.5 ? 'reverse_flow' : 'tampering'
      severity = 'critical'
    } else if (meter.status === 'offline') {
      anomalyType = 'zero_consumption'
      severity = meter.battery < 15 ? 'high' : 'medium'
    } else if (meter.consumption > meter.avgConsumption * 1.5) {
      anomalyType = 'sudden_increase'
      severity = meter.consumption > meter.avgConsumption * 2 ? 'high' : 'medium'
    } else if (meter.consumption < meter.avgConsumption * 0.3 && meter.consumption > 0) {
      anomalyType = 'sudden_decrease'
      severity = 'low'
    } else {
      return // No anomaly
    }
    
    const deviation = meter.avgConsumption > 0 ? 
      Math.round(((meter.consumption - meter.avgConsumption) / meter.avgConsumption) * 100) : 0
    
    anomalies.push({
      meterId: meter.id,
      accountNumber: meter.accountNumber,
      customerName: meter.customerName,
      dma: meter.dma,
      anomalyType,
      severity,
      detectedAt: new Date(Date.now() - Math.floor(Math.random() * 48) * 60 * 60 * 1000).toISOString(),
      currentConsumption: meter.consumption,
      expectedConsumption: meter.avgConsumption,
      deviation,
      status: Math.random() > 0.6 ? 'new' : Math.random() > 0.3 ? 'investigating' : 'resolved',
      estimatedLoss: anomalyType === 'tampering' || anomalyType === 'reverse_flow' ? 
        Math.round(meter.avgConsumption * 30 * 15.5) : 0 // K15.50 per m³
    })
  })
  
  return anomalies.sort((a, b) => {
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
    return (severityOrder[a.severity as keyof typeof severityOrder] || 4) - 
           (severityOrder[b.severity as keyof typeof severityOrder] || 4)
  })
}

// GET endpoint
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const type = searchParams.get('type') || 'all'
  const dma = searchParams.get('dma')
  const status = searchParams.get('status')
  
  const meters = generateMeters()
  const anomalies = generateAnomalies(meters)
  
  // Filter meters if needed
  let filteredMeters = meters
  if (dma) {
    filteredMeters = filteredMeters.filter(m => m.dma === dma)
  }
  if (status) {
    filteredMeters = filteredMeters.filter(m => m.status === status)
  }
  
  // Calculate summary stats
  const stats = {
    totalMeters: meters.length,
    online: meters.filter(m => m.status === 'online').length,
    offline: meters.filter(m => m.status === 'offline').length,
    warning: meters.filter(m => m.status === 'warning').length,
    tampered: meters.filter(m => m.status === 'tampered').length,
    totalConsumptionToday: Math.round(meters.reduce((sum, m) => sum + m.consumption, 0)),
    avgBattery: Math.round(meters.reduce((sum, m) => sum + m.battery, 0) / meters.length),
    activeAnomalies: anomalies.filter(a => a.status !== 'resolved').length,
    estimatedLossToday: Math.round(anomalies.reduce((sum, a) => sum + (a.estimatedLoss || 0), 0) / 30),
    dmaBreakdown: LUSAKA_DMAS.map(d => ({
      name: d.name,
      meterCount: meters.filter(m => m.dma === d.name).length,
      consumption: Math.round(meters.filter(m => m.dma === d.name).reduce((sum, m) => sum + m.consumption, 0)),
      issues: meters.filter(m => m.dma === d.name && m.status !== 'online').length
    }))
  }
  
  if (type === 'meters') {
    return NextResponse.json({ meters: filteredMeters, stats })
  } else if (type === 'anomalies') {
    return NextResponse.json({ anomalies, stats })
  } else if (type === 'stats') {
    return NextResponse.json({ stats })
  }
  
  return NextResponse.json({
    meters: filteredMeters,
    anomalies,
    stats,
    lastUpdated: new Date().toISOString()
  })
}
