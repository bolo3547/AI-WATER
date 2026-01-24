'use client'

/**
 * AQUAWATCH NRW - EXPLAINABLE AI INSIGHTS PANEL
 * ==============================================
 * 
 * Step 8: Shows why AI detected a leak with:
 * - Top contributing signals
 * - Confidence breakdown by detection method
 * - Evidence timeline chart
 * - Human-readable explanation
 * - Actionable recommendations
 */

import React, { useMemo } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Activity,
  Moon,
  Volume2,
  Radio,
  Brain,
  BarChart3,
  Clock,
  Lightbulb,
  CheckCircle2,
  Info,
  Zap,
} from 'lucide-react'

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface SignalEvidence {
  signal_type: string
  contribution: number
  value: number
  threshold: number
  deviation: number
  description: string
  timestamp: string
  sensor_id?: string | null
  raw_data?: Record<string, unknown>
}

interface ConfidenceBreakdown {
  statistical_confidence: number
  ml_confidence: number
  temporal_confidence: number
  spatial_confidence: number
  acoustic_confidence: number
  overall_confidence: number
  weights: Record<string, number>
}

interface EvidenceTimelinePoint {
  timestamp: string
  signal_type: string
  value: number
  anomaly_score: number
  description: string
  is_key_event: boolean
}

interface AIReason {
  pressure_drop?: SignalEvidence | null
  flow_rise?: SignalEvidence | null
  multi_sensor_agreement?: SignalEvidence | null
  night_flow_deviation?: SignalEvidence | null
  acoustic_anomaly?: SignalEvidence | null
  confidence: ConfidenceBreakdown
  top_signals: string[]
  evidence_timeline: EvidenceTimelinePoint[]
  detection_method: string
  detection_timestamp: string
  analysis_duration_seconds: number
  explanation: string
  recommendations: string[]
  model_version: string
  feature_importance: Record<string, number>
}

