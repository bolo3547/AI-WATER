'use client'

// =============================================================================
// SYNC SERVICE
// =============================================================================
// Handles synchronization between offline IndexedDB and online API
// - Detects online/offline status
// - Queues actions when offline
// - Syncs pending actions when back online
// - Background sync support
// =============================================================================

import {
  WorkOrder,
  PendingAction,
  getAllPendingActions,
  getPendingAction,
  removePendingAction,
  updatePendingAction,
  saveWorkOrders,
  getWorkOrder,
  updateWorkOrderLocally,
  getSyncStatus,
  updateSyncStatus,
  markSyncComplete,
  markSyncError,
  getAllWorkOrders,
  getPendingActionCount,
} from './indexeddb'

// =============================================================================
// TYPES
// =============================================================================

export interface SyncResult {
  success: boolean
  synced: number
  failed: number
  errors: string[]
}

export interface WorkOrderSyncResponse {
  workOrders: WorkOrder[]
  total: number
  lastUpdated: string
}

export type SyncEventType = 
  | 'sync_started'
  | 'sync_completed'
  | 'sync_failed'
  | 'action_synced'
  | 'action_failed'
  | 'online'
  | 'offline'

export interface SyncEvent {
  type: SyncEventType
  data?: Record<string, unknown>
  timestamp: string
}

type SyncEventListener = (event: SyncEvent) => void

// =============================================================================
// SYNC SERVICE CLASS
// =============================================================================

class SyncService {
  private listeners: Set<SyncEventListener> = new Set()
  private isSyncing = false
  private syncInterval: NodeJS.Timeout | null = null
  private token: string | null = null
  private userId: string | null = null
  private tenantId: string = 'default-tenant'
  
  // API base URL
  private get apiBaseUrl(): string {
    if (typeof window === 'undefined') return ''
    return process.env.NEXT_PUBLIC_API_URL || ''
  }
  
  // =============================================================================
  // INITIALIZATION
  // =============================================================================
  
  /**
   * Initialize the sync service with auth credentials
   */
  initialize(token: string, userId: string, tenantId?: string): void {
    this.token = token
    this.userId = userId
    if (tenantId) this.tenantId = tenantId
    
    // Setup online/offline listeners
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline)
      window.addEventListener('offline', this.handleOffline)
      
