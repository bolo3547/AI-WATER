/**
 * AquaWatch Smart Meters Service
 * ==============================
 * TypeScript service layer for Smart Meter API interactions
 * Handles connection state awareness - no fake data when disconnected
 */

// ============================================================================
// TYPES
// ============================================================================

export type MeterType = 'residential' | 'commercial' | 'industrial' | 'dma_inlet' | 'dma_outlet';
export type MeterStatus = 'online' | 'offline' | 'warning' | 'critical' | 'disconnected';
export type AlertType = 'high_consumption' | 'night_flow' | 'reverse_flow' | 'tamper' | 'leak' | 'battery_low' | 'offline' | 'signal_lost';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type ConnectionQuality = 'excellent' | 'good' | 'fair' | 'poor' | 'disconnected';

export interface MeterAlert {
  id: string;
  meterId: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface SmartMeter {
  id: string;
  serialNumber: string;
  customerName: string;
  address: string;
  type: MeterType;
  dma: string;
  lat: number;
  lng: number;
  status: MeterStatus;
  connected: boolean;
  lastConnected: string | null;
  currentReading: number | null;
  flowRate: number | null;
  batteryLevel: number | null;
  signalStrength: number | null;
  lastUpdate: string | null;
  dailyUsage: number | null;
  monthlyUsage: number | null;
  hourlyData: number[] | null;
}

export interface DMABalance {
  id: string;
  name: string;
  zone: string;
  totalInput: number | null;
  totalOutput: number | null;
  billedConsumption: number | null;
  nrwPercentage: number | null;
  meterCount: number;
  connectedMeters: number;
  status: 'good' | 'concern' | 'poor' | 'unknown';
}

export interface SystemConnection {
  amiGatewayConnected: boolean;
  mqttBrokerConnected: boolean;
  lastHeartbeat: string | null;
  connectionQuality: ConnectionQuality;
}

export interface SystemStats {
  totalMeters: number;
  connectedMeters: number;
  onlineMeters: number;
  warningMeters: number;
  criticalMeters: number;
  offlineMeters: number;
  totalFlow: number | null;
  totalDailyUsage: number | null;
  avgNRW: number | null;
  dataAvailable: boolean;
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

const API_BASE = '/api/smart-meters';

/**
 * Get all meters with optional filtering
 */
export async function getMeters(options?: { dma?: string; type?: string }): Promise<{
  success: boolean;
  systemConnected: boolean;
  connectionQuality: ConnectionQuality;
  meters: SmartMeter[];
  timestamp: string;
}> {
  const params = new URLSearchParams({ action: 'meters' });
  if (options?.dma) params.append('dma', options.dma);
  if (options?.type) params.append('type', options.type);
  
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get a single meter by ID
 */
export async function getMeter(id: string): Promise<{
  success: boolean;
  meter: SmartMeter;
  systemConnected: boolean;
}> {
  const params = new URLSearchParams({ action: 'meter', id });
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get all DMA balances
 */
export async function getDMAs(): Promise<{
  success: boolean;
  systemConnected: boolean;
  dmas: DMABalance[];
  timestamp: string;
}> {
  const params = new URLSearchParams({ action: 'dmas' });
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get a single DMA balance
 */
export async function getDMA(id: string): Promise<{
  success: boolean;
  dma: DMABalance;
  systemConnected: boolean;
}> {
  const params = new URLSearchParams({ action: 'dma', id });
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get system statistics
 */
export async function getStats(): Promise<{
  success: boolean;
  stats: SystemStats;
  connection: SystemConnection;
  timestamp: string;
}> {
  const params = new URLSearchParams({ action: 'stats' });
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get connection status
 */
export async function getConnectionStatus(): Promise<{
  success: boolean;
  connection: SystemConnection;
  timestamp: string;
}> {
  const params = new URLSearchParams({ action: 'connection' });
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Get active alerts
 */
export async function getAlerts(unacknowledgedOnly = false): Promise<{
  success: boolean;
  alerts: MeterAlert[];
  count: number;
}> {
  const params = new URLSearchParams({ action: 'alerts' });
  if (unacknowledgedOnly) params.append('unacknowledged', 'true');
  const response = await fetch(`${API_BASE}?${params}`);
  return response.json();
}

/**
 * Connect to AMI Gateway
 */
export async function connect(): Promise<{
  success: boolean;
  message: string;
  connection: SystemConnection;
  metersOnline: number;
}> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'connect' })
  });
  return response.json();
}

/**
 * Disconnect from AMI Gateway
 */
export async function disconnect(): Promise<{
  success: boolean;
  message: string;
  connection: SystemConnection;
}> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'disconnect' })
  });
  return response.json();
}

/**
 * Refresh a single meter's data
 */
