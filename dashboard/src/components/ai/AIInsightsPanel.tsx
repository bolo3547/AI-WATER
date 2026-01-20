'use client'

import { useState, useEffect } from 'react'
import { Brain, Sparkles, RefreshCw, ChevronDown, ChevronUp, Zap, AlertTriangle, TrendingUp, Lightbulb, X } from 'lucide-react'

interface AIInsightsPanelProps {
  type: 'leak_analysis' | 'nrw_insights' | 'dma_recommendation' | 'alert_priority' | 'sensor_diagnosis' | 'trend_analysis' | 'general'
  data: any
  title?: string
  autoLoad?: boolean
  compact?: boolean
}

async function analyzeWithAI(request: { type: string, context: any, question?: string }) {
  try {
    const systemPrompts: Record<string, string> = {
      leak_analysis: `You are an expert water utility AI. Analyze leak data concisely. Focus on severity, causes, and actions.`,
      nrw_insights: `You are an NRW analysis expert. Analyze metrics, compare to benchmarks, suggest reductions.`,
      dma_recommendation: `You are a DMA optimization expert. Identify issues, prioritize interventions.`,
      alert_priority: `You are an alert prioritization AI. Rank by urgency, recommend response sequence.`,
      sensor_diagnosis: `You are an IoT sensor expert. Diagnose issues, recommend maintenance.`,
      trend_analysis: `You are a trend analysis expert. Identify patterns, predict issues.`,
      general: `You are LWSC AI assistant. Be helpful and data-driven.`
    }

    const messages = [
      { role: 'system', content: systemPrompts[request.type] || systemPrompts.general },
      { 
        role: 'user', 
        content: request.question 
          ? `${request.question}\n\nData:\n${JSON.stringify(request.context, null, 2)}`
          : `Analyze this data:\n${JSON.stringify(request.context, null, 2)}`
      }
    ]

    const response = await fetch('/api/ai/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, type: request.type })
    })

    if (!response.ok) throw new Error('Analysis failed')
    const data = await response.json()
    
    return {
      success: true,
      analysis: data.content || data.analysis || 'Analysis complete.'
    }
  } catch (error) {
    return { success: false, analysis: 'Unable to perform AI analysis.' }
  }
}