      // Update initial status
      updateSyncStatus({ isOnline: navigator.onLine })
    }
  }
  
  /**
   * Cleanup on logout
   */
  cleanup(): void {
    this.token = null
    this.userId = null
    this.stopAutoSync()
    
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline)
      window.removeEventListener('offline', this.handleOffline)
    }
  }
  
  // =============================================================================
  // EVENT HANDLING
  // =============================================================================
  
  private handleOnline = async (): Promise<void> => {
    await updateSyncStatus({ isOnline: true })
    this.emit({ type: 'online', timestamp: new Date().toISOString() })
    
    // Trigger sync when back online
    this.syncAll()
  }
  
  private handleOffline = async (): Promise<void> => {
    await updateSyncStatus({ isOnline: false })
    this.emit({ type: 'offline', timestamp: new Date().toISOString() })
  }
  
  /**
   * Subscribe to sync events
   */
  subscribe(listener: SyncEventListener): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }
  
  private emit(event: SyncEvent): void {
    this.listeners.forEach(listener => listener(event))
  }
  
  // =============================================================================
  // API HELPERS
  // =============================================================================
  
  private async apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.apiBaseUrl}${endpoint}`
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
      ...(options.headers || {}),
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API Error: ${response.status}`)
    }
    
    return response.json()
  }
  
  // =============================================================================
  // WORK ORDER SYNC
  // =============================================================================
  
  /**
   * Fetch work orders from server and save to IndexedDB
   */
  async fetchWorkOrders(): Promise<WorkOrder[]> {
    if (!navigator.onLine) {
      // Return cached work orders when offline
      return getAllWorkOrders()
    }
    
    try {
      const response = await this.apiRequest<WorkOrderSyncResponse>(
        `/api/v1/tenants/${this.tenantId}/technician/work-orders?assigned_to=${this.userId}`
      )
      
      // Save to IndexedDB
      await saveWorkOrders(response.workOrders)
      
      return response.workOrders
    } catch (error) {
      console.error('Failed to fetch work orders:', error)
      
      // Return cached data on error
      return getAllWorkOrders()
    }
  }
  
  /**
   * Fetch a single work order
   */
  async fetchWorkOrder(workOrderId: string): Promise<WorkOrder | undefined> {
    if (!navigator.onLine) {
      return getWorkOrder(workOrderId)
    }
    
    try {
      const response = await this.apiRequest<{ workOrder: WorkOrder }>(
        `/api/v1/tenants/${this.tenantId}/technician/work-orders/${workOrderId}`
      )
      
      // Update local copy
      await updateWorkOrderLocally(workOrderId, {
        ...response.workOrder,
        _syncStatus: 'synced',
      })
      
      return response.workOrder
    } catch (error) {
      console.error('Failed to fetch work order:', error)
      return getWorkOrder(workOrderId)
    }
  }
  
  // =============================================================================
  // PENDING ACTIONS SYNC
  // =============================================================================
  
  /**
   * Sync a single pending action to the server
   */
  private async syncAction(action: PendingAction): Promise<boolean> {
    try {
      // Increment attempt count
      await updatePendingAction(action.id, {
        attempts: action.attempts + 1,
        lastAttempt: new Date().toISOString(),
      })
      
      // Build the API request based on action type
      const endpoint = this.getActionEndpoint(action)
      const method = this.getActionMethod(action)
      const body = this.getActionBody(action)
      
      await this.apiRequest(endpoint, { method, body: JSON.stringify(body) })
      
      // Success - remove from pending
      await removePendingAction(action.id)
      
      // Update local work order sync status
      const workOrder = await getWorkOrder(action.workOrderId)
      if (workOrder) {
        await updateWorkOrderLocally(action.workOrderId, { _syncStatus: 'synced' })
      }
      
      this.emit({
        type: 'action_synced',
        data: { actionId: action.id, workOrderId: action.workOrderId },
        timestamp: new Date().toISOString(),
      })
      
      return true
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      await updatePendingAction(action.id, {
        error: errorMessage,
      })
      
      // Mark work order with error status
      await updateWorkOrderLocally(action.workOrderId, { _syncStatus: 'error' })
      
      this.emit({
        type: 'action_failed',
        data: { actionId: action.id, error: errorMessage },
        timestamp: new Date().toISOString(),
      })
      
      return false
    }
  }
  
  private getActionEndpoint(action: PendingAction): string {
    const base = `/api/v1/tenants/${this.tenantId}/technician/work-orders/${action.workOrderId}`
    
    switch (action.actionType) {
      case 'status_update':
        return `${base}/status`
      case 'add_note':
        return `${base}/notes`
      case 'add_photo':
        return `${base}/photos`
      case 'update_materials':
        return `${base}/materials`
      case 'complete_order':
        return `${base}/complete`
      case 'update_duration':
        return `${base}/duration`
      default:
        return base
    }
  }
  
  private getActionMethod(action: PendingAction): string {
    switch (action.actionType) {
      case 'status_update':
      case 'update_materials':
      case 'update_duration':
        return 'PATCH'
      case 'add_note':
      case 'add_photo':
      case 'complete_order':
        return 'POST'
      default:
        return 'POST'
    }
  }
  
  private getActionBody(action: PendingAction): Record<string, unknown> {
    return {
      ...action.payload,
      offline_action_id: action.id,
      offline_created_at: action.createdAt,
    }
  }
  
  /**
   * Sync all pending actions
   */
  async syncPendingActions(): Promise<SyncResult> {
    const actions = await getAllPendingActions()
    
    // Sort by creation time (oldest first)
    actions.sort((a, b) => 
      new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    )
    
    const result: SyncResult = {
      success: true,
      synced: 0,
      failed: 0,
      errors: [],
    }
    
    for (const action of actions) {
      // Skip if too many attempts
      if (action.attempts >= 5) {
        result.failed++
        result.errors.push(`Action ${action.id} exceeded max attempts`)
        continue
      }
      
      const success = await this.syncAction(action)
      
      if (success) {
        result.synced++
      } else {
        result.failed++
        if (action.error) {
          result.errors.push(action.error)
        }
      }
    }
    
    result.success = result.failed === 0
    return result
  }
  
  // =============================================================================
  // FULL SYNC
  // =============================================================================
  
  /**
   * Perform full sync (pending actions + fetch latest work orders)
   */
  async syncAll(): Promise<SyncResult> {
    if (this.isSyncing) {
      return { success: false, synced: 0, failed: 0, errors: ['Sync already in progress'] }
    }
    
    if (!navigator.onLine) {
      return { success: false, synced: 0, failed: 0, errors: ['Device is offline'] }
    }
    
    this.isSyncing = true
    this.emit({ type: 'sync_started', timestamp: new Date().toISOString() })
    
    try {
      // 1. Sync pending actions first
      const actionResult = await this.syncPendingActions()
      
      // 2. Fetch latest work orders
      await this.fetchWorkOrders()
      
      // 3. Update sync status
      await markSyncComplete()
      await updateSyncStatus({ pendingCount: await getPendingActionCount() })
      
      this.emit({
        type: 'sync_completed',
        data: actionResult,
        timestamp: new Date().toISOString(),
      })
      
      return actionResult
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      await markSyncError(errorMessage)
      
      this.emit({
        type: 'sync_failed',
        data: { error: errorMessage },
        timestamp: new Date().toISOString(),
      })
      
      return {
        success: false,
        synced: 0,
        failed: 0,
        errors: [errorMessage],
      }
    } finally {
      this.isSyncing = false
    }
  }
  
  // =============================================================================
  // AUTO SYNC
  // =============================================================================
  
  /**
   * Start automatic sync at regular intervals
   */
  startAutoSync(intervalMs: number = 60000): void {
    this.stopAutoSync()
    
    this.syncInterval = setInterval(() => {
      if (navigator.onLine && !this.isSyncing) {
        this.syncAll()
      }
    }, intervalMs)
    
    // Also do initial sync
    if (navigator.onLine) {
      this.syncAll()
    }
  }
  
  /**
   * Stop automatic sync
   */
  stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
      this.syncInterval = null
    }
  }
  
  // =============================================================================
  // STATUS CHECKS
  // =============================================================================
  
  /**
   * Check if currently syncing
   */
  get syncing(): boolean {
    return this.isSyncing
  }
  
  /**
   * Check if online
   */
  get online(): boolean {
    return typeof navigator !== 'undefined' ? navigator.onLine : true
  }
  
  /**
   * Get pending action count
   */
  async getPendingCount(): Promise<number> {
    return getPendingActionCount()
  }
  
  /**
   * Get full sync status
   */
  async getStatus(): Promise<{
    isOnline: boolean
    isSyncing: boolean
    pendingCount: number
    lastSync: string | null
    lastError: string | null
  }> {
    const status = await getSyncStatus()
    const pendingCount = await getPendingActionCount()
    
    return {
      isOnline: navigator.onLine,
      isSyncing: this.isSyncing,
      pendingCount,
      lastSync: status.lastSyncAt,
      lastError: status.lastError,
    }
  }
}

