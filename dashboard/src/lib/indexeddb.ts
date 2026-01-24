'use client'

// =============================================================================
// INDEXEDDB HELPER
// =============================================================================
// Provides offline storage for technician mobile experience
// - Work orders cache
// - Pending actions queue (status updates, notes, photos)
// - Sync status tracking
// =============================================================================

const DB_NAME = 'aquawatch_technician'
const DB_VERSION = 1

// Store names
export const STORES = {
  WORK_ORDERS: 'work_orders',
  PENDING_ACTIONS: 'pending_actions',
  SYNC_STATUS: 'sync_status',
  USER_DATA: 'user_data',
} as const

// =============================================================================
// TYPES
// =============================================================================

export type WorkOrderStatus = 'pending' | 'assigned' | 'in-progress' | 'completed' | 'cancelled'
export type Priority = 'critical' | 'high' | 'medium' | 'low'
export type WorkOrderType = 'leak_repair' | 'meter_install' | 'meter_replace' | 'pipe_repair' | 'valve_maintenance' | 'inspection'

export interface WorkOrder {
  id: string
  title: string
  type: WorkOrderType
  description: string
  location: string
  dma: string
  lat: number
  lng: number
  priority: Priority
  status: WorkOrderStatus
  createdAt: string
  scheduledDate: string
  assignedTo: string | null
  assignedToId: string | null
  assignedTeam: string | null
  estimatedDuration: number // hours
  actualDuration: number | null
  materials: { item: string; quantity: number; used: number }[]
  notes: string[]
  photos: string[]
  customerContact: string | null
  customerPhone: string | null
  leakId: string | null
  completedAt: string | null
  // Offline tracking
  _localUpdatedAt?: string
  _syncStatus?: 'synced' | 'pending' | 'error'
}

export type PendingActionType = 
  | 'status_update'
  | 'add_note'
  | 'add_photo'
  | 'update_materials'
  | 'update_duration'
  | 'complete_order'

export interface PendingAction {
  id: string
  workOrderId: string
  actionType: PendingActionType
  payload: Record<string, unknown>
  createdAt: string
  attempts: number
  lastAttempt: string | null
  error: string | null
}

export interface SyncStatus {
  id: string // 'global'
  lastSyncAt: string | null
  pendingCount: number
  isOnline: boolean
  lastError: string | null
}

// =============================================================================
// DATABASE INITIALIZATION
// =============================================================================

let dbInstance: IDBDatabase | null = null
let dbPromise: Promise<IDBDatabase> | null = null

export function openDatabase(): Promise<IDBDatabase> {
  if (dbInstance) {
    return Promise.resolve(dbInstance)
  }
  
  if (dbPromise) {
    return dbPromise
  }
  
  dbPromise = new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('IndexedDB not available'))
      return
    }
    
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    
    request.onerror = () => {
      dbPromise = null
      reject(request.error)
    }
    
    request.onsuccess = () => {
      dbInstance = request.result
      
      // Handle connection close
      dbInstance.onclose = () => {
        dbInstance = null
        dbPromise = null
      }
      
      resolve(dbInstance)
    }
    
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result
      
      // Work Orders store
      if (!db.objectStoreNames.contains(STORES.WORK_ORDERS)) {
        const workOrdersStore = db.createObjectStore(STORES.WORK_ORDERS, { keyPath: 'id' })
        workOrdersStore.createIndex('status', 'status', { unique: false })
        workOrdersStore.createIndex('assignedToId', 'assignedToId', { unique: false })
        workOrdersStore.createIndex('priority', 'priority', { unique: false })
        workOrdersStore.createIndex('scheduledDate', 'scheduledDate', { unique: false })
        workOrdersStore.createIndex('_syncStatus', '_syncStatus', { unique: false })
      }
      
      // Pending Actions store
      if (!db.objectStoreNames.contains(STORES.PENDING_ACTIONS)) {
        const actionsStore = db.createObjectStore(STORES.PENDING_ACTIONS, { keyPath: 'id' })
        actionsStore.createIndex('workOrderId', 'workOrderId', { unique: false })
        actionsStore.createIndex('createdAt', 'createdAt', { unique: false })
        actionsStore.createIndex('actionType', 'actionType', { unique: false })
      }
      
      // Sync Status store
      if (!db.objectStoreNames.contains(STORES.SYNC_STATUS)) {
        db.createObjectStore(STORES.SYNC_STATUS, { keyPath: 'id' })
      }
      
      // User Data store
      if (!db.objectStoreNames.contains(STORES.USER_DATA)) {
        db.createObjectStore(STORES.USER_DATA, { keyPath: 'id' })
      }
    }
  })
  
  return dbPromise
}

