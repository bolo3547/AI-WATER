import { createClient } from '@supabase/supabase-js'

// Supabase Configuration
// To set up:
// 1. Create free account at https://supabase.com
// 2. Create new project
// 3. Get URL and anon key from Settings > API
// 4. Add to .env.local:
//    NEXT_PUBLIC_SUPABASE_URL=your-project-url
//    NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Check if Supabase is configured
export const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey)

// Create Supabase client (or null if not configured)
export const supabase = isSupabaseConfigured 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null

// Database Types
export interface DBPayment {
  id: string
  account_number: string
  customer_name: string
  amount: number
  method: 'mobile_money' | 'bank_transfer' | 'cash' | 'card'
  reference: string
  dma: string
  status: 'completed' | 'pending' | 'failed'
  created_at: string
}

export interface DBMeter {
  id: string
  account_number: string
  customer_name: string
  dma: string
  address: string
  meter_type: string
  status: 'online' | 'offline' | 'warning' | 'tampered'
  last_reading: number
  last_reading_at: string
  created_at: string
}

export interface DBAlert {
  id: string
  type: 'leak' | 'burst' | 'pressure' | 'quality' | 'tamper'
  severity: 'critical' | 'high' | 'medium' | 'low'
  dma: string
  location: string
  description: string
  status: 'active' | 'acknowledged' | 'resolved'
  created_at: string
  resolved_at?: string
}

export interface DBWorkOrder {
  id: string
  alert_id?: string
  title: string
  description: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'pending' | 'assigned' | 'in_progress' | 'completed'
  assigned_to?: string
  dma: string
  location: string
  created_at: string
  completed_at?: string
}

export interface DBFieldCrew {
  id: string
  name: string
  phone: string
  role: string
  status: 'available' | 'en_route' | 'on_site' | 'break' | 'offline'
  current_task?: string
  lat?: number
  lng?: number
  last_update: string
}

export interface DBSensorReading {
  id: string
  sensor_id: string
  dma: string
  flow_rate: number
  pressure: number
  temperature?: number
  battery?: number
  timestamp: string
}

// Database Operations (with fallback to in-memory)
export const db = {
  // Payments
  payments: {
    async getAll() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('payments')
        .select('*')
        .order('created_at', { ascending: false })
      return error ? [] : data
    },
    
    async create(payment: Omit<DBPayment, 'id' | 'created_at'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('payments')
        .insert(payment)
        .select()
        .single()
      return error ? null : data
    },
    
    async getByDMA(dma: string) {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('payments')
        .select('*')
        .eq('dma', dma)
        .order('created_at', { ascending: false })
      return error ? [] : data
    },
    
    async getTotals() {
      if (!supabase) return { total: 0, count: 0 }
      const { data, error } = await supabase
        .from('payments')
        .select('amount')
        .eq('status', 'completed')
      if (error) return { total: 0, count: 0 }
      const total = data.reduce((sum, p) => sum + p.amount, 0)
      return { total, count: data.length }
    }
  },
  
  // Meters
  meters: {
    async getAll() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('meters')
        .select('*')
        .order('last_reading_at', { ascending: false })
      return error ? [] : data
    },
    
    async create(meter: Omit<DBMeter, 'id' | 'created_at'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('meters')
        .insert(meter)
        .select()
        .single()
      return error ? null : data
    },
    
    async updateReading(id: string, reading: number) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('meters')
        .update({ last_reading: reading, last_reading_at: new Date().toISOString() })
        .eq('id', id)
        .select()
        .single()
      return error ? null : data
    }
  },
  
  // Alerts
  alerts: {
    async getAll() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .order('created_at', { ascending: false })
      return error ? [] : data
    },
    
    async getActive() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .eq('status', 'active')
        .order('severity', { ascending: true })
      return error ? [] : data
    },
    
    async create(alert: Omit<DBAlert, 'id' | 'created_at'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('alerts')
        .insert(alert)
        .select()
        .single()
      return error ? null : data
    },
    
    async resolve(id: string) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('alerts')
        .update({ status: 'resolved', resolved_at: new Date().toISOString() })
        .eq('id', id)
        .select()
        .single()
      return error ? null : data
    }
  },
  
  // Work Orders
  workOrders: {
    async getAll() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('work_orders')
        .select('*')
        .order('created_at', { ascending: false })
      return error ? [] : data
    },
    
    async create(workOrder: Omit<DBWorkOrder, 'id' | 'created_at'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('work_orders')
        .insert(workOrder)
        .select()
        .single()
      return error ? null : data
    },
    
    async updateStatus(id: string, status: DBWorkOrder['status'], assignedTo?: string) {
      if (!supabase) return null
      const update: any = { status }
      if (assignedTo) update.assigned_to = assignedTo
      if (status === 'completed') update.completed_at = new Date().toISOString()
      
      const { data, error } = await supabase
        .from('work_orders')
        .update(update)
        .eq('id', id)
        .select()
        .single()
      return error ? null : data
    }
  },
  
  // Field Crews
  fieldCrews: {
    async getAll() {
      if (!supabase) return []
      const { data, error } = await supabase
        .from('field_crews')
        .select('*')
        .order('name')
      return error ? [] : data
    },
    
    async create(crew: Omit<DBFieldCrew, 'id'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('field_crews')
        .insert(crew)
        .select()
        .single()
      return error ? null : data
    },
    
    async updateStatus(id: string, status: DBFieldCrew['status'], lat?: number, lng?: number) {
      if (!supabase) return null
      const update: any = { status, last_update: new Date().toISOString() }
      if (lat !== undefined) update.lat = lat
      if (lng !== undefined) update.lng = lng
      
      const { data, error } = await supabase
        .from('field_crews')
        .update(update)
        .eq('id', id)
        .select()
        .single()
      return error ? null : data
    }
  },
  
  // Sensor Readings
  sensorReadings: {
    async getLatest(sensorId: string) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('sensor_readings')
        .select('*')
        .eq('sensor_id', sensorId)
        .order('timestamp', { ascending: false })
        .limit(1)
        .single()
      return error ? null : data
    },
    
    async create(reading: Omit<DBSensorReading, 'id'>) {
      if (!supabase) return null
      const { data, error } = await supabase
        .from('sensor_readings')
        .insert(reading)
        .select()
        .single()
      return error ? null : data
    },
    
    async getByDMA(dma: string, hours: number = 24) {
      if (!supabase) return []
      const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()
      const { data, error } = await supabase
        .from('sensor_readings')
        .select('*')
        .eq('dma', dma)
        .gte('timestamp', since)
        .order('timestamp', { ascending: true })
      return error ? [] : data
    }
  }
}

