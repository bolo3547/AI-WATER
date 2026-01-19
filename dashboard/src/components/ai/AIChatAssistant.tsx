'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Send, X, Bot, User, Brain, Loader2,
  RefreshCw, Activity, Droplets, AlertTriangle, Sparkles
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  suggestions?: string[]
  isLoading?: boolean
}

interface SystemData {
  metrics: {
    timestamp: string
    total_nrw_percent: number
    total_inflow: number
    total_consumption: number
    total_losses: number
    water_recovered_30d: number
    revenue_recovered_30d: number
    sensor_count: number
    sensors_online: number
    dma_count: number
    active_high_priority_leaks: number
    ai_confidence: number
    detection_accuracy: number
    last_data_received: string
  }
  dmas: Array<{
    dma_id: string
    name: string
    nrw_percent: number
    priority_score: number
    status: string
    trend: string
    inflow: number
    consumption: number
    real_losses: number
    connections: number
    leak_count: number
    pressure: number
    confidence: number
    last_updated: string
  }>
  sensors: {
    timestamp: string
    sensors: Array<{
      id: string
      name: string
      type: string
      status: string
      battery: number
      signal_strength: number
      last_reading: string
      readings: any
    }>
  }
  infrastructure: {
    timestamp: string
    components: {
      api_server: { status: string; latency: number; uptime: number }
      database: { status: string; connections: number; storage_percent: number }
      ai_engine: { status: string; model_version: string; accuracy: number }
      mqtt_broker: { status: string; connected_devices: number }
      data_ingestion: { status: string; queue_size: number }
    }
  }
}

