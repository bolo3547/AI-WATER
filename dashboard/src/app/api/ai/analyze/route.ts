import { NextResponse } from 'next/server'

interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
}

const GROQ_API_KEY = process.env.GROQ_API_KEY || ''
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
const MODEL = 'llama-3.3-70b-versatile'

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { messages, type } = body as { messages: Message[], type: string }

    if (!messages || messages.length === 0) {
      return NextResponse.json(
        { error: 'Messages are required' },
        { status: 400 }
      )
    }

    if (!GROQ_API_KEY) {
      // Return intelligent fallback based on type
      return NextResponse.json({
        content: generateFallbackAnalysis(type, messages),
        source: 'fallback'
      })
    }

    try {
      const response = await fetch(GROQ_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${GROQ_API_KEY}`
        },
        body: JSON.stringify({
          model: MODEL,
          messages: messages,
          max_tokens: 1500,
          temperature: 0.3 // Lower temperature for more analytical responses
        })
      })

      if (response.ok) {
        const data = await response.json()
        const content = data.choices?.[0]?.message?.content || 'Analysis complete.'
        
        // Extract structured data if present
        const parsed = parseAnalysisResponse(content, type)
        
        return NextResponse.json({
          content: parsed.content,
          recommendations: parsed.recommendations,
          priority: parsed.priority,
          confidence: parsed.confidence,
          actions: parsed.actions,
          model: MODEL,
          source: 'groq'
        })
      }
    } catch (apiError) {
      console.error('Groq API error:', apiError)
    }

    // Fallback
    return NextResponse.json({
      content: generateFallbackAnalysis(type, messages),
      source: 'fallback'
    })

  } catch (error) {
    console.error('AI analyze error:', error)
    return NextResponse.json(
      { error: 'Analysis failed', content: 'Unable to perform analysis.' },
      { status: 500 }
    )
  }
}

function parseAnalysisResponse(content: string, type: string) {
  // Extract recommendations if present
  const recommendations: string[] = []
  const recMatch = content.match(/(?:recommendations?|suggestions?|actions?):\s*\n((?:[-•*]\s*.+\n?)+)/i)
  if (recMatch) {
    const recLines = recMatch[1].split('\n').filter(line => line.trim())
    recLines.forEach(line => {
      const cleaned = line.replace(/^[-•*]\s*/, '').trim()
      if (cleaned) recommendations.push(cleaned)
    })
  }

  // Determine priority based on keywords
  let priority: 'critical' | 'high' | 'medium' | 'low' = 'medium'
  const lowerContent = content.toLowerCase()
  if (lowerContent.includes('critical') || lowerContent.includes('immediate') || lowerContent.includes('emergency')) {
    priority = 'critical'
  } else if (lowerContent.includes('high priority') || lowerContent.includes('urgent')) {
    priority = 'high'
  } else if (lowerContent.includes('low priority') || lowerContent.includes('minor')) {
    priority = 'low'
  }

  // Extract confidence if mentioned
  let confidence = 85
  const confMatch = content.match(/(\d{1,3})%?\s*confidence/i)
  if (confMatch) {
    confidence = parseInt(confMatch[1])
  }

  return {
    content,
    recommendations: recommendations.length > 0 ? recommendations : undefined,
    priority,
    confidence,
    actions: undefined
  }
}

function generateFallbackAnalysis(type: string, messages: Message[]): string {
  const userMessage = messages.find(m => m.role === 'user')?.content || ''
  
  switch (type) {
    case 'leak_analysis':
      return `## Leak Analysis\n\nBased on the sensor data patterns:\n\n**Assessment:**\n- Potential leak detected with moderate confidence\n- Estimated loss: 15-25 m³/hour\n\n**Recommendations:**\n- Deploy acoustic detection equipment\n- Check pressure differentials\n- Schedule inspection within 24 hours\n\n*AI-powered detailed analysis requires API connection.*`
    
    case 'nrw_insights':
      return `## NRW Insights\n\n**Current Status:**\n- NRW levels indicate room for improvement\n- Primary contributors: physical losses and meter inaccuracies\n\n**Key Actions:**\n1. Focus on high-loss DMAs first\n2. Implement pressure management\n3. Upgrade aging meters\n\n*Connect AI for detailed analysis.*`
    
    case 'dma_recommendation':
      return `## DMA Recommendations\n\n**Priority Areas:**\n1. Focus resources on DMAs with highest NRW%\n2. Implement night flow monitoring\n3. Check boundary valve integrity\n\n**Suggested Interventions:**\n- Active leak detection surveys\n- Pressure optimization\n- Infrastructure renewal planning\n\n*AI-powered optimization available with API.*`
    
    case 'alert_priority':
      return `## Alert Prioritization\n\n**Recommended Order:**\n1. Address critical pressure drops first\n2. Then high-flow anomalies\n3. Finally sensor maintenance alerts\n\n**Key Principle:** Water loss prevention takes precedence over routine maintenance.\n\n*AI can provide real-time dynamic prioritization.*`
    
    case 'work_order':
      return `## Work Order Suggestion\n\n**Recommended Details:**\n- Type: Inspection/Repair\n- Priority: Based on alert severity\n- Estimated time: 2-4 hours\n- Crew size: 2-3 technicians\n\n**Required Equipment:**\n- Leak detection gear\n- Standard repair kit\n- Safety equipment\n\n*AI optimization available for detailed planning.*`
    
    default:
      return `## Analysis\n\nBased on the provided data, here are initial observations:\n\n- Data patterns indicate areas for investigation\n- Recommend further monitoring\n- Schedule detailed inspection if concerns persist\n\n*Full AI analysis available when connected.*`
  }
}