export async function refreshMeter(meterId: string): Promise<{
  success: boolean;
  meter?: SmartMeter;
  message?: string;
  error?: string;
}> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'refresh_meter', meterId })
  });
  return response.json();
}

/**
 * Refresh all meters' data
 */
export async function refreshAllMeters(): Promise<{
  success: boolean;
  message: string;
  metersUpdated: number;
  timestamp: string;
  error?: string;
}> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'refresh_all' })
  });
  return response.json();
}

/**
 * Acknowledge an alert
 */
export async function acknowledgeAlert(alertId: string): Promise<{
  success: boolean;
  message?: string;
  error?: string;
}> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'acknowledge_alert', alertId })
  });
  return response.json();
}

// ============================================================================
// STREAM SUBSCRIPTION
// ============================================================================

export type StreamEventType = 'connection' | 'meter_update' | 'dma_update' | 'alert' | 'heartbeat' | 'info';

export interface StreamEvent {
  type: StreamEventType;
  data: any;
}

export interface StreamHandlers {
  onConnection?: (data: { connected: boolean; quality: ConnectionQuality; timestamp: string }) => void;
  onMeterUpdate?: (data: { meterId: string; flowRate: number; signalStrength: number; batteryLevel: number; timestamp: string }) => void;
  onDMAUpdate?: (data: { dmaId: string; nrwPercentage: number; connectedMeters: number; timestamp: string }) => void;
  onAlert?: (data: MeterAlert) => void;
  onHeartbeat?: (data: { timestamp: string; uptime: number }) => void;
  onInfo?: (data: { message: string }) => void;
  onError?: (error: Error) => void;
}

/**
 * Subscribe to real-time meter updates via SSE
 * Returns an unsubscribe function
 */
export function subscribeToMeterStream(handlers: StreamHandlers): () => void {
  const eventSource = new EventSource('/api/smart-meters/stream');
  
  eventSource.addEventListener('connection', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onConnection?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.addEventListener('meter_update', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onMeterUpdate?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.addEventListener('dma_update', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onDMAUpdate?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.addEventListener('alert', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onAlert?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.addEventListener('heartbeat', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onHeartbeat?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.addEventListener('info', (event) => {
    try {
      const data = JSON.parse(event.data);
      handlers.onInfo?.(data);
    } catch (e) {
      handlers.onError?.(e as Error);
    }
  });
  
  eventSource.onerror = (error) => {
    handlers.onError?.(new Error('Stream connection error'));
  };
  
  // Return unsubscribe function
  return () => {
    eventSource.close();
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get meter type display name
 */
export function getMeterTypeDisplay(type: MeterType): string {
  switch (type) {
    case 'residential': return 'Residential';
    case 'commercial': return 'Commercial';
    case 'industrial': return 'Industrial';
    case 'dma_inlet': return 'DMA Inlet';
    case 'dma_outlet': return 'DMA Outlet';
    default: return type;
  }
}

/**
 * Get status display color class
 */
export function getStatusColor(status: MeterStatus): string {
  switch (status) {
    case 'online': return 'bg-green-500';
    case 'warning': return 'bg-yellow-500';
    case 'critical': return 'bg-red-500';
    case 'offline': return 'bg-gray-500';
    case 'disconnected': return 'bg-gray-600';
    default: return 'bg-gray-500';
  }
}

/**
 * Get connection quality display
 */
export function getConnectionQualityDisplay(quality: ConnectionQuality): {
  label: string;
  color: string;
  icon: 'wifi' | 'wifi-low' | 'wifi-off';
} {
  switch (quality) {
    case 'excellent':
      return { label: 'Excellent', color: 'text-green-400', icon: 'wifi' };
    case 'good':
      return { label: 'Good', color: 'text-green-300', icon: 'wifi' };
    case 'fair':
      return { label: 'Fair', color: 'text-yellow-400', icon: 'wifi-low' };
    case 'poor':
      return { label: 'Poor', color: 'text-orange-400', icon: 'wifi-low' };
    case 'disconnected':
      return { label: 'Disconnected', color: 'text-gray-500', icon: 'wifi-off' };
    default:
      return { label: 'Unknown', color: 'text-gray-400', icon: 'wifi-off' };
  }
}

/**
 * Format flow rate for display
 */
export function formatFlowRate(flowRate: number | null): string {
  if (flowRate === null) return '-- L/h';
  if (flowRate >= 1000) return `${(flowRate / 1000).toFixed(1)} m³/h`;
  return `${Math.round(flowRate)} L/h`;
}

/**
 * Format reading for display
 */
export function formatReading(reading: number | null): string {
  if (reading === null) return '-- m³';
  return `${reading.toFixed(1)} m³`;
}