interface LeakXAIPanelProps {
  aiReason: AIReason | null | undefined
  leakId?: string
  className?: string
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const SignalIcon: React.FC<{ type: string; className?: string }> = ({ type, className = 'w-4 h-4' }) => {
  const icons: Record<string, React.ReactNode> = {
    pressure_drop: <TrendingDown className={className} />,
    flow_rise: <TrendingUp className={className} />,
    multi_sensor_agreement: <Radio className={className} />,
    night_flow_deviation: <Moon className={className} />,
    acoustic_anomaly: <Volume2 className={className} />,
    statistical_anomaly: <BarChart3 className={className} />,
    ml_detection: <Brain className={className} />,
  }
  return <>{icons[type] || <Activity className={className} />}</>
}

const SignalLabel: Record<string, string> = {
  pressure_drop: 'Pressure Drop',
  flow_rise: 'Flow Increase',
  multi_sensor_agreement: 'Multi-Sensor Agreement',
  night_flow_deviation: 'Night Flow Deviation',
  acoustic_anomaly: 'Acoustic Anomaly',
  statistical_anomaly: 'Statistical Anomaly',
  ml_detection: 'ML Detection',
}

const getContributionColor = (contribution: number): string => {
  if (contribution >= 0.7) return 'text-red-500'
  if (contribution >= 0.5) return 'text-orange-500'
  if (contribution >= 0.3) return 'text-yellow-500'
  return 'text-green-500'
}

const getProgressColor = (value: number): string => {
  if (value >= 0.7) return 'bg-red-500'
  if (value >= 0.5) return 'bg-orange-500'
  if (value >= 0.3) return 'bg-yellow-500'
  return 'bg-green-500'
}

// =============================================================================
// SIGNAL CARD COMPONENT
// =============================================================================

const SignalCard: React.FC<{ signal: SignalEvidence; rank: number }> = ({ signal, rank }) => {
  const contributionPercent = Math.round(signal.contribution * 100)
  
  return (
    <div className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <SignalIcon type={signal.signal_type} className="w-4 h-4 text-muted-foreground" />
          <span className="font-medium text-sm">
            {SignalLabel[signal.signal_type] || signal.signal_type}
          </span>
          <Badge 
            variant={contributionPercent >= 70 ? 'destructive' : contributionPercent >= 50 ? 'default' : 'secondary'}
            className="ml-auto"
          >
            {contributionPercent}% contribution
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">{signal.description}</p>
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <span>Value: {signal.value.toFixed(2)}</span>
          <span>Threshold: {signal.threshold.toFixed(2)}</span>
          {signal.sensor_id && <span>Sensor: {signal.sensor_id}</span>}
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// CONFIDENCE BREAKDOWN COMPONENT
// =============================================================================

const ConfidenceBar: React.FC<{ 
  label: string
  value: number
  weight: number
  icon: React.ReactNode 
}> = ({ label, value, weight, icon }) => {
  const percentage = Math.round(value * 100)
  const weightPercent = Math.round(weight * 100)
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2 text-muted-foreground">
                {icon}
                {label}
              </span>
              <span className={`font-medium ${getContributionColor(value)}`}>
                {percentage}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${getProgressColor(value)}`}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Weight in overall score: {weightPercent}%</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

const ConfidenceBreakdownPanel: React.FC<{ confidence: ConfidenceBreakdown }> = ({ confidence }) => {
  const overallPercent = Math.round(confidence.overall_confidence * 100)
  
  return (
    <div className="space-y-4">
      {/* Overall Confidence */}
      <div className="flex items-center justify-between p-3 bg-primary/5 rounded-lg">
        <span className="font-medium">Overall Confidence</span>
        <div className="flex items-center gap-2">
          <div className="w-24 h-3 bg-muted rounded-full overflow-hidden">
            <div 
              className={`h-full ${getProgressColor(confidence.overall_confidence)}`}
              style={{ width: `${overallPercent}%` }}
            />
          </div>
          <span className={`font-bold text-lg ${getContributionColor(confidence.overall_confidence)}`}>
            {overallPercent}%
          </span>
        </div>
      </div>
      
      {/* Method Breakdown */}
      <div className="grid gap-3">
        <ConfidenceBar 
          label="Statistical"
          value={confidence.statistical_confidence}
          weight={confidence.weights.statistical || 0.2}
          icon={<BarChart3 className="w-4 h-4" />}
        />
        <ConfidenceBar 
          label="Machine Learning"
          value={confidence.ml_confidence}
          weight={confidence.weights.ml || 0.25}
          icon={<Brain className="w-4 h-4" />}
        />
        <ConfidenceBar 
          label="Temporal Analysis"
          value={confidence.temporal_confidence}
          weight={confidence.weights.temporal || 0.2}
          icon={<Clock className="w-4 h-4" />}
        />
        <ConfidenceBar 
          label="Spatial Correlation"
          value={confidence.spatial_confidence}
          weight={confidence.weights.spatial || 0.25}
          icon={<Radio className="w-4 h-4" />}
        />
        <ConfidenceBar 
          label="Acoustic Analysis"
          value={confidence.acoustic_confidence}
          weight={confidence.weights.acoustic || 0.1}
          icon={<Volume2 className="w-4 h-4" />}
        />
      </div>
    </div>
  )
}

// =============================================================================
// EVIDENCE TIMELINE COMPONENT
// =============================================================================

const EvidenceTimeline: React.FC<{ events: EvidenceTimelinePoint[] }> = ({ events }) => {
  const sortedEvents = useMemo(() => 
    [...events].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
    [events]
  )
  
  if (events.length === 0) return null
  
  return (
    <div className="space-y-2">
      {sortedEvents.map((event, index) => {
        const time = new Date(event.timestamp).toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        })
        
        return (
          <div 
            key={index}
            className={`flex items-start gap-3 p-2 rounded-lg transition-colors ${
              event.is_key_event ? 'bg-destructive/10 border border-destructive/20' : 'bg-muted/30'
            }`}
          >
            <div className={`flex items-center justify-center w-6 h-6 rounded-full ${
              event.is_key_event ? 'bg-destructive text-destructive-foreground' : 'bg-muted'
            }`}>
              {event.is_key_event ? (
                <Zap className="w-3 h-3" />
              ) : (
                <span className="text-xs">{index + 1}</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium">{time}</span>
                <SignalIcon type={event.signal_type} className="w-3 h-3 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {SignalLabel[event.signal_type] || event.signal_type}
                </span>
                {event.is_key_event && (
                  <Badge variant="destructive" className="text-xs">Key Event</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">{event.description}</p>
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${getContributionColor(event.anomaly_score)}`}>
                {Math.round(event.anomaly_score * 100)}%
              </div>
              <div className="text-xs text-muted-foreground">anomaly</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// =============================================================================
// MAIN XAI PANEL COMPONENT
// =============================================================================

export const LeakXAIPanel: React.FC<LeakXAIPanelProps> = ({ 
  aiReason, 
  leakId,
  className = '' 
}) => {
  if (!aiReason) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            AI Analysis
          </CardTitle>
          <CardDescription>No AI analysis available for this leak</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Info className="w-6 h-6 mr-2" />
            <span>AI insights will appear here when available</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Collect all signals
  const signals: SignalEvidence[] = []
  if (aiReason.pressure_drop) signals.push(aiReason.pressure_drop)
  if (aiReason.flow_rise) signals.push(aiReason.flow_rise)
  if (aiReason.multi_sensor_agreement) signals.push(aiReason.multi_sensor_agreement)
  if (aiReason.night_flow_deviation) signals.push(aiReason.night_flow_deviation)
  if (aiReason.acoustic_anomaly) signals.push(aiReason.acoustic_anomaly)
  
  // Sort by contribution
  signals.sort((a, b) => b.contribution - a.contribution)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header Card with Explanation */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-primary" />
                Why AI Detected This Leak
              </CardTitle>
              <CardDescription className="mt-1">
                Model v{aiReason.model_version} • Analyzed in {(aiReason.analysis_duration_seconds * 1000).toFixed(0)}ms
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs">
              {aiReason.detection_method}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
              {aiReason.explanation}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Top Contributing Signals */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Top Contributing Signals
          </CardTitle>
          <CardDescription>
            Signals ranked by their contribution to detection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {signals.length > 0 ? (
              signals.slice(0, 4).map((signal, index) => (
                <SignalCard key={signal.signal_type} signal={signal} rank={index + 1} />
              ))
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                No detailed signal information available
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Confidence Breakdown */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Confidence Breakdown
          </CardTitle>
          <CardDescription>
            How each detection method contributed to the overall confidence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ConfidenceBreakdownPanel confidence={aiReason.confidence} />
        </CardContent>
      </Card>

      {/* Evidence Timeline */}
      {aiReason.evidence_timeline.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Evidence Timeline
            </CardTitle>
            <CardDescription>
              Sequence of anomalous events leading to detection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <EvidenceTimeline events={aiReason.evidence_timeline} />
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {aiReason.recommendations.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="w-4 h-4" />
              AI Recommendations
            </CardTitle>
            <CardDescription>
              Suggested next steps based on analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {aiReason.recommendations.map((rec, index) => {
                const isUrgent = rec.toLowerCase().includes('urgent') || rec.toLowerCase().includes('critical')
                return (
                  <div 
                    key={index}
                    className={`flex items-start gap-3 p-3 rounded-lg ${
                      isUrgent ? 'bg-destructive/10 border border-destructive/20' : 'bg-muted/50'
                    }`}
                  >
                    <CheckCircle2 className={`w-4 h-4 mt-0.5 ${
                      isUrgent ? 'text-destructive' : 'text-primary'
                    }`} />
                    <span className={`text-sm ${isUrgent ? 'font-medium' : ''}`}>{rec}</span>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Feature Importance (Compact) */}
      {Object.keys(aiReason.feature_importance).length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Feature Importance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(aiReason.feature_importance)
                .sort(([, a], [, b]) => b - a)
                .map(([feature, importance]) => (
                  <Badge 
                    key={feature}
                    variant={importance >= 0.7 ? 'destructive' : importance >= 0.5 ? 'default' : 'secondary'}
                    className="gap-1"
                  >
                    <SignalIcon type={feature} className="w-3 h-3" />
                    {SignalLabel[feature] || feature}: {Math.round(importance * 100)}%
                  </Badge>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default LeakXAIPanel
