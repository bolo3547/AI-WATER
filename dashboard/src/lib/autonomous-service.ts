// =============================================================================
// AUTONOMOUS OPERATIONS SERVICE
// =============================================================================
// Client-side service for interacting with the Autonomous Operations API
// Handles valve control, AI decisions, and system configuration
// =============================================================================

export interface Valve {
  id: string
  name: string
  location: string
  dma: string
  pipeId: string
  type: 'gate' | 'butterfly' | 'prv' | 'check' | 'isolation'
  status: 'open' | 'closed' | 'partial' | 'error' | 'maintenance'
  openPercent: number
  pressure: number
  flow: number
  autoMode: boolean
  lastAction: string
  lastActionBy: 'ai' | 'manual' | 'schedule' | 'emergency'
  controlledBy: 'manual' | 'ai' | 'schedule'
  health: number
  actuatorStatus: 'online' | 'offline' | 'degraded'
  coordinates: { lat: number; lng: number }
  createdAt: string
  updatedAt: string
}

export interface NetworkSegment {
  id: string
  name: string
  dma: string
  status: 'healthy' | 'isolated' | 'rerouting' | 'alert' | 'maintenance'
  flowIn: number
  flowOut: number
  pressure: number
  activeValves: number
  leakDetected: boolean
  autoHealing: boolean
  lastIncident: string | null
  affectedCustomers: number
  pipes: string[]
  valveIds: string[]
}

export interface AIDecision {
  id: string
  timestamp: string
  type: 'valve_control' | 'isolation' | 'reroute' | 'pressure_adjust' | 'alert' | 'dispatch' | 'notify'
  action: string
  reason: string
  affectedArea: string
  status: 'executed' | 'pending' | 'overridden' | 'failed' | 'cancelled'
  impact: string
  confidence: number
  triggeredBy: string
  executedAt: string | null
  approvedBy: string | null
  waterSaved: number
  customersAffected: number
  riskScore: number
}

export interface PendingAction {
  id: string
  type: string
  target: string
  parameters: Record<string, any>
  status: 'pending' | 'approved' | 'executing' | 'completed' | 'failed'
  requiresApproval: boolean
  createdAt: string
  executedAt: string | null
  riskScore: number
  affectedCustomers: number
  waterSavings: number
}

export interface AutonomousStats {
  totalValves: number
  autoValves: number
  aiControlled: number
  valveErrors: number
  healthySegments: number
  isolatedSegments: number
  alertSegments: number
  totalSegments: number
  decisionsToday: number
  waterSavedToday: number
  incidentsHandled: number
  avgResponseTime: number
  uptime: number
  autonomyLevel: number
  emergencyMode: boolean
  lastSystemCheck: string
}

export interface AutonomousSystemStatus {
  systemOnline: boolean
  autonomyLevel: number
  emergencyMode: boolean
  lastUpdate: string
  activeIncidents: number
  pendingApprovals: number
}

// =============================================================================
// API CLIENT
// =============================================================================

const API_BASE = '/api/autonomous'

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<{ success: boolean; data?: T; error?: string; message?: string }> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    })
    
    const result = await response.json()
    return result
  } catch (error) {
    console.error('Autonomous API error:', error)
    return { success: false, error: 'Network error' }
  }
}

// =============================================================================
// VALVE OPERATIONS
// =============================================================================

export async function getValves(): Promise<Valve[]> {
  const result = await fetchAPI<Valve[]>('?resource=valves')
  return result.data || []
}

export async function controlValve(
  valveId: string,
  position: number,
  reason?: string,
  override?: boolean
): Promise<{ success: boolean; valve?: Valve; decision?: AIDecision; error?: string }> {
  const result = await fetchAPI<{ valve: Valve; decision: AIDecision }>('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'control_valve',
      valveId,
      position,
      reason,
      override,
      operatorId: 'current-user', // Would come from auth
    }),
  })
  
  return {
    success: result.success,
    valve: result.data?.valve,
    decision: result.data?.decision,
    error: result.error,
  }
}

export async function toggleValveAutoMode(
  valveId: string,
  enabled: boolean
): Promise<{ success: boolean; valve?: Valve; error?: string }> {
  const result = await fetchAPI<{ valve: Valve }>('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'toggle_auto_mode',
      valveId,
      enabled,
      operatorId: 'current-user',
    }),
  })
  
  return {
    success: result.success,
    valve: result.data?.valve,
    error: result.error,
  }
}

// =============================================================================
// NETWORK SEGMENTS
// =============================================================================

export async function getNetworkSegments(): Promise<NetworkSegment[]> {
  const result = await fetchAPI<NetworkSegment[]>('?resource=segments')
  return result.data || []
}

// =============================================================================
// AI DECISIONS
// =============================================================================

export async function getDecisions(limit?: number): Promise<AIDecision[]> {
  const query = limit ? `?resource=decisions&limit=${limit}` : '?resource=decisions'
  const result = await fetchAPI<AIDecision[]>(query)
  return result.data || []
}

// =============================================================================
// PENDING ACTIONS
// =============================================================================

export async function getPendingActions(): Promise<PendingAction[]> {
  const result = await fetchAPI<PendingAction[]>('?resource=pending')
  return result.data || []
}

export async function approveAction(
  actionId: string
): Promise<{ success: boolean; error?: string }> {
  const result = await fetchAPI('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'approve_action',
      actionId,
      operatorId: 'current-user',
    }),
  })
  
  return { success: result.success, error: result.error }
}