export function AIInsightsPanel({ type, data, title, autoLoad = false, compact = false }: AIInsightsPanelProps) {
  const [analysis, setAnalysis] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(!compact)
  const [contentExpanded, setContentExpanded] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const getTitle = () => {
    if (title) return title
    switch (type) {
      case 'leak_analysis': return 'AI Leak Analysis'
      case 'nrw_insights': return 'AI NRW Insights'
      case 'dma_recommendation': return 'AI DMA Recommendations'
      case 'alert_priority': return 'AI Priority Analysis'
      case 'sensor_diagnosis': return 'AI Sensor Diagnosis'
      case 'trend_analysis': return 'AI Trend Analysis'
      default: return 'AI Insights'
    }
  }

  const loadAnalysis = async () => {
    if (!data) return
    setLoading(true)
    try {
      const result = await analyzeWithAI({ type, context: data })
      setAnalysis(result.analysis)
      setLastUpdated(new Date())
    } catch (error) {
      setAnalysis('Unable to generate AI insights at this time.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (autoLoad && data) {
      loadAnalysis()
    }
  }, [autoLoad])

  if (compact && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-200 rounded-lg hover:border-purple-300 transition-colors"
      >
        <Brain className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-medium text-purple-700">Get AI Insights</span>
        <Sparkles className="w-3 h-3 text-purple-500" />
      </button>
    )
  }

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 border border-purple-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600">
        <div className="flex items-center gap-2 text-white">
          <Brain className="w-5 h-5" />
          <span className="font-semibold">{getTitle()}</span>
          <Sparkles className="w-4 h-4 text-purple-200" />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadAnalysis}
            disabled={loading}
            className="p-1.5 rounded-lg bg-white/20 hover:bg-white/30 transition-colors disabled:opacity-50"
            title="Refresh analysis"
          >
            <RefreshCw className={`w-4 h-4 text-white ${loading ? 'animate-spin' : ''}`} />
          </button>
          {compact && (
            <button
              onClick={() => setExpanded(false)}
              className="p-1.5 rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
            >
              <ChevronUp className="w-4 h-4 text-white" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center gap-3 text-purple-600">
              <Brain className="w-6 h-6 animate-pulse" />
              <span className="text-sm">AI is analyzing...</span>
            </div>
          </div>
        ) : analysis ? (
          <div className="prose prose-sm max-w-none">
            <div 
              className={`text-slate-700 text-sm leading-relaxed ai-content overflow-hidden transition-all duration-300 ${contentExpanded ? '' : 'max-h-40'}`}
              dangerouslySetInnerHTML={{ 
                __html: analysis
                  .replace(/\*\*(.*?)\*\*/g, '<strong class="text-slate-900">$1</strong>')
                  .replace(/\*(.*?)\*/g, '<em>$1</em>')
                  .replace(/^### (.*$)/gm, '<h4 class="text-base font-semibold text-slate-900 mt-3 mb-1">$1</h4>')
                  .replace(/^## (.*$)/gm, '<h3 class="text-lg font-bold text-purple-800 mt-4 mb-2">$1</h3>')
                  .replace(/^# (.*$)/gm, '<h2 class="text-xl font-bold text-purple-900 mt-4 mb-2">$1</h2>')
                  .replace(/^- (.*$)/gm, '<li class="ml-4 list-disc">$1</li>')
                  .replace(/^(\d+)\. (.*$)/gm, '<li class="ml-4 list-decimal"><strong>$1.</strong> $2</li>')
                  .replace(/\n\n/g, '</p><p class="mt-2">')
                  .replace(/\n/g, '<br/>')
              }}
            />
            {/* Expand/Collapse button */}
            <button
              onClick={() => setContentExpanded(!contentExpanded)}
              className="flex items-center gap-1.5 mt-3 pt-2 border-t border-purple-100 text-xs text-purple-600 hover:text-purple-800 transition-colors w-full"
            >
              {contentExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  <span>Show less</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  <span>Read more</span>
                </>
              )}
              {lastUpdated && (
                <span className="ml-auto text-slate-400">
                  Generated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </button>
          </div>
        ) : (
          <div className="text-center py-6">
            <Brain className="w-10 h-10 text-purple-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500 mb-3">Click to generate AI-powered analysis</p>
            <button
              onClick={loadAnalysis}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium flex items-center gap-2 mx-auto"
            >
              <Sparkles className="w-4 h-4" />
              Generate Insights
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Quick insight button for inline use
interface AIQuickInsightProps {
  data: any
  type: 'leak_analysis' | 'nrw_insights' | 'dma_recommendation' | 'alert_priority' | 'sensor_diagnosis' | 'trend_analysis' | 'general'
  label?: string
}

export function AIQuickInsight({ data, type, label }: AIQuickInsightProps) {
  const [insight, setInsight] = useState('')
  const [loading, setLoading] = useState(false)
  const [show, setShow] = useState(false)

  const getInsight = async () => {
    setLoading(true)
    setShow(true)
    try {
      const result = await analyzeWithAI({ 
        type, 
        context: data,
        question: 'Give a brief 2-3 sentence insight. Be concise.'
      })
      setInsight(result.analysis)
    } catch {
      setInsight('Unable to generate insight.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={getInsight}
        disabled={loading}
        className="flex items-center gap-1.5 px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors disabled:opacity-50"
      >
        <Brain className={`w-3 h-3 ${loading ? 'animate-pulse' : ''}`} />
        {loading ? 'Analyzing...' : (label || 'AI Insight')}
      </button>
      
      {show && !loading && insight && (
        <div className="absolute z-50 top-full mt-2 left-0 w-72 p-3 bg-white border border-purple-200 rounded-lg shadow-xl">
          <div className="flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-600 leading-relaxed">{insight}</p>
          </div>
          <button 
            onClick={() => setShow(false)}
            className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  )
}

// Floating AI analysis button
export function AIAnalyzeButton({ onClick, loading }: { onClick: () => void, loading?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="fixed bottom-24 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105 disabled:opacity-50"
    >
      <Brain className={`w-5 h-5 ${loading ? 'animate-pulse' : ''}`} />
      <span className="font-medium">{loading ? 'Analyzing...' : 'AI Analyze'}</span>
      <Sparkles className="w-4 h-4" />
    </button>
  )
}
