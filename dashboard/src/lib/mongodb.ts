import { MongoClient, Db, Collection } from 'mongodb'

// MongoDB Connection URI - Use environment variable or default to MongoDB Atlas free tier
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb+srv://lwsc:lwsc2026@cluster0.mongodb.net/lwsc_nrw?retryWrites=true&w=majority'
const MONGODB_DB = process.env.MONGODB_DB || 'lwsc_nrw'

if (!MONGODB_URI) {
  throw new Error('Please define the MONGODB_URI environment variable')
}

// Cached connection
let cachedClient: MongoClient | null = null
let cachedDb: Db | null = null

// Global clientPromise for Next.js API routes
let clientPromise: Promise<MongoClient>

if (process.env.NODE_ENV === 'development') {
  // In development, use a global variable to preserve the MongoClient across HMR
  let globalWithMongo = global as typeof globalThis & {
    _mongoClientPromise?: Promise<MongoClient>
  }
  if (!globalWithMongo._mongoClientPromise) {
    const client = new MongoClient(MONGODB_URI)
    globalWithMongo._mongoClientPromise = client.connect()
  }
  clientPromise = globalWithMongo._mongoClientPromise
} else {
  // In production, create a new client
  const client = new MongoClient(MONGODB_URI)
  clientPromise = client.connect()
}

export default clientPromise

export interface WorkOrder {
  _id?: string
  id: string
  title: string
  dma: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in_progress' | 'completed'
  assignee: string
  created_at: string
  due_date: string
  estimated_loss: number
  source: string
  description?: string
  created_by?: string
  completed_at?: string
  completion_notes?: string
}

export interface User {
  _id?: string
  id: string
  username: string
  password: string // hashed
  name: string
  email: string
  role: 'admin' | 'operator' | 'technician'
  department?: string
  phone?: string
  created_at: string
  last_login?: string
  status: 'active' | 'inactive'
}

export interface SensorReading {
  _id?: string
  sensor_id: string
  timestamp: string
  flow_rate: number
  pressure: number
  temperature?: number
  battery_level?: number
  signal_strength?: number
  dma: string
}

export interface Alert {
  _id?: string
  id: string
  type: 'leak' | 'pressure' | 'flow' | 'sensor' | 'system'
  severity: 'critical' | 'warning' | 'info'
  title: string
  message: string
  location?: string
  dma?: string
  sensor_id?: string
  created_at: string
  acknowledged_at?: string
  acknowledged_by?: string
  resolved_at?: string
  resolved_by?: string
  status: 'active' | 'acknowledged' | 'resolved'
}

export interface Message {
  _id?: string
  id: string
  from_user: string
  from_role: string
  to_user: string
  to_role: string
  content: string
  work_order_id?: string
  timestamp: string
  read: boolean
}

export async function connectToDatabase(): Promise<{ client: MongoClient; db: Db }> {
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb }
  }

  const client = new MongoClient(MONGODB_URI)
  await client.connect()
  const db = client.db(MONGODB_DB)

  cachedClient = client
  cachedDb = db

  console.log('[MongoDB] Connected to database:', MONGODB_DB)
  
  return { client, db }
}

// Collection helpers
export async function getWorkOrdersCollection(): Promise<Collection<WorkOrder>> {
  const { db } = await connectToDatabase()
  return db.collection<WorkOrder>('work_orders')
}

export async function getUsersCollection(): Promise<Collection<User>> {
  const { db } = await connectToDatabase()
  return db.collection<User>('users')
}

export async function getSensorReadingsCollection(): Promise<Collection<SensorReading>> {
  const { db } = await connectToDatabase()
  return db.collection<SensorReading>('sensor_readings')
}

export async function getAlertsCollection(): Promise<Collection<Alert>> {
  const { db } = await connectToDatabase()
  return db.collection<Alert>('alerts')
}

export async function getMessagesCollection(): Promise<Collection<Message>> {
  const { db } = await connectToDatabase()
  return db.collection<Message>('messages')
}