// SQL Schema for Supabase (run in SQL Editor)
export const DATABASE_SCHEMA = `
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  account_number TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  method TEXT NOT NULL CHECK (method IN ('mobile_money', 'bank_transfer', 'cash', 'card')),
  reference TEXT,
  dma TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'pending', 'failed')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meters table
CREATE TABLE IF NOT EXISTS meters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  account_number TEXT UNIQUE NOT NULL,
  customer_name TEXT NOT NULL,
  dma TEXT NOT NULL,
  address TEXT,
  meter_type TEXT DEFAULT 'smart',
  status TEXT DEFAULT 'online' CHECK (status IN ('online', 'offline', 'warning', 'tampered')),
  last_reading DECIMAL(12,2) DEFAULT 0,
  last_reading_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL CHECK (type IN ('leak', 'burst', 'pressure', 'quality', 'tamper')),
  severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
  dma TEXT NOT NULL,
  location TEXT,
  description TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

-- Work Orders table
CREATE TABLE IF NOT EXISTS work_orders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  alert_id UUID REFERENCES alerts(id),
  title TEXT NOT NULL,
  description TEXT,
  priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed')),
  assigned_to UUID REFERENCES field_crews(id),
  dma TEXT NOT NULL,
  location TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Field Crews table
CREATE TABLE IF NOT EXISTS field_crews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  phone TEXT,
  role TEXT,
  status TEXT DEFAULT 'offline' CHECK (status IN ('available', 'en_route', 'on_site', 'break', 'offline')),
  current_task TEXT,
  lat DECIMAL(10,6),
  lng DECIMAL(10,6),
  last_update TIMESTAMPTZ DEFAULT NOW()
);

-- Sensor Readings table (for IoT data)
CREATE TABLE IF NOT EXISTS sensor_readings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  sensor_id TEXT NOT NULL,
  dma TEXT NOT NULL,
  flow_rate DECIMAL(10,2),
  pressure DECIMAL(10,2),
  temperature DECIMAL(5,2),
  battery INTEGER,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_payments_dma ON payments(dma);
CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_dma ON alerts(dma);
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_dma ON sensor_readings(dma);

-- Enable Row Level Security
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE meters ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE field_crews ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_readings ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now - customize for production)
CREATE POLICY "Allow all" ON payments FOR ALL USING (true);
CREATE POLICY "Allow all" ON meters FOR ALL USING (true);
CREATE POLICY "Allow all" ON alerts FOR ALL USING (true);
CREATE POLICY "Allow all" ON work_orders FOR ALL USING (true);
CREATE POLICY "Allow all" ON field_crews FOR ALL USING (true);
CREATE POLICY "Allow all" ON sensor_readings FOR ALL USING (true);
`