// =============================================================================
// SINGLETON EXPORT
// =============================================================================

export const syncService = new SyncService()

// =============================================================================
// REACT HOOK
// =============================================================================

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from './auth'

export interface UseSyncReturn {
  isOnline: boolean
  isSyncing: boolean
  pendingCount: number
  lastSync: string | null
  lastError: string | null
  sync: () => Promise<SyncResult>
  fetchWorkOrders: () => Promise<WorkOrder[]>
}

export function useSync(): UseSyncReturn {
  const { token, user } = useAuth()
  
  const [isOnline, setIsOnline] = useState(true)
  const [isSyncing, setIsSyncing] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)
  const [lastSync, setLastSync] = useState<string | null>(null)
  const [lastError, setLastError] = useState<string | null>(null)
  
  // Initialize sync service
  useEffect(() => {
    if (token && user) {
      syncService.initialize(token, user.user_id)
      syncService.startAutoSync(60000) // Sync every minute
      
      // Get initial status
      syncService.getStatus().then(status => {
        setIsOnline(status.isOnline)
        setPendingCount(status.pendingCount)
        setLastSync(status.lastSync)
        setLastError(status.lastError)
      })
      
      return () => {
        syncService.stopAutoSync()
      }
    }
  }, [token, user])
  
  // Subscribe to sync events
  useEffect(() => {
    const unsubscribe = syncService.subscribe((event) => {
      switch (event.type) {
        case 'online':
          setIsOnline(true)
          break
        case 'offline':
          setIsOnline(false)
          break
        case 'sync_started':
          setIsSyncing(true)
          break
        case 'sync_completed':
          setIsSyncing(false)
          setLastSync(event.timestamp)
          setLastError(null)
          syncService.getPendingCount().then(setPendingCount)
          break
        case 'sync_failed':
          setIsSyncing(false)
          setLastError((event.data?.error as string) || 'Sync failed')
          break
        case 'action_synced':
        case 'action_failed':
          syncService.getPendingCount().then(setPendingCount)
          break
      }
    })
    
    return unsubscribe
  }, [])
  
  const sync = useCallback(async () => {
    return syncService.syncAll()
  }, [])
  
  const fetchWorkOrders = useCallback(async () => {
    return syncService.fetchWorkOrders()
  }, [])
  
  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSync,
    lastError,
    sync,
    fetchWorkOrders,
  }
}
