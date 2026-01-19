// Central AI Service for LWSC NRW Detection System
// Uses Groq API for intelligent analysis throughout the application

interface AIAnalysisRequest {
  type: 'leak_analysis' | 'nrw_insights' | 'dma_recommendation' | 'alert_priority' | 'work_order' | 'sensor_diagnosis' | 'trend_analysis' | 'general'
  context: any
  question?: string
}

interface AIAnalysisResponse {
  success: boolean
  analysis: string
  recommendations?: string[]
  priority?: 'critical' | 'high' | 'medium' | 'low'
  confidence?: number
  actions?: Array<{ action: string; urgency: string }>
}

// System prompts for different analysis types
const SYSTEM_PROMPTS: Record<string, string> = {
  leak_analysis: `You are an expert water utility AI analyzing leak detection data for LWSC (Lusaka Water & Sewerage Company). 
Analyze the provided sensor data and leak indicators to:
1. Assess leak severity and estimated water loss
2. Identify probable causes
3. Recommend immediate actions
4. Estimate repair priority and resources needed
Be concise, technical, and actionable. Format with markdown.`,

  nrw_insights: `You are an NRW (Non-Revenue Water) analysis expert for LWSC.
Analyze the provided NRW metrics to:
1. Identify key loss contributors
2. Compare against industry benchmarks (global avg ~30%)
3. Recommend specific reduction strategies
4. Calculate potential savings
Be data-driven and provide specific numbers. Format with markdown.`,

  dma_recommendation: `You are a District Metered Area (DMA) optimization expert for LWSC.
Analyze the DMA performance data to:
1. Identify underperforming areas
2. Recommend resource allocation
3. Suggest infrastructure improvements
4. Prioritize interventions by ROI
Be specific about which DMAs need attention. Format with markdown.`,

  alert_priority: `You are an intelligent alert prioritization system for LWSC.
Analyze the alert data to:
1. Rank alerts by urgency and impact
2. Identify related/cascading issues
3. Recommend response sequence
4. Estimate resources needed
Be decisive and clear about priorities. Format with markdown.`,

  work_order: `You are a work order optimization AI for LWSC field operations.
Based on the provided data:
1. Recommend work order details
2. Estimate completion time
3. List required parts/tools
4. Suggest optimal crew assignment
5. Identify safety considerations
Be practical and field-ready. Format with markdown.`,

  sensor_diagnosis: `You are an IoT sensor diagnostics expert for water utility systems.
Analyze the sensor data to:
1. Identify anomalies or malfunctions
2. Diagnose probable causes
3. Recommend calibration or maintenance
4. Predict potential failures
Be technical but clear. Format with markdown.`,

  trend_analysis: `You are a water utility trend analysis expert for LWSC.
Analyze the historical data to:
1. Identify significant trends
2. Detect seasonal patterns
3. Predict future issues
4. Recommend proactive measures
Use statistical insights. Format with markdown.`,

  general: `You are LWSC AI, an intelligent assistant for Lusaka Water & Sewerage Company.
Help with water utility operations, NRW reduction, leak detection, and system management.
Be helpful, professional, and data-driven. Format with markdown.`
}

export async function analyzeWithAI(request: AIAnalysisRequest): Promise<AIAnalysisResponse> {
  try {
    const systemPrompt = SYSTEM_PROMPTS[request.type] || SYSTEM_PROMPTS.general
    
    const messages = [
      { role: 'system', content: systemPrompt },
      { 
        role: 'user', 
        content: request.question 
          ? `${request.question}\n\nContext Data:\n${JSON.stringify(request.context, null, 2)}`
          : `Analyze this data and provide insights:\n${JSON.stringify(request.context, null, 2)}`
      }
    ]

    const response = await fetch('/api/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, type: request.type })
    })

    if (!response.ok) {
      throw new Error('AI analysis failed')
    }

    const data = await response.json()
    
    return {
      success: true,
      analysis: data.content || data.analysis,
      recommendations: data.recommendations,
      priority: data.priority,
      confidence: data.confidence,
      actions: data.actions
    }
  } catch (error) {
    console.error('AI analysis error:', error)
    return {
      success: false,
      analysis: 'Unable to perform AI analysis at this time.',
      recommendations: []
    }
  }
}

// Quick analysis functions for common use cases
export async function analyzeLeaks(leakData: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'leak_analysis',
    context: leakData
  })
  return result.analysis
}

export async function getNRWInsights(metrics: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'nrw_insights',
    context: metrics
  })
  return result.analysis
}

export async function getDMARecommendations(dmaData: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'dma_recommendation',
    context: dmaData
  })
  return result.analysis
}

export async function prioritizeAlerts(alerts: any[]): Promise<string> {
  const result = await analyzeWithAI({
    type: 'alert_priority',
    context: alerts
  })
  return result.analysis
}

export async function generateWorkOrderSuggestion(context: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'work_order',
    context
  })
  return result.analysis
}

export async function diagnoseSensor(sensorData: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'sensor_diagnosis',
    context: sensorData
  })
  return result.analysis
}

export async function analyzeTrends(historicalData: any): Promise<string> {
  const result = await analyzeWithAI({
    type: 'trend_analysis',
    context: historicalData
  })
  return result.analysis
}