interface ConversationMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export default function AIChatAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [systemData, setSystemData] = useState<SystemData | null>(null)
  const [lastFetch, setLastFetch] = useState<Date | null>(null)
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch real system data
  const fetchSystemData = async () => {
    try {
      const response = await fetch('/api/realtime?type=all')
      const data = await response.json()
      setSystemData(data)
      setLastFetch(new Date())
      return data
    } catch (error) {
      console.error('Failed to fetch system data:', error)
      return null
    }
  }

  // Build system context from live data
  const buildSystemContext = (data: SystemData | null): string => {
    if (!data) return 'No live system data available.'
    
    const criticalDmas = data.dmas.filter(d => d.status === 'critical')
    const warningDmas = data.dmas.filter(d => d.status === 'warning')
    const totalLeaks = data.dmas.reduce((sum, d) => sum + d.leak_count, 0)
    
    return `
LIVE LWSC WATER SYSTEM DATA (as of ${new Date().toLocaleTimeString()}):

NETWORK METRICS:
- Total NRW (Non-Revenue Water): ${data.metrics.total_nrw_percent}%
- Total Inflow: ${data.metrics.total_inflow.toLocaleString()} m³/hr
- Total Consumption: ${data.metrics.total_consumption.toLocaleString()} m³/hr  
- Total Losses: ${data.metrics.total_losses.toLocaleString()} m³/hr
- Water Recovered (30 days): ${data.metrics.water_recovered_30d.toLocaleString()} m³
- Revenue Recovered (30 days): K${data.metrics.revenue_recovered_30d.toLocaleString()}
- Active High Priority Leaks: ${data.metrics.active_high_priority_leaks}
- AI Detection Confidence: ${data.metrics.ai_confidence}%
- Detection Accuracy: ${data.metrics.detection_accuracy}%

SENSORS:
- Total Sensors: ${data.metrics.sensor_count}
- Sensors Online: ${data.metrics.sensors_online}
- Sensors Offline: ${data.metrics.sensor_count - data.metrics.sensors_online}
- Sensor Details: ${data.sensors.sensors.map(s => `${s.name}: ${s.status}, Battery ${s.battery}%, Signal ${s.signal_strength}%`).join('; ')}

DMAs (District Metered Areas):
- Total DMAs: ${data.dmas.length}
- Critical (need immediate attention): ${criticalDmas.length} - ${criticalDmas.map(d => d.name).join(', ') || 'None'}
- Warning: ${warningDmas.length} - ${warningDmas.map(d => d.name).join(', ') || 'None'}
- Total Active Leaks: ${totalLeaks}

DMA DETAILS:
${data.dmas.map(d => `- ${d.name}: NRW ${d.nrw_percent}%, Status ${d.status}, ${d.leak_count} leaks, Inflow ${d.inflow} m³/hr, Losses ${d.real_losses} m³/hr, ${d.connections} connections`).join('\n')}

INFRASTRUCTURE STATUS:
- API Server: ${data.infrastructure.components.api_server.status} (${data.infrastructure.components.api_server.latency}ms latency)
- Database: ${data.infrastructure.components.database.status} (${data.infrastructure.components.database.storage_percent}% storage used)
- AI Engine: ${data.infrastructure.components.ai_engine.status} (v${data.infrastructure.components.ai_engine.model_version}, ${data.infrastructure.components.ai_engine.accuracy}% accuracy)
- MQTT Broker: ${data.infrastructure.components.mqtt_broker.status} (${data.infrastructure.components.mqtt_broker.connected_devices} devices)
`.trim()
  }

  // Initial data fetch and welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      fetchSystemData().then(data => {
        const welcomeMessage: Message = {
          id: '0',
          role: 'assistant',
          content: data 
            ? `👋 **Hello! I'm LWSC AI Assistant** - your intelligent companion powered by advanced AI.\n\n🎯 **I can answer ANY question** - just like ChatGPT! Whether it's about water systems, general knowledge, math, coding, or anything else.\n\n📊 **Current System Status:**\n• Network NRW: **${data.metrics.total_nrw_percent}%**\n• Active DMAs: **${data.dmas.length}** (${data.dmas.filter((d: any) => d.status === 'critical').length} critical)\n• Sensors Online: **${data.metrics.sensors_online}/${data.metrics.sensor_count}**\n• AI Confidence: **${data.metrics.ai_confidence}%**\n\n💬 **Try asking me:**\n• "What's the weather like?" (general)\n• "Explain NRW reduction strategies" (water)\n• "Write me a Python function" (coding)\n• "What's 2^10?" (math)\n\nHow can I help you today?`
            : `👋 **Hello! I'm LWSC AI Assistant** - your intelligent companion powered by advanced AI.\n\n🎯 **I can answer ANY question** - just like ChatGPT!\n\n💡 **Ask me about:**\n• Water management & leak detection\n• NRW analysis & reduction strategies\n• General knowledge & questions\n• Coding, math, writing, and more!\n\nHow can I assist you today?`,
          timestamp: new Date(),
          suggestions: ['System status', 'What is NRW?', 'Tell me a fact', 'Help me with coding']
        }
        setMessages([welcomeMessage])
        
        // Initialize conversation history with enhanced system prompt
        setConversationHistory([{
          role: 'system',
          content: `You are LWSC AI Assistant, an advanced AI assistant similar to ChatGPT, specialized for Lusaka Water & Sewerage Company (LWSC) in Zambia. 

## Your Role:
- Answer ANY question (water-related or general) intelligently and helpfully
- Be conversational, friendly, and engaging
- Use markdown formatting and emojis where appropriate
- Provide accurate, detailed responses

## Live Data Access:
${buildSystemContext(data)}

Remember: You can discuss ANY topic, not just water! Be as helpful as ChatGPT.`
        }])
      })
    }
  }, [isOpen, messages.length])

  // Refresh data periodically when chat is open
  useEffect(() => {
    if (isOpen) {
      const interval = setInterval(fetchSystemData, 30000)
      return () => clearInterval(interval)
    }
  }, [isOpen])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Call AI API for intelligent responses
  const callAI = async (userMessage: string): Promise<{ content: string, suggestions: string[] }> => {
    // Update system context with latest data
    const latestData = await fetchSystemData()
    
    // Build messages for AI - Enhanced ChatGPT-like system prompt
    const updatedHistory: ConversationMessage[] = [
      {
        role: 'system',
        content: `You are LWSC AI Assistant, an advanced AI assistant similar to ChatGPT, specialized for Lusaka Water & Sewerage Company (LWSC) in Zambia. You are knowledgeable, helpful, and conversational.

## Your Capabilities:
1. **Water Management Expert**: Deep knowledge of NRW (Non-Revenue Water), leak detection, pressure management, water distribution, DMAs, and utility operations
2. **General Assistant**: You can answer ANY question like ChatGPT - math, science, history, coding, writing, analysis, advice, etc.
3. **Real-Time Data Access**: You have live system data from LWSC sensors, DMAs, and infrastructure
4. **Multilingual**: You can respond in English, and understand basic local context (Zambia)

## Conversation Style:
- Be friendly, conversational, and engaging like ChatGPT
- Use emojis sparingly but effectively for visual appeal 🎯
- Format responses with markdown: **bold**, *italic*, bullet points, numbered lists
- Keep responses focused but thorough (150-400 words typically)
- Ask clarifying questions when needed
- Remember context from the conversation

## When Answering:
- For water/LWSC questions: Use the live data provided below
- For general questions: Answer knowledgeably like ChatGPT would
- Always be accurate and helpful
- If you don't know something, say so honestly

## Response Format:
At the end of your response, ALWAYS provide 2-4 suggested follow-up questions in this exact format:
[SUGGESTIONS: question1 | question2 | question3]

## CURRENT LIVE LWSC SYSTEM DATA:
${buildSystemContext(latestData)}

You are both a water utility expert AND a general-purpose AI assistant. Answer any question the user asks - don't limit yourself to only water topics!`
      },
      ...conversationHistory.filter(m => m.role !== 'system'),
      { role: 'user', content: userMessage }
    ]

    try {
      // Call AI API
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: updatedHistory,
          systemData: latestData
        })
      })

      if (!response.ok) {
        throw new Error('AI service unavailable')
      }

      const data = await response.json()
      let content = data.content || data.message || 'I apologize, but I couldn\'t generate a response.'
      
      // Extract suggestions if present
      let suggestions: string[] = ['System status', 'Show NRW', 'Help']
      const suggestionsMatch = content.match(/\[SUGGESTIONS?:\s*([^\]]+)\]/i)
      if (suggestionsMatch) {
        suggestions = suggestionsMatch[1].split('|').map((s: string) => s.trim()).filter((s: string) => s.length > 0)
        content = content.replace(/\[SUGGESTIONS?:\s*[^\]]+\]/i, '').trim()
      }

      // Update conversation history
      setConversationHistory([
        ...updatedHistory,
        { role: 'assistant', content }
      ])

      return { content, suggestions }
    } catch (error) {
      console.error('AI API error:', error)
      // Fallback to local response if API fails
      return generateLocalResponse(userMessage, latestData)
    }
  }

  // Local fallback response generator (used when API is unavailable)
  const generateLocalResponse = (query: string, data: SystemData | null): { content: string, suggestions: string[] } => {
    if (!data) {
      return {
        content: `⚠️ Unable to connect to system data. Please check your connection and try again.`,
        suggestions: ['Retry', 'Check system health']
      }
    }

    const q = query.toLowerCase()
    const { metrics, dmas, sensors, infrastructure } = data

    // System status / overview
    if (q.includes('status') || q.includes('overview') || q.includes('system') || q.includes('health')) {
      const criticalDmas = dmas.filter((d: any) => d.status === 'critical')
      const warningDmas = dmas.filter((d: any) => d.status === 'warning')
      const offlineSensors = sensors.sensors.filter((s: any) => s.status !== 'online')
      
      return {
        content: `📊 **Live System Status** (as of ${new Date().toLocaleTimeString()})\n\n` +
          `**Network Performance:**\n` +
          `• Total NRW: **${metrics.total_nrw_percent}%** ${metrics.total_nrw_percent > 35 ? '🔴' : metrics.total_nrw_percent > 25 ? '🟡' : '🟢'}\n` +
          `• Water Inflow: **${metrics.total_inflow.toLocaleString()} m³/hr**\n` +
          `• Consumption: **${metrics.total_consumption.toLocaleString()} m³/hr**\n` +
          `• Losses: **${metrics.total_losses.toLocaleString()} m³/hr**\n\n` +
          `**Infrastructure:**\n` +
          `• API Server: ${infrastructure.components.api_server.status === 'healthy' ? '✅' : '⚠️'} ${infrastructure.components.api_server.latency}ms\n` +
          `• Database: ${infrastructure.components.database.status === 'healthy' ? '✅' : '⚠️'} ${infrastructure.components.database.storage_percent}% storage\n` +
          `• AI Engine: ${infrastructure.components.ai_engine.status === 'healthy' ? '✅' : '⚠️'} v${infrastructure.components.ai_engine.model_version}\n` +
          `• MQTT: ${infrastructure.components.mqtt_broker.status === 'healthy' ? '✅' : '⚠️'} ${infrastructure.components.mqtt_broker.connected_devices} devices\n\n` +
          `**Alerts:** ${criticalDmas.length} critical, ${warningDmas.length} warning, ${offlineSensors.length} sensors offline`,
        suggestions: ['Show critical DMAs', 'Sensor details', 'NRW breakdown']
      }
    }

    // NRW queries
    if (q.includes('nrw') || q.includes('non-revenue') || q.includes('loss') || q.includes('water loss')) {
      const sortedByNrw = [...dmas].sort((a: any, b: any) => b.nrw_percent - a.nrw_percent)
      const worst3 = sortedByNrw.slice(0, 3)
      const best3 = sortedByNrw.slice(-3).reverse()
      
      return {
        content: `📉 **Live NRW Analysis** (Updated: ${new Date().toLocaleTimeString()})\n\n` +
          `**Network Summary:**\n` +
          `• Current NRW Rate: **${metrics.total_nrw_percent}%**\n` +
          `• Daily Loss Volume: **${Math.round(metrics.total_losses * 24).toLocaleString()} m³**\n` +
          `• Est. Revenue Loss: **K${Math.round(metrics.total_losses * 24 * 50).toLocaleString()}/day**\n` +
          `• 30-Day Recovery: **K${metrics.revenue_recovered_30d.toLocaleString()}**\n\n` +
          `**Worst Performing DMAs:**\n` +
          worst3.map((d: any, i: number) => `${i + 1}. **${d.name}** - ${d.nrw_percent}% ${d.status === 'critical' ? '🔴' : '🟡'}`).join('\n') +
          `\n\n**Best Performing DMAs:**\n` +
          best3.map((d: any, i: number) => `${i + 1}. **${d.name}** - ${d.nrw_percent}% 🟢`).join('\n') +
          `\n\n💡 **AI Tip:** Focus on ${worst3[0].name} to reduce NRW by ~${Math.round(worst3[0].nrw_percent * 0.1)}%`,
        suggestions: [`Details: ${worst3[0].name}`, 'Show all DMAs', 'NRW trend']
      }
    }

    // DMA queries
    if (q.includes('dma') || q.includes('zone') || q.includes('district') || q.includes('area')) {
      const criticalDmas = dmas.filter((d: any) => d.status === 'critical')
      const warningDmas = dmas.filter((d: any) => d.status === 'warning')
      
      // Check for specific DMA
      const specificDma = dmas.find((d: any) => q.includes(d.name.toLowerCase()))
      if (specificDma) {
        return {
          content: `🗺️ **${specificDma.name} - Live Data**\n\n` +
            `**Performance:**\n` +
            `• NRW Rate: **${specificDma.nrw_percent}%** ${specificDma.status === 'critical' ? '🔴' : specificDma.status === 'warning' ? '🟡' : '🟢'}\n` +
            `• Priority Score: **${specificDma.priority_score}/100**\n` +
            `• Trend: ${specificDma.trend === 'up' ? '📈 Increasing' : specificDma.trend === 'down' ? '📉 Improving' : '➡️ Stable'}\n\n` +
            `**Flow Data:**\n` +
            `• Inflow: **${specificDma.inflow} m³/hr**\n` +
            `• Consumption: **${specificDma.consumption} m³/hr**\n` +
            `• Losses: **${specificDma.real_losses} m³/hr**\n` +
            `• Pressure: **${specificDma.pressure} bar**\n\n` +
            `**Coverage:** ${specificDma.connections.toLocaleString()} connections | ${specificDma.leak_count} leaks`,
          suggestions: ['Compare DMAs', 'Dispatch crew', 'Show leaks']
        }
      }

      // Critical DMAs
      if (q.includes('critical') || q.includes('worst') || q.includes('priority')) {
        return {
          content: `🚨 **Critical DMAs Requiring Attention**\n\n` +
            (criticalDmas.length > 0 
              ? criticalDmas.map((d: any, i: number) => 
                  `**${i + 1}. ${d.name}** (Score: ${d.priority_score})\n` +
                  `   NRW: ${d.nrw_percent}% | Losses: ${d.real_losses} m³/hr | Leaks: ${d.leak_count}`
                ).join('\n\n')
              : '✅ No critical DMAs!') +
            (warningDmas.length > 0 
              ? `\n\n**Warning (${warningDmas.length}):** ${warningDmas.map((d: any) => d.name).join(', ')}`
              : '') +
            `\n\n💡 Potential savings: **K${Math.round(criticalDmas.reduce((sum: number, d: any) => sum + d.real_losses * 24 * 50 * 0.3, 0)).toLocaleString()}/day**`,
          suggestions: criticalDmas.length > 0 ? [`Fix ${criticalDmas[0].name}`, 'Dispatch crews'] : ['View all DMAs']
        }
      }

      // All DMAs
      return {
        content: `🗺️ **All DMAs - Live Status**\n\n` +
          dmas.map((d: any, i: number) => 
            `**${i + 1}. ${d.name}** ${d.status === 'critical' ? '🔴' : d.status === 'warning' ? '🟡' : '🟢'}\n` +
            `   NRW: ${d.nrw_percent}% | Inflow: ${d.inflow} m³/hr | Leaks: ${d.leak_count}`
          ).join('\n\n') +
          `\n\n**Summary:** ${criticalDmas.length} critical, ${warningDmas.length} warning`,
        suggestions: ['Critical only', 'NRW breakdown', 'Best performers']
      }
    }

    // Sensor queries
    if (q.includes('sensor') || q.includes('meter') || q.includes('device') || q.includes('iot')) {
      const onlineSensors = sensors.sensors.filter((s: any) => s.status === 'online')
      const offlineSensors = sensors.sensors.filter((s: any) => s.status !== 'online')
      const lowBattery = sensors.sensors.filter((s: any) => s.battery < 30)
      
      return {
        content: `📡 **Sensor Network - Live**\n\n` +
          `**Overview:**\n` +
          `• Total: **${sensors.sensors.length}**\n` +
          `• Online: **${onlineSensors.length}** ✅\n` +
          `• Offline: **${offlineSensors.length}** ${offlineSensors.length > 0 ? '⚠️' : ''}\n` +
          `• Low Battery: **${lowBattery.length}** ${lowBattery.length > 0 ? '🔋' : ''}\n\n` +
          `**Sensors:**\n` +
          sensors.sensors.map((s: any) => 
            `• **${s.name}**\n  ${s.status === 'online' ? '🟢' : '🔴'} ${s.status} | 🔋 ${s.battery}% | 📶 ${s.signal_strength}%`
          ).join('\n\n') +
          (lowBattery.length > 0 
            ? `\n\n⚠️ **Low Battery:** ${lowBattery.map((s: any) => `${s.name} (${s.battery}%)`).join(', ')}`
            : ''),
        suggestions: lowBattery.length > 0 ? ['Schedule maintenance', 'Battery report'] : ['View readings']
      }
    }

    // Leak queries
    if (q.includes('leak') || q.includes('burst') || q.includes('pipe')) {
      const dmasWithLeaks = dmas.filter((d: any) => d.leak_count > 0).sort((a: any, b: any) => b.leak_count - a.leak_count)
      const totalLeaks = dmas.reduce((sum: number, d: any) => sum + d.leak_count, 0)
      
      return {
        content: `🔍 **Active Leak Detection** (Live)\n\n` +
          `**Summary:**\n` +
          `• Total Leaks: **${totalLeaks}**\n` +
          `• Critical: **${dmas.filter((d: any) => d.status === 'critical').reduce((sum: number, d: any) => sum + d.leak_count, 0)}**\n` +
          `• Water Loss: **${metrics.total_losses.toLocaleString()} m³/hr**\n` +
          `• AI Accuracy: **${metrics.detection_accuracy}%**\n\n` +
          `**By Location:**\n` +
          (dmasWithLeaks.length > 0 
            ? dmasWithLeaks.map((d: any, i: number) => 
                `**${i + 1}. ${d.name}** - ${d.leak_count} leak${d.leak_count > 1 ? 's' : ''} ${d.status === 'critical' ? '🔴' : '🟡'}\n` +
                `   Losses: ${d.real_losses} m³/hr | Pressure: ${d.pressure} bar`
              ).join('\n\n')
            : '✅ No active leaks!') +
          `\n\n💡 ${dmasWithLeaks.length > 0 
            ? `Fix ${dmasWithLeaks[0].name} to save K${Math.round(dmasWithLeaks[0].real_losses * 24 * 50).toLocaleString()}/day`
            : 'Network performing well!'}`,
        suggestions: dmasWithLeaks.length > 0 
          ? [`Fix ${dmasWithLeaks[0].name}`, 'Show on map', 'Dispatch crew']
          : ['View predictions', 'Check sensors']
      }
    }

    // Crew / dispatch
    if (q.includes('crew') || q.includes('team') || q.includes('dispatch') || q.includes('technician')) {
      const priorityDmas = dmas.filter((d: any) => d.leak_count > 0).slice(0, 4)
      return {
        content: `👷 **Dispatch Recommendations** (Based on Live Data)\n\n` +
          `**Priority Deployments:**\n` +
          priorityDmas.map((d: any, i: number) => 
            `${i + 1}. **${d.name}** - ${d.leak_count} leak${d.leak_count > 1 ? 's' : ''}\n` +
            `   Priority: ${d.priority_score}/100 | Est. time: ${d.leak_count * 2}h`
          ).join('\n\n') +
          `\n\n**Optimal Route:**\n` +
          `${priorityDmas.slice(0, 3).map((d: any) => d.name).join(' → ')}\n` +
          `Est. time saved: ~2.4 hours\n\n` +
          `💡 Start with **${priorityDmas[0]?.name || 'N/A'}** - highest impact`,
        suggestions: ['Create work order', 'View all tasks', 'Optimize routes']
      }
    }

    // Report / summary
    if (q.includes('report') || q.includes('summary') || q.includes('daily') || q.includes('today')) {
      return {
        content: `📋 **System Report** (${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()})\n\n` +
          `**Network:**\n` +
          `• NRW: ${metrics.total_nrw_percent}%\n` +
          `• Inflow: ${metrics.total_inflow.toLocaleString()} m³/hr\n` +
          `• Losses: ${metrics.total_losses.toLocaleString()} m³/hr\n\n` +
          `**DMAs:** ${dmas.length} total\n` +
          `• Critical: ${dmas.filter((d: any) => d.status === 'critical').length}\n` +
          `• Warning: ${dmas.filter((d: any) => d.status === 'warning').length}\n` +
          `• Healthy: ${dmas.filter((d: any) => d.status === 'healthy').length}\n\n` +
          `**Sensors:** ${metrics.sensors_online}/${metrics.sensor_count} online\n\n` +
          `**30-Day Recovery:**\n` +
          `• Water: ${metrics.water_recovered_30d.toLocaleString()} m³\n` +
          `• Revenue: K${metrics.revenue_recovered_30d.toLocaleString()}\n\n` +
          `AI Confidence: ${metrics.ai_confidence}%`,
        suggestions: ['Export PDF', 'Weekly trend', 'Compare periods']
      }
    }

    // Help
    if (q.includes('help') || q.includes('what can') || q.includes('how to')) {
      return {
        content: `👋 **I'm LWSC AI Assistant** - Connected to Live Data!\n\n` +
          `**Ask me about:**\n\n` +
          `🔍 **Leaks:** "Show active leaks", "Where are leaks?"\n` +
          `📊 **NRW:** "What's our NRW?", "Worst DMAs"\n` +
          `🗺️ **DMAs:** "Critical DMAs", "Details for Kabulonga"\n` +
          `📡 **Sensors:** "Sensor health", "Low battery"\n` +
          `📋 **Reports:** "System status", "Daily summary"\n` +
          `👷 **Dispatch:** "Dispatch crews", "Priority tasks"\n\n` +
          `I fetch **real-time data** for every response!`,
        suggestions: ['System status', 'Show NRW', 'Critical DMAs', 'Sensors']
      }
    }

    // Default
    return {
      content: `I understand you're asking about "${query}".\n\n` +
        `**Current System:**\n` +
        `• NRW: ${metrics.total_nrw_percent}%\n` +
        `• Leaks: ${dmas.reduce((sum: number, d: any) => sum + d.leak_count, 0)}\n` +
        `• Critical DMAs: ${dmas.filter((d: any) => d.status === 'critical').length}\n` +
        `• Sensors: ${metrics.sensors_online}/${metrics.sensor_count} online\n\n` +
        `Ask about leaks, NRW, DMAs, sensors, or say "help" for options.`,
      suggestions: ['System status', 'Show leaks', 'NRW analysis', 'Help']
    }
  }

  const handleSend = async (text?: string) => {
    const messageText = text || input
    if (!messageText.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    const loadingId = (Date.now() + 1).toString()
    setMessages(prev => [...prev, {
      id: loadingId,
      role: 'assistant',
      content: '✨ Thinking...',
      timestamp: new Date(),
      isLoading: true
    }])

    // Use AI API for response
    const { content, suggestions } = await callAI(messageText)
    
    setMessages(prev => prev.map(m => 
      m.id === loadingId 
        ? { ...m, content, suggestions, isLoading: false }
        : m
    ))
    setIsTyping(false)
  }

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full shadow-lg shadow-purple-500/30 flex items-center justify-center text-white hover:scale-110 transition-transform z-50 ${isOpen ? 'hidden' : ''}`}
      >
        <Sparkles className="w-7 h-7" />
        <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full border-2 border-white animate-pulse" />
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[420px] h-[650px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden border border-slate-200">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold flex items-center gap-2">LWSC AI <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">GPT</span></h3>
                <div className="flex items-center gap-2 text-xs text-purple-200">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  Live Data Connected
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button 
                onClick={fetchSystemData}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setIsOpen(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Data Indicators */}
          {systemData && (
            <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-emerald-500" />
                <span className="text-slate-600">NRW: <strong className={systemData.metrics.total_nrw_percent > 35 ? 'text-red-600' : 'text-emerald-600'}>{systemData.metrics.total_nrw_percent}%</strong></span>
              </div>
              <div className="flex items-center gap-1">
                <Droplets className="w-3 h-3 text-blue-500" />
                <span className="text-slate-600">Loss: <strong>{systemData.metrics.total_losses}</strong></span>
              </div>
              <div className="flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-amber-500" />
                <span className="text-slate-600">Critical: <strong>{systemData.dmas.filter((d: any) => d.status === 'critical').length}</strong></span>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                  <div className={`flex items-end gap-2 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gradient-to-br from-purple-500 to-blue-500 text-white'
                    }`}>
                      {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={`px-4 py-3 rounded-2xl ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-br-md' 
                        : 'bg-white shadow-sm border border-slate-200 rounded-bl-md'
                    }`}>
                      {message.isLoading ? (
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Fetching live data...
                        </div>
                      ) : (
                        <div className={`text-sm whitespace-pre-wrap ${message.role === 'user' ? '' : 'text-slate-700'}`}>
                          {message.content.split('\n').map((line, i) => {
                            const parts = line.split(/(\*\*.*?\*\*)/g)
                            return (
                              <p key={i} className={i > 0 ? 'mt-1' : ''}>
                                {parts.map((part, j) => {
                                  if (part.startsWith('**') && part.endsWith('**')) {
                                    return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>
                                  }
                                  return part
                                })}
                              </p>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {message.role === 'assistant' && message.suggestions && !message.isLoading && (
                    <div className="mt-2 ml-9 flex flex-wrap gap-1">
                      {message.suggestions.map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(suggestion)}
                          className="px-3 py-1.5 bg-white border border-slate-200 rounded-full text-xs text-slate-600 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-slate-200 bg-white">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !isTyping && handleSend()}
                placeholder="Ask about leaks, NRW, DMAs..."
                disabled={isTyping}
                className="flex-1 px-4 py-2.5 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:bg-white transition-colors disabled:opacity-50"
              />
              <button 
                onClick={() => handleSend()}
                disabled={!input.trim() || isTyping}
                className="w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl flex items-center justify-center text-white hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