export async function closeDatabase(): Promise<void> {
  if (dbInstance) {
    dbInstance.close()
    dbInstance = null
    dbPromise = null
  }
}

// =============================================================================
// GENERIC OPERATIONS
// =============================================================================

async function getStore(
  storeName: string,
  mode: IDBTransactionMode = 'readonly'
): Promise<IDBObjectStore> {
  const db = await openDatabase()
  const transaction = db.transaction(storeName, mode)
  return transaction.objectStore(storeName)
}

export async function get<T>(storeName: string, key: string): Promise<T | undefined> {
  const store = await getStore(storeName)
  return new Promise((resolve, reject) => {
    const request = store.get(key)
    request.onsuccess = () => resolve(request.result as T | undefined)
    request.onerror = () => reject(request.error)
  })
}

export async function getAll<T>(storeName: string): Promise<T[]> {
  const store = await getStore(storeName)
  return new Promise((resolve, reject) => {
    const request = store.getAll()
    request.onsuccess = () => resolve(request.result as T[])
    request.onerror = () => reject(request.error)
  })
}

export async function put<T>(storeName: string, value: T): Promise<void> {
  const store = await getStore(storeName, 'readwrite')
  return new Promise((resolve, reject) => {
    const request = store.put(value)
    request.onsuccess = () => resolve()
    request.onerror = () => reject(request.error)
  })
}

export async function remove(storeName: string, key: string): Promise<void> {
  const store = await getStore(storeName, 'readwrite')
  return new Promise((resolve, reject) => {
    const request = store.delete(key)
    request.onsuccess = () => resolve()
    request.onerror = () => reject(request.error)
  })
}

export async function clear(storeName: string): Promise<void> {
  const store = await getStore(storeName, 'readwrite')
  return new Promise((resolve, reject) => {
    const request = store.clear()
    request.onsuccess = () => resolve()
    request.onerror = () => reject(request.error)
  })
}

export async function getAllByIndex<T>(
  storeName: string,
  indexName: string,
  value: IDBValidKey
): Promise<T[]> {
  const store = await getStore(storeName)
  const index = store.index(indexName)
  return new Promise((resolve, reject) => {
    const request = index.getAll(value)
    request.onsuccess = () => resolve(request.result as T[])
    request.onerror = () => reject(request.error)
  })
}

