import { NextResponse } from 'next/server'

interface Message {
  role: 'system' | 'user' | 'assistant'
  content: string
}

// AI Provider configurations (in order of preference)
// Groq is FREE and fast - recommended for production
const AI_PROVIDERS = [
  {
    name: 'groq',
    url: 'https://api.groq.com/openai/v1/chat/completions',
    key: process.env.GROQ_API_KEY || '',
    model: 'llama-3.3-70b-versatile' // Fast, free, powerful
  },
  {
    name: 'together',
    url: 'https://api.together.xyz/v1/chat/completions',
    key: process.env.TOGETHER_API_KEY || '',
    model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo'
  },
  {
    name: 'openai',
    url: process.env.OPENAI_API_URL || 'https://api.openai.com/v1/chat/completions',
    key: process.env.OPENAI_API_KEY || '',
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini'
  }
]

// Check which providers are available
function getAvailableProviders() {
  return AI_PROVIDERS.filter(p => p.key && p.key.length > 10)
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { messages, systemData } = body as { messages: Message[], systemData: any }

    if (!messages || messages.length === 0) {
      return NextResponse.json(
        { error: 'Messages are required' },
        { status: 400 }
      )
    }

    const availableProviders = getAvailableProviders()
    console.log(`Available AI providers: ${availableProviders.map(p => p.name).join(', ') || 'NONE - using local fallback'}`)

    // Try each AI provider in order
    for (const provider of availableProviders) {
      try {
        console.log(`Trying ${provider.name} with model ${provider.model}...`)
        
        const response = await fetch(provider.url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${provider.key}`
          },
          body: JSON.stringify({
            model: provider.model,
            messages: messages,
            max_tokens: 2000,
            temperature: 0.7,
            top_p: 0.9
          })
        })

        if (response.ok) {
          const data = await response.json()
          const content = data.choices?.[0]?.message?.content || 'No response generated'
          
          console.log(`✅ ${provider.name} responded successfully`)
          
          return NextResponse.json({
            content,
            model: provider.model,
            source: provider.name,
            isAI: true
          })
        } else {
          const errorText = await response.text()
          console.error(`${provider.name} API error (${response.status}):`, errorText)
        }
      } catch (apiError) {
        console.error(`${provider.name} API error:`, apiError)
        // Continue to next provider
      }
    }

    // Fallback: Generate intelligent local response
    console.log('⚠️ All AI providers failed or unavailable, using local fallback')
    const userMessage = messages.filter(m => m.role === 'user').pop()?.content || ''
    const localResponse = generateIntelligentResponse(userMessage, systemData)
    
    return NextResponse.json({
      content: localResponse.content,
      suggestions: localResponse.suggestions,
      model: 'local-fallback',
      source: 'local',
      isAI: false,
      note: 'AI API not configured. Add GROQ_API_KEY to environment variables for real AI responses.'
    })

  } catch (error) {
    console.error('AI chat error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to process request',
        content: 'I apologize, but I encountered an error. Please try again.',
        isAI: false
      },
      { status: 500 }
    )
  }
}

// Intelligent local response generator
function generateIntelligentResponse(query: string, data: any): { content: string, suggestions: string[] } {
  const q = query.toLowerCase().trim()
  
  // Natural greetings - be conversational
  if (/^(hi|hello|hey|yo|sup|hiya|howdy|greetings)[\s!.,?]*$/i.test(q) || 
      q.startsWith('hi ') || q.startsWith('hello ') || q.startsWith('hey ')) {
    const greetings = [
      `👋 Hey there! I'm the LWSC AI Assistant. How can I help you today?`,
      `Hello! 👋 Great to see you! What can I help you with?`,
      `Hi! I'm here to assist with anything - water system questions, general help, or just a chat. What's on your mind?`,
      `Hey! 👋 I'm your LWSC assistant. Ask me anything!`
    ]
    return {
      content: greetings[Math.floor(Math.random() * greetings.length)] + 
        (data?.metrics ? `\n\n📊 *Quick update: Network NRW is at ${data.metrics.total_nrw_percent}% today.*` : ''),
      suggestions: ['System status', 'What can you do?', 'Tell me about NRW', 'Weather today']
    }
  }

  // How are you / personal questions
  if (q.includes('how are you') || q.includes("how's it going") || q.includes('how do you do')) {
    return {
      content: `I'm doing great, thanks for asking! 😊 As an AI, I'm always ready to help.\n\n${data?.metrics ? `The water network is running well - ${data.metrics.sensors_online}/${data.metrics.sensor_count} sensors are online.` : ''}\n\nWhat can I help you with today?`,
      suggestions: ['System status', 'Tell me a fact', 'Help with work']
    }
  }

  // What can you do / capabilities
  if (q.includes('what can you do') || q.includes('help me') || q === 'help' || q.includes('your capabilities')) {
    return {
      content: `🤖 **I'm an AI assistant that can help with many things!**\n\n**Water System (my specialty):**\n• Real-time NRW analysis and leak detection\n• DMA performance monitoring\n• Sensor status and alerts\n• Work order management\n\n**General Assistance:**\n• Answer questions on any topic\n• Explain concepts and provide information\n• Help with analysis and recommendations\n• Have a conversation!\n\nJust ask me anything naturally - I understand context! 💬`,
      suggestions: ['System overview', 'What is NRW?', 'Show critical areas', 'Fun fact']
    }
  }

  // Who are you / identity
  if (q.includes('who are you') || q.includes('your name') || q.includes('what are you')) {
    return {
      content: `I'm the **LWSC AI Assistant** 🤖\n\nI'm an artificial intelligence designed to help Lusaka Water & Sewerage Company manage their water distribution network. I have access to real-time data from sensors, DMAs, and the AI detection system.\n\nBut I'm also a general-purpose AI - feel free to ask me about anything, not just water! How can I help you?`,
      suggestions: ['System status', 'Tell me a joke', 'What is NRW?']
    }
  }

  // Jokes / fun
  if (q.includes('joke') || q.includes('funny') || q.includes('make me laugh')) {
    const jokes = [
      `Why did the water utility worker bring a ladder to work? 🪜\n\nBecause they wanted to reach the *high* water mark! 💧`,
      `What did the pipe say to the leak? 🔧\n\n"You're really draining me!" 😄`,
      `Why are water engineers always calm? 🌊\n\nBecause they know how to go with the flow! 💧`,
      `What's a water utility's favorite music? 🎵\n\nHeavy metal... pipes! 🤘`
    ]
    return {
      content: jokes[Math.floor(Math.random() * jokes.length)],
      suggestions: ['Another joke', 'System status', 'Tell me a fact']
    }
  }

  // Facts / interesting
  if (q.includes('fact') || q.includes('interesting') || q.includes('did you know')) {
    const facts = [
      `💡 **Did you know?**\n\nThe average person uses about 100-150 liters of water per day. That's roughly 50 bathtubs full per year!`,
      `💡 **Water Fact:**\n\nA dripping tap can waste over 20,000 liters per year - that's enough to fill a small swimming pool!`,
      `💡 **Fun Fact:**\n\nWater is the only substance on Earth that naturally exists in three states: solid (ice), liquid (water), and gas (steam).`,
      `💡 **Did you know?**\n\nThe global average for Non-Revenue Water (NRW) is about 30%. Some cities lose over 50% of their water!`
    ]
    return {
      content: facts[Math.floor(Math.random() * facts.length)],
      suggestions: ['Another fact', 'System status', 'What is NRW?']
    }
  }

  // Thank you responses
  if (q.includes('thank') || q.includes('thanks') || q.includes('cheers') || q.includes('appreciate')) {
    return {
      content: `You're welcome! 😊 Happy to help anytime. Is there anything else you'd like to know?`,
      suggestions: ['System status', 'More info', 'That\'s all, bye']
    }
  }

  // Goodbye
  if (q.includes('bye') || q.includes('goodbye') || q.includes('see you') || q.includes('that\'s all')) {
    return {
      content: `Goodbye! 👋 Have a great day! Feel free to come back anytime you need help with the water system or anything else. 😊`,
      suggestions: ['Actually, one more thing...']
    }
  }

  // Weather (playful response since we don't have weather API)
  if (q.includes('weather') || q.includes('temperature') || q.includes('rain')) {
    return {
      content: `🌤️ I don't have direct access to weather data, but I can tell you that water flows best when it's not frozen! 😄\n\nFor accurate weather, check your local forecast. Is there something else I can help you with?`,
      suggestions: ['System status', 'NRW analysis', 'Help']
    }
  }

  // Time
  if (q.includes('what time') || q.includes('current time')) {
    return {
      content: `🕐 The current time is **${new Date().toLocaleTimeString()}** on **${new Date().toLocaleDateString()}**.\n\nAnything else I can help with?`,
      suggestions: ['System status', 'Help']
    }
  }

  // If no system data, provide general responses
  if (!data || !data.metrics) {
    // Check for water-related terms
    if (q.includes('nrw') || q.includes('water') || q.includes('leak') || q.includes('pipe')) {
      return {
        content: `I'd love to help with that! However, I'm currently having trouble accessing live system data. 📡\n\nIn general, NRW (Non-Revenue Water) is water that's produced but lost before reaching customers - typically through leaks, theft, or meter issues.\n\nCan I help with something else, or would you like to try again for live data?`,
        suggestions: ['What is NRW?', 'Retry', 'General help']
      }
    }

    return {
      content: `I'd be happy to help with "${query}"!\n\nI'm your LWSC AI assistant. While I specialize in water management, I can chat about many topics. Currently, I'm having trouble accessing live system data, but I can still help with general questions.\n\nWhat would you like to know?`,
      suggestions: ['What can you do?', 'Tell me a fact', 'Help']
    }
  }

  // === SYSTEM DATA AVAILABLE - Water-specific responses ===
  const { metrics, dmas, sensors, infrastructure } = data

  // System status / overview
  if (q.includes('status') || q.includes('overview') || q.includes('summary') || q.includes('health') || q.includes('how is the system')) {
    const criticalDmas = dmas?.filter((d: any) => d.status === 'critical') || []
    const warningDmas = dmas?.filter((d: any) => d.status === 'warning') || []
    
    return {
      content: `📊 **System Status** (${new Date().toLocaleTimeString()})\n\n` +
        `**Performance:**\n` +
        `• NRW: **${metrics.total_nrw_percent}%** ${metrics.total_nrw_percent > 35 ? '🔴 High' : metrics.total_nrw_percent > 25 ? '🟡 Moderate' : '🟢 Good'}\n` +
        `• Inflow: **${metrics.total_inflow?.toLocaleString() || 0} m³/hr**\n` +
        `• Losses: **${metrics.total_losses?.toLocaleString() || 0} m³/hr**\n\n` +
        `**Infrastructure:**\n` +
        `• Sensors: **${metrics.sensors_online}/${metrics.sensor_count}** online\n` +
        `• DMAs: ${criticalDmas.length} critical 🔴, ${warningDmas.length} warning 🟡\n` +
        `• AI Confidence: **${metrics.ai_confidence}%**\n\n` +
        `${criticalDmas.length > 0 ? `⚠️ **Action needed** in ${criticalDmas[0]?.name}` : '✅ System running smoothly!'}`,
      suggestions: ['Critical DMAs', 'Show leaks', 'Sensor details', 'NRW breakdown']
    }
  }

  // NRW queries
  if (q.includes('nrw') || (q.includes('water') && q.includes('loss'))) {
    const sortedByNrw = [...(dmas || [])].sort((a: any, b: any) => b.nrw_percent - a.nrw_percent)
    const worst3 = sortedByNrw.slice(0, 3)
    
    return {
      content: `📉 **NRW Analysis**\n\n` +
        `**Current:** ${metrics.total_nrw_percent}% ${metrics.total_nrw_percent > 35 ? '(High - needs attention!)' : metrics.total_nrw_percent > 25 ? '(Moderate)' : '(Good!)'}\n` +
        `**Daily Loss:** ~${Math.round((metrics.total_losses || 0) * 24).toLocaleString()} m³\n` +
        `**Est. Revenue Loss:** K${Math.round((metrics.total_losses || 0) * 24 * 50).toLocaleString()}/day\n\n` +
        `**Worst Areas:**\n${worst3.map((d: any, i: number) => `${i + 1}. ${d.name}: ${d.nrw_percent}%`).join('\n')}\n\n` +
        `💡 Focusing on ${worst3[0]?.name || 'critical areas'} would have the biggest impact!`,
      suggestions: [`About ${worst3[0]?.name || 'worst DMA'}`, 'How to reduce NRW', 'Create work order']
    }
  }

  // Leak queries
  if (q.includes('leak') || q.includes('burst') || q.includes('repair')) {
    const totalLeaks = (dmas || []).reduce((sum: number, d: any) => sum + (d.leak_count || 0), 0)
    const dmasWithLeaks = (dmas || []).filter((d: any) => d.leak_count > 0).sort((a: any, b: any) => b.leak_count - a.leak_count)
    
    return {
      content: `🔍 **Leak Detection**\n\n` +
        `**Active Leaks:** ${totalLeaks}\n` +
        `**Loss Rate:** ${(metrics.total_losses || 0).toLocaleString()} m³/hr\n` +
        `**Detection Accuracy:** ${metrics.detection_accuracy}%\n\n` +
        `**Locations:**\n${dmasWithLeaks.length > 0 
          ? dmasWithLeaks.slice(0, 4).map((d: any) => `• ${d.name}: ${d.leak_count} leak(s)`).join('\n')
          : '✅ No active leaks!'}\n\n` +
        (dmasWithLeaks.length > 0 ? `💡 Priority: ${dmasWithLeaks[0].name}` : '💡 Great - keep monitoring!'),
      suggestions: dmasWithLeaks.length > 0 ? ['Dispatch crew', 'Create work order', 'More details'] : ['System status', 'NRW analysis']
    }
  }

  // DMA queries
  if (q.includes('dma') || q.includes('critical') || q.includes('zone') || q.includes('area') || q.includes('district')) {
    const criticalDmas = (dmas || []).filter((d: any) => d.status === 'critical')
    const warningDmas = (dmas || []).filter((d: any) => d.status === 'warning')
    
    return {
      content: `🗺️ **DMA Overview**\n\n` +
        `**Total DMAs:** ${dmas?.length || 0}\n` +
        `• 🔴 Critical: ${criticalDmas.length}\n` +
        `• 🟡 Warning: ${warningDmas.length}\n` +
        `• 🟢 Healthy: ${(dmas?.length || 0) - criticalDmas.length - warningDmas.length}\n\n` +
        (criticalDmas.length > 0 
          ? `**Critical Areas:**\n${criticalDmas.map((d: any) => `• ${d.name}: NRW ${d.nrw_percent}%, ${d.leak_count} leaks`).join('\n')}`
          : '✅ No critical DMAs!'),
      suggestions: criticalDmas[0] ? [`Details ${criticalDmas[0].name}`, 'All DMAs', 'Dispatch'] : ['All DMAs', 'NRW analysis']
    }
  }

  // Sensor queries
  if (q.includes('sensor') || q.includes('device') || q.includes('iot')) {
    const sensorList = sensors?.sensors || []
    const offline = sensorList.filter((s: any) => s.status !== 'online')
    const lowBattery = sensorList.filter((s: any) => s.battery < 30)
    
    return {
      content: `📡 **Sensor Network**\n\n` +
        `**Status:** ${metrics.sensors_online}/${metrics.sensor_count} online\n` +
        `**Offline:** ${offline.length} ${offline.length > 0 ? '⚠️' : '✅'}\n` +
        `**Low Battery:** ${lowBattery.length}\n\n` +
        `${offline.length > 0 ? `**Offline sensors:** ${offline.map((s: any) => s.name).join(', ')}` : '✅ All sensors operational!'}` +
        `${lowBattery.length > 0 ? `\n**Need charging:** ${lowBattery.map((s: any) => s.name).join(', ')}` : ''}`,
      suggestions: offline.length > 0 ? ['Fix offline sensors', 'Sensor details'] : ['Sensor readings', 'System status']
    }
  }

  // Default: Try to give a helpful response
  return {
    content: `I understand you're asking about "${query}". 🤔\n\n` +
      `I'm the LWSC AI Assistant with access to live water system data. Here's what I can help with:\n\n` +
      `• 📊 **"System status"** - Overall network health\n` +
      `• 💧 **"NRW analysis"** - Water loss breakdown\n` +
      `• 🔍 **"Show leaks"** - Active leak locations\n` +
      `• 🗺️ **"Critical DMAs"** - Areas needing attention\n` +
      `• 📡 **"Sensor status"** - Device monitoring\n\n` +
      `Or just chat with me about anything! What would you like to explore?`,
    suggestions: ['System status', 'NRW analysis', 'Active leaks', 'Help']
  }
}
