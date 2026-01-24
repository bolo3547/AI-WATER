// =============================================================================
// AUTONOMOUS REAL-TIME STREAM HOOK
// =============================================================================
// React hook for subscribing to real-time autonomous system updates via SSE
// =============================================================================

import { useEffect, useRef, useState, useCallback } from 'react'
import { Valve, NetworkSegment, AIDecision } from '@/lib/autonomous-service'

interface StreamEvent {
  type: 'connected' | 'decision' | 'valve_update' | 'segment_update' | 'incident' | 'heartbeat'
  data?: any
  message?: string
  timestamp?: string
}

interface Incident {
  id: string
  timestamp: string
  type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  location: string
  autoResponseTriggered: boolean
}

interface UseAutonomousStreamOptions {
  onDecision?: (decision: AIDecision) => void
  onValveUpdate?: (update: Partial<Valve> & { id: string }) => void
  onSegmentUpdate?: (update: Partial<NetworkSegment> & { id: string }) => void
  onIncident?: (incident: Incident) => void
  onConnected?: () => void
  onDisconnected?: () => void
  autoReconnect?: boolean
}

interface UseAutonomousStreamReturn {
  isConnected: boolean
  lastHeartbeat: Date | null
  recentDecisions: AIDecision[]
  recentIncidents: Incident[]
  connect: () => void
  disconnect: () => void
}

export function useAutonomousStream(options: UseAutonomousStreamOptions = {}): UseAutonomousStreamReturn {
  const {
    onDecision,
    onValveUpdate,
    onSegmentUpdate,
    onIncident,
    onConnected,
    onDisconnected,
    autoReconnect = true
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null)
  const [recentDecisions, setRecentDecisions] = useState<AIDecision[]>([])
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([])
  
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    try {
      const eventSource = new EventSource('/api/autonomous/stream')
      eventSourceRef.current = eventSource

      eventSource.onopen = () => {
        setIsConnected(true)
        onConnected?.()
      }

      eventSource.onmessage = (event) => {
        try {
          const parsed: StreamEvent = JSON.parse(event.data)
          
          switch (parsed.type) {
            case 'connected':
              setIsConnected(true)
              onConnected?.()
              break
              
            case 'decision':
              if (parsed.data) {
                const decision = parsed.data as AIDecision
                setRecentDecisions(prev => [decision, ...prev].slice(0, 50))
                onDecision?.(decision)
              }
              break
              
            case 'valve_update':
              if (parsed.data) {
                onValveUpdate?.(parsed.data)
              }
              break
              
            case 'segment_update':
              if (parsed.data) {
                onSegmentUpdate?.(parsed.data)
              }
              break
              
            case 'incident':
              if (parsed.data) {
                const incident = parsed.data as Incident
                setRecentIncidents(prev => [incident, ...prev].slice(0, 20))
                onIncident?.(incident)
              }
              break
              
            case 'heartbeat':
              setLastHeartbeat(new Date())
              break
          }
        } catch (err) {
          console.error('Failed to parse stream event:', err)
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
        onDisconnected?.()
        eventSource.close()
        eventSourceRef.current = null
        
        // Auto reconnect
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 5000)
        }
      }
    } catch (err) {
      console.error('Failed to connect to stream:', err)
      setIsConnected(false)
    }
  }, [onConnected, onDisconnected, onDecision, onValveUpdate, onSegmentUpdate, onIncident, autoReconnect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    isConnected,
    lastHeartbeat,
    recentDecisions,
    recentIncidents,
    connect,
    disconnect
  }
}

// =============================================================================
// SIMPLE STREAM CONSUMER
// =============================================================================
// For components that just want to update their local state

export function useAutonomousUpdates(
  valves: Valve[],
  segments: NetworkSegment[],
  decisions: AIDecision[],
  setValves: React.Dispatch<React.SetStateAction<Valve[]>>,
  setSegments: React.Dispatch<React.SetStateAction<NetworkSegment[]>>,
  setDecisions: React.Dispatch<React.SetStateAction<AIDecision[]>>
) {
  const { isConnected, recentIncidents } = useAutonomousStream({
    onDecision: (decision) => {
      setDecisions(prev => [decision, ...prev].slice(0, 100))
    },
    onValveUpdate: (update) => {
      setValves(prev => prev.map(v => 
        v.id === update.id 
          ? { ...v, ...update, updatedAt: update.updatedAt || new Date().toISOString() }
          : v
      ))
    },
    onSegmentUpdate: (update) => {
      setSegments(prev => prev.map(s =>
        s.id === update.id
          ? { ...s, ...update }
          : s
      ))
    },
    onIncident: (incident) => {
      // Could show toast notification here
      console.log('🚨 Incident:', incident)
    }
  })

  return { isConnected, recentIncidents }
}