export async function rejectAction(
  actionId: string,
  reason?: string
): Promise<{ success: boolean; error?: string }> {
  const result = await fetchAPI('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'reject_action',
      actionId,
      reason,
      operatorId: 'current-user',
    }),
  })
  
  return { success: result.success, error: result.error }
}

// =============================================================================
// SYSTEM CONFIGURATION
// =============================================================================

export async function getStats(): Promise<AutonomousStats | null> {
  const result = await fetchAPI<AutonomousStats>('?resource=stats')
  return result.data || null
}

export async function getSystemStatus(): Promise<AutonomousSystemStatus | null> {
  const result = await fetchAPI<AutonomousSystemStatus>('?resource=status')
  return result.data || null
}

export async function setAutonomyLevel(
  level: number
): Promise<{ success: boolean; description?: string; error?: string }> {
  const result = await fetchAPI<{ autonomyLevel: number; description: string }>('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'set_autonomy_level',
      level,
      operatorId: 'current-user',
    }),
  })
  
  return {
    success: result.success,
    description: result.data?.description,
    error: result.error,
  }
}

export async function toggleEmergencyMode(
  enabled: boolean,
  reason?: string
): Promise<{ success: boolean; error?: string }> {
  const result = await fetchAPI('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'toggle_emergency',
      enabled,
      reason,
      operatorId: 'current-user',
    }),
  })
  
  return { success: result.success, error: result.error }
}

// =============================================================================
// INCIDENT SIMULATION (FOR TESTING)
// =============================================================================

export async function simulateIncident(
  type: 'pipe_burst' | 'pressure_drop' | 'high_night_flow',
  location: string,
  severity?: 'low' | 'medium' | 'high' | 'critical'
): Promise<{ success: boolean; actions?: AIDecision[]; error?: string }> {
  const result = await fetchAPI<{ actions: AIDecision[] }>('', {
    method: 'POST',
    body: JSON.stringify({
      action: 'simulate_incident',
      type,
      location,
      severity: severity || 'high',
    }),
  })
  
  return {
    success: result.success,
    actions: result.data?.actions,
    error: result.error,
  }
}

// =============================================================================
// FULL SYSTEM STATE
// =============================================================================

export interface FullAutonomousState {
  valves: Valve[]
  segments: NetworkSegment[]
  decisions: AIDecision[]
  pendingActions: PendingAction[]
  stats: AutonomousStats
  autonomyLevel: number
  emergencyMode: boolean
}

export async function getFullSystemState(): Promise<FullAutonomousState | null> {
  const result = await fetchAPI<FullAutonomousState>('')
  return result.data || null
}

// =============================================================================
// REAL-TIME UPDATES (POLLING)
// =============================================================================

export function subscribeToUpdates(
  callback: (state: FullAutonomousState) => void,
  intervalMs: number = 5000
): () => void {
  let isRunning = true
  
  const poll = async () => {
    if (!isRunning) return
    
    const state = await getFullSystemState()
    if (state && isRunning) {
      callback(state)
    }
    
    if (isRunning) {
      setTimeout(poll, intervalMs)
    }
  }
  
  poll()
  
  // Return unsubscribe function
  return () => {
    isRunning = false
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

export function getValveStatusColor(status: Valve['status']): string {
  switch (status) {
    case 'open': return 'bg-green-100 text-green-700 border-green-200'
    case 'closed': return 'bg-red-100 text-red-700 border-red-200'
    case 'partial': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
    case 'error': return 'bg-red-100 text-red-700 border-red-200'
    case 'maintenance': return 'bg-blue-100 text-blue-700 border-blue-200'
    default: return 'bg-gray-100 text-gray-700'
  }
}

export function getSegmentStatusColor(status: NetworkSegment['status']): string {
  switch (status) {
    case 'healthy': return 'bg-green-500'
    case 'isolated': return 'bg-red-500'
    case 'rerouting': return 'bg-yellow-500'
    case 'alert': return 'bg-orange-500'
    case 'maintenance': return 'bg-blue-500'
    default: return 'bg-gray-500'
  }
}

export function getDecisionTypeIcon(type: AIDecision['type']): string {
  switch (type) {
    case 'isolation': return '🔒'
    case 'reroute': return '↪️'
    case 'pressure_adjust': return '📊'
    case 'valve_control': return '⚙️'
    case 'alert': return '⚠️'
    case 'dispatch': return '🚗'
    case 'notify': return '📱'
    default: return '📋'
  }
}

export function getAutonomyLevelInfo(level: number): {
  name: string
  description: string
  color: string
} {
  const levels: Record<number, { name: string; description: string; color: string }> = {
    0: { name: 'Manual', description: 'All actions require human control', color: 'text-gray-600' },
    1: { name: 'Assisted', description: 'AI suggests, human approves all', color: 'text-blue-600' },
    2: { name: 'Supervised', description: 'AI executes alerts, human approves physical', color: 'text-cyan-600' },
    3: { name: 'Conditional', description: 'AI handles most, human for high-risk', color: 'text-green-600' },
    4: { name: 'High', description: 'AI handles 99%, human for emergencies', color: 'text-purple-600' },
    5: { name: 'Full Autonomy', description: 'AI manages everything', color: 'text-red-600' },
  }
  return levels[level] || levels[0]
}

export function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return 'Never'
  
  const date = new Date(dateString)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hr ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  return date.toLocaleDateString()
}