// Initialize default data if collections are empty
export async function initializeDatabase() {
  const { db } = await connectToDatabase()
  
  // Check and initialize users
  const usersCollection = db.collection<User>('users')
  const userCount = await usersCollection.countDocuments()
  
  if (userCount === 0) {
    console.log('[MongoDB] Initializing default users...')
    await usersCollection.insertMany([
      {
        id: 'user-admin-001',
        username: 'admin',
        password: '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', // 'admin' hashed
        name: 'System Administrator',
        email: 'admin@lwsc.co.zm',
        role: 'admin',
        department: 'IT',
        phone: '+260 97 1234567',
        created_at: new Date().toISOString(),
        status: 'active'
      },
      {
        id: 'user-operator-001',
        username: 'operator',
        password: 'b17e7f45c319d9cde54c3a0e1eb8c8f8d86f7c5a3e5e4a1a7c8f2e9d0b3a6c5e', // 'operator' hashed
        name: 'Control Room Operator',
        email: 'operator@lwsc.co.zm',
        role: 'operator',
        department: 'Operations',
        phone: '+260 97 2345678',
        created_at: new Date().toISOString(),
        status: 'active'
      },
      {
        id: 'user-tech-001',
        username: 'technician',
        password: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', // 'password' hashed
        name: 'Field Technician',
        email: 'technician@lwsc.co.zm',
        role: 'technician',
        department: 'Maintenance',
        phone: '+260 97 3456789',
        created_at: new Date().toISOString(),
        status: 'active'
      }
    ])
    console.log('[MongoDB] Default users created')
  }
  
  // Check and initialize work orders
  const workOrdersCollection = db.collection<WorkOrder>('work_orders')
  const woCount = await workOrdersCollection.countDocuments()
  
  if (woCount === 0) {
    console.log('[MongoDB] Initializing sample work orders...')
    await workOrdersCollection.insertMany([
      {
        id: 'WO-2026-0001',
        title: 'Investigate suspected main leak - Junction Rd',
        dma: 'Kabulonga North',
        priority: 'high',
        status: 'pending',
        assignee: 'Team Alpha',
        created_at: new Date(Date.now() - 86400000).toISOString(),
        due_date: new Date(Date.now() + 86400000).toISOString(),
        estimated_loss: 280,
        source: 'AI Detection',
        description: 'Major underground leak detected by AI. Estimated loss 280 m³/day.',
        created_by: 'System'
      },
      {
        id: 'WO-2026-0002',
        title: 'Pressure transient investigation - Block C',
        dma: 'Roma Industrial',
        priority: 'medium',
        status: 'pending',
        assignee: 'Unassigned',
        created_at: new Date(Date.now() - 172800000).toISOString(),
        due_date: new Date(Date.now() + 259200000).toISOString(),
        estimated_loss: 135,
        source: 'AI Detection',
        description: 'Pressure anomalies detected in industrial zone.',
        created_by: 'System'
      },
      {
        id: 'WO-2026-0003',
        title: 'Night flow anomaly investigation',
        dma: 'Matero West',
        priority: 'high',
        status: 'in_progress',
        assignee: 'Team Beta',
        created_at: new Date(Date.now() - 43200000).toISOString(),
        due_date: new Date(Date.now() + 172800000).toISOString(),
        estimated_loss: 420,
        source: 'AI Detection',
        description: 'Unusual night flow patterns detected. Possible unauthorized connections.',
        created_by: 'Operator'
      }
    ])
    console.log('[MongoDB] Sample work orders created')
  }
  
  // Check and initialize alerts
  const alertsCollection = db.collection<Alert>('alerts')
  const alertCount = await alertsCollection.countDocuments()
  
  if (alertCount === 0) {
    console.log('[MongoDB] Initializing sample alerts...')
    await alertsCollection.insertMany([
      {
        id: 'alert-001',
        type: 'leak',
        severity: 'critical',
        title: 'Major Leak Detected',
        message: 'AI detected significant pressure drop indicating major leak at Junction Rd',
        location: 'Junction Rd & Main St',
        dma: 'Kabulonga North',
        sensor_id: 'ESP32-001',
        created_at: new Date(Date.now() - 3600000).toISOString(),
        status: 'active'
      },
      {
        id: 'alert-002',
        type: 'pressure',
        severity: 'warning',
        title: 'Low Pressure Alert',
        message: 'Pressure below threshold in Roma Industrial zone',
        location: 'Industrial Zone Block C',
        dma: 'Roma Industrial',
        sensor_id: 'ESP32-008',
        created_at: new Date(Date.now() - 7200000).toISOString(),
        status: 'acknowledged',
        acknowledged_at: new Date(Date.now() - 3600000).toISOString(),
        acknowledged_by: 'Operator'
      }
    ])
    console.log('[MongoDB] Sample alerts created')
  }
  
  console.log('[MongoDB] Database initialization complete')
}