export async function count(storeName: string): Promise<number> {
  const store = await getStore(storeName)
  return new Promise((resolve, reject) => {
    const request = store.count()
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

// =============================================================================
// WORK ORDER OPERATIONS
// =============================================================================

export async function saveWorkOrder(workOrder: WorkOrder): Promise<void> {
  await put(STORES.WORK_ORDERS, {
    ...workOrder,
    _localUpdatedAt: new Date().toISOString(),
  })
}

export async function saveWorkOrders(workOrders: WorkOrder[]): Promise<void> {
  const db = await openDatabase()
  const transaction = db.transaction(STORES.WORK_ORDERS, 'readwrite')
  const store = transaction.objectStore(STORES.WORK_ORDERS)
  
  const now = new Date().toISOString()
  
  for (const workOrder of workOrders) {
    store.put({
      ...workOrder,
      _localUpdatedAt: now,
      _syncStatus: 'synced',
    })
  }
  
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve()
    transaction.onerror = () => reject(transaction.error)
  })
}

export async function getWorkOrder(id: string): Promise<WorkOrder | undefined> {
  return get<WorkOrder>(STORES.WORK_ORDERS, id)
}

export async function getAllWorkOrders(): Promise<WorkOrder[]> {
  return getAll<WorkOrder>(STORES.WORK_ORDERS)
}

export async function getAssignedWorkOrders(userId: string): Promise<WorkOrder[]> {
  return getAllByIndex<WorkOrder>(STORES.WORK_ORDERS, 'assignedToId', userId)
}

export async function getWorkOrdersByStatus(status: WorkOrderStatus): Promise<WorkOrder[]> {
  return getAllByIndex<WorkOrder>(STORES.WORK_ORDERS, 'status', status)
}

export async function getPendingWorkOrders(): Promise<WorkOrder[]> {
  return getAllByIndex<WorkOrder>(STORES.WORK_ORDERS, '_syncStatus', 'pending')
}

export async function updateWorkOrderLocally(
  id: string,
  updates: Partial<WorkOrder>
): Promise<WorkOrder | undefined> {
  const workOrder = await getWorkOrder(id)
  if (!workOrder) return undefined
  
  const updated = {
    ...workOrder,
    ...updates,
    _localUpdatedAt: new Date().toISOString(),
    _syncStatus: 'pending' as const,
  }
  
  await saveWorkOrder(updated)
  return updated
}

// =============================================================================
// PENDING ACTIONS OPERATIONS
// =============================================================================

export function generateActionId(): string {
  return `action-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
}

export async function addPendingAction(
  workOrderId: string,
  actionType: PendingActionType,
  payload: Record<string, unknown>
): Promise<PendingAction> {
  const action: PendingAction = {
    id: generateActionId(),
    workOrderId,
    actionType,
    payload,
    createdAt: new Date().toISOString(),
    attempts: 0,
    lastAttempt: null,
    error: null,
  }
  
  await put(STORES.PENDING_ACTIONS, action)
  await updateSyncStatus({ pendingCount: await getPendingActionCount() })
  
  return action
}

export async function getPendingAction(id: string): Promise<PendingAction | undefined> {
  return get<PendingAction>(STORES.PENDING_ACTIONS, id)
}

export async function getAllPendingActions(): Promise<PendingAction[]> {
  return getAll<PendingAction>(STORES.PENDING_ACTIONS)
}

export async function getPendingActionsForWorkOrder(workOrderId: string): Promise<PendingAction[]> {
  return getAllByIndex<PendingAction>(STORES.PENDING_ACTIONS, 'workOrderId', workOrderId)
}

export async function getPendingActionCount(): Promise<number> {
  return count(STORES.PENDING_ACTIONS)
}

export async function updatePendingAction(
  id: string,
  updates: Partial<PendingAction>
): Promise<void> {
  const action = await getPendingAction(id)
  if (!action) return
  
  await put(STORES.PENDING_ACTIONS, { ...action, ...updates })
}

export async function removePendingAction(id: string): Promise<void> {
  await remove(STORES.PENDING_ACTIONS, id)
  await updateSyncStatus({ pendingCount: await getPendingActionCount() })
}

export async function clearAllPendingActions(): Promise<void> {
  await clear(STORES.PENDING_ACTIONS)
  await updateSyncStatus({ pendingCount: 0 })
}

// =============================================================================
// SYNC STATUS OPERATIONS
// =============================================================================

const SYNC_STATUS_ID = 'global'

export async function getSyncStatus(): Promise<SyncStatus> {
  const status = await get<SyncStatus>(STORES.SYNC_STATUS, SYNC_STATUS_ID)
  return status || {
    id: SYNC_STATUS_ID,
    lastSyncAt: null,
    pendingCount: 0,
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    lastError: null,
  }
}

export async function updateSyncStatus(updates: Partial<SyncStatus>): Promise<void> {
  const current = await getSyncStatus()
  await put(STORES.SYNC_STATUS, { ...current, ...updates })
}

export async function markSyncComplete(): Promise<void> {
  await updateSyncStatus({
    lastSyncAt: new Date().toISOString(),
    lastError: null,
  })
}

export async function markSyncError(error: string): Promise<void> {
  await updateSyncStatus({
    lastError: error,
  })
}

// =============================================================================
// USER DATA OPERATIONS
// =============================================================================

export interface TechnicianUserData {
  id: string // 'current_user'
  userId: string
  username: string
  role: string
  tenantId: string
  lastLogin: string
}

const USER_DATA_ID = 'current_user'

export async function saveTechnicianData(data: Omit<TechnicianUserData, 'id'>): Promise<void> {
  await put(STORES.USER_DATA, { id: USER_DATA_ID, ...data })
}

export async function getTechnicianData(): Promise<TechnicianUserData | undefined> {
  return get<TechnicianUserData>(STORES.USER_DATA, USER_DATA_ID)
}

export async function clearTechnicianData(): Promise<void> {
  await remove(STORES.USER_DATA, USER_DATA_ID)
}

// =============================================================================
// HIGH-LEVEL OFFLINE OPERATIONS
// =============================================================================

/**
 * Update work order status offline
 */
export async function updateWorkOrderStatusOffline(
  workOrderId: string,
  newStatus: WorkOrderStatus,
  note?: string
): Promise<WorkOrder | undefined> {
  // Update local copy
  const updated = await updateWorkOrderLocally(workOrderId, { status: newStatus })
  
  // Create pending action
  await addPendingAction(workOrderId, 'status_update', {
    newStatus,
    note,
    updatedAt: new Date().toISOString(),
  })
  
  return updated
}

/**
 * Add note to work order offline
 */
export async function addNoteOffline(
  workOrderId: string,
  note: string
): Promise<WorkOrder | undefined> {
  const workOrder = await getWorkOrder(workOrderId)
  if (!workOrder) return undefined
  
  // Update local copy
  const updated = await updateWorkOrderLocally(workOrderId, {
    notes: [...workOrder.notes, note],
  })
  
  // Create pending action
  await addPendingAction(workOrderId, 'add_note', {
    note,
    addedAt: new Date().toISOString(),
  })
  
  return updated
}

/**
 * Add photo to work order offline (base64)
 */
export async function addPhotoOffline(
  workOrderId: string,
  photoBase64: string
): Promise<WorkOrder | undefined> {
  const workOrder = await getWorkOrder(workOrderId)
  if (!workOrder) return undefined
  
  // Update local copy
  const updated = await updateWorkOrderLocally(workOrderId, {
    photos: [...workOrder.photos, photoBase64],
  })
  
  // Create pending action
  await addPendingAction(workOrderId, 'add_photo', {
    photoBase64,
    addedAt: new Date().toISOString(),
  })
  
  return updated
}

/**
 * Update material usage offline
 */
export async function updateMaterialUsageOffline(
  workOrderId: string,
  materialIndex: number,
  usedQuantity: number
): Promise<WorkOrder | undefined> {
  const workOrder = await getWorkOrder(workOrderId)
  if (!workOrder) return undefined
  
  const materials = [...workOrder.materials]
  if (materials[materialIndex]) {
    materials[materialIndex] = {
      ...materials[materialIndex],
      used: usedQuantity,
    }
  }
  
  // Update local copy
  const updated = await updateWorkOrderLocally(workOrderId, { materials })
  
  // Create pending action
  await addPendingAction(workOrderId, 'update_materials', {
    materialIndex,
    usedQuantity,
    updatedAt: new Date().toISOString(),
  })
  
  return updated
}

/**
 * Complete work order offline
 */
export async function completeWorkOrderOffline(
  workOrderId: string,
  actualDuration: number,
  completionNote?: string
): Promise<WorkOrder | undefined> {
  const now = new Date().toISOString()
  
  // Update local copy
  const updated = await updateWorkOrderLocally(workOrderId, {
    status: 'completed',
    actualDuration,
    completedAt: now,
    notes: completionNote 
      ? [...(await getWorkOrder(workOrderId))?.notes || [], completionNote]
      : undefined,
  })
  
  // Create pending action
  await addPendingAction(workOrderId, 'complete_order', {
    actualDuration,
    completionNote,
    completedAt: now,
  })
  
  return updated
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Clear all offline data (for logout)
 */
export async function clearAllOfflineData(): Promise<void> {
  await clear(STORES.WORK_ORDERS)
  await clear(STORES.PENDING_ACTIONS)
  await clear(STORES.USER_DATA)
  await updateSyncStatus({
    lastSyncAt: null,
    pendingCount: 0,
    lastError: null,
  })
}

/**
 * Get offline storage stats
 */
export async function getOfflineStats(): Promise<{
  workOrderCount: number
  pendingActionCount: number
  lastSync: string | null
}> {
  const [workOrderCount, pendingActionCount, syncStatus] = await Promise.all([
    count(STORES.WORK_ORDERS),
    count(STORES.PENDING_ACTIONS),
    getSyncStatus(),
  ])
  
  return {
    workOrderCount,
    pendingActionCount,
    lastSync: syncStatus.lastSyncAt,
  }
}
