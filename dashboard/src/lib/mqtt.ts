// MQTT Client for Real IoT Sensor Integration
// Connects to AquaWatch sensors deployed in the field
// 
// DEPLOYMENT: Install mqtt package when deploying for real sensor integration:
// npm install mqtt
//
// This module provides a graceful fallback when mqtt is not installed,
// allowing the dashboard to build and run without the mqtt dependency.

import { db } from './supabase'

// MQTT Configuration
const MQTT_CONFIG = {
  brokerUrl: process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883',
  username: process.env.MQTT_USERNAME || '',
  password: process.env.MQTT_PASSWORD || '',
  clientId: `lwsc-dashboard-${Date.now()}`,
  topics: {
    sensors: 'lwsc/sensors/+/data',          // lwsc/sensors/{sensor_id}/data
    alerts: 'lwsc/sensors/+/alert',          // lwsc/sensors/{sensor_id}/alert
    status: 'lwsc/sensors/+/status',         // lwsc/sensors/{sensor_id}/status
    commands: 'lwsc/sensors/+/command'       // lwsc/sensors/{sensor_id}/command (publish)
  }
}

export const isMQTTConfigured = !!process.env.MQTT_BROKER_URL

// Sensor Data Types
export interface SensorData {
  sensorId: string
  dma: string
  timestamp: string
  flowRate: number      // m³/h
  pressure: number      // bar
  temperature?: number  // °C
  battery?: number      // %
  signal?: number       // dBm
  tamperDetected?: boolean
}

export interface SensorAlert {
  sensorId: string
  dma: string
  type: 'leak' | 'burst' | 'low_pressure' | 'high_pressure' | 'tamper' | 'offline'
  severity: 'critical' | 'high' | 'medium' | 'low'
  value?: number
  threshold?: number
  message: string
  timestamp: string
}

export interface SensorStatus {
  sensorId: string
  online: boolean
  battery: number
  signal: number
  lastSeen: string
  firmware: string
}

// Type for the mqtt module (optional dependency)
interface MQTTClientInterface {
  on: (event: string, callback: (...args: unknown[]) => void) => void
  subscribe: (topic: string | string[], callback?: (err: Error | null) => void) => void
  publish: (topic: string, message: string, options?: object, callback?: (err: Error | null) => void) => void
  end: () => void
}

// MQTT Client (for server-side use)
// Note: In Next.js, use this in API routes or server components
export class MQTTSensorClient {
  private client: MQTTClientInterface | null = null
  private reconnectAttempts = 0
  private onDataCallback?: (data: SensorData) => void
  private onAlertCallback?: (alert: SensorAlert) => void
  private onStatusCallback?: (status: SensorStatus) => void

  async connect(): Promise<boolean> {
    if (!isMQTTConfigured) {
      console.log('MQTT not configured. Set MQTT_BROKER_URL environment variable.')
      return false
    }

    // Try to load mqtt package dynamically using eval to bypass TypeScript
    let mqttModule: { connect: (url: string, options: object) => MQTTClientInterface }
    try {
      // eslint-disable-next-line no-eval
      mqttModule = eval("require('mqtt')")
    } catch {
      console.log('MQTT package not installed. Run: npm install mqtt')
      return false
    }

    try {
      this.client = mqttModule.connect(MQTT_CONFIG.brokerUrl, {
        clientId: MQTT_CONFIG.clientId,
        username: MQTT_CONFIG.username || undefined,
        password: MQTT_CONFIG.password || undefined,
        reconnectPeriod: 5000,
        keepalive: 60
      })

      return new Promise((resolve, reject) => {
        this.client!.on('connect', () => {
          console.log('MQTT connected to broker')
          this.reconnectAttempts = 0
          this.subscribeToTopics()
          resolve(true)
        })

        this.client!.on('error', (error: unknown) => {
          console.error('MQTT error:', error)
          reject(error)
        })

        this.client!.on('message', (...args: unknown[]) => {
          const topic = args[0] as string
          const message = args[1] as Buffer
          this.handleMessage(topic, message)
        })
        
        this.client!.on('reconnect', () => {
          this.reconnectAttempts++
          console.log(`MQTT reconnecting... attempt ${this.reconnectAttempts}`)
        })

        this.client!.on('offline', () => {
          console.log('MQTT client offline')
        })
      })
    } catch (error) {
      console.error('Failed to connect to MQTT:', error)
      return false
    }
  }

  private subscribeToTopics() {
    if (!this.client) return

    const topics = [
      MQTT_CONFIG.topics.sensors,
      MQTT_CONFIG.topics.alerts,
      MQTT_CONFIG.topics.status
    ]

    topics.forEach(topic => {
      this.client!.subscribe(topic, (err: Error | null) => {
        if (err) {
          console.error(`Failed to subscribe to ${topic}:`, err)
        } else {
          console.log(`Subscribed to ${topic}`)
        }
      })
    })
  }

  private handleMessage(topic: string, message: Buffer) {
    try {
      const payload = JSON.parse(message.toString())
      const sensorId = topic.split('/')[2] // lwsc/sensors/{sensor_id}/...

      if (topic.includes('/data')) {
        this.handleSensorData({ sensorId, ...payload })
      } else if (topic.includes('/alert')) {
        this.handleSensorAlert({ sensorId, ...payload })
      } else if (topic.includes('/status')) {
        this.handleSensorStatus({ sensorId, ...payload })
      }
    } catch (error) {
      console.error('Failed to parse MQTT message:', error)
    }
  }

  private async handleSensorData(data: SensorData) {
    // Store in database
    await db.sensorReadings.create({
      sensor_id: data.sensorId,
      dma: data.dma,
      flow_rate: data.flowRate,
      pressure: data.pressure,
      temperature: data.temperature,
      battery: data.battery,
      timestamp: data.timestamp || new Date().toISOString()
    })

    // Check for anomalies
    this.checkForAnomalies(data)

    // Notify callback
    this.onDataCallback?.(data)
  }

  private async handleSensorAlert(alert: SensorAlert) {
    // Create alert in database
    await db.alerts.create({
      type: alert.type === 'burst' ? 'burst' : 
            alert.type === 'tamper' ? 'tamper' : 
            alert.type === 'leak' ? 'leak' : 'pressure',
      severity: alert.severity,
      dma: alert.dma,
      location: `Sensor ${alert.sensorId}`,
      description: alert.message,
      status: 'active'
    })

    // Notify callback
    this.onAlertCallback?.(alert)
  }

  private handleSensorStatus(status: SensorStatus) {
    this.onStatusCallback?.(status)
  }

  private checkForAnomalies(data: SensorData) {
    // AI-based anomaly detection thresholds
    const thresholds = {
      minPressure: 1.5,    // bar - below this suggests leak
      maxPressure: 8.0,    // bar - above this is dangerous
      maxFlowVariation: 50 // % change suggests burst
    }

    // Low pressure alert
    if (data.pressure < thresholds.minPressure) {
      this.handleSensorAlert({
        sensorId: data.sensorId,
        dma: data.dma,
        type: 'low_pressure',
        severity: data.pressure < 1.0 ? 'critical' : 'high',
        value: data.pressure,
        threshold: thresholds.minPressure,
        message: `Low pressure detected: ${data.pressure} bar (threshold: ${thresholds.minPressure} bar)`,
        timestamp: new Date().toISOString()
      })
    }

    // High pressure alert
    if (data.pressure > thresholds.maxPressure) {
      this.handleSensorAlert({
        sensorId: data.sensorId,
        dma: data.dma,
        type: 'high_pressure',
        severity: 'critical',
        value: data.pressure,
        threshold: thresholds.maxPressure,
        message: `High pressure detected: ${data.pressure} bar (threshold: ${thresholds.maxPressure} bar)`,
        timestamp: new Date().toISOString()
      })
    }

    // Tamper detection
    if (data.tamperDetected) {
      this.handleSensorAlert({
        sensorId: data.sensorId,
        dma: data.dma,
        type: 'tamper',
        severity: 'critical',
        message: `Tamper detected on sensor ${data.sensorId}`,
        timestamp: new Date().toISOString()
      })
    }
  }

  // Send command to sensor
  sendCommand(sensorId: string, command: string, payload?: object) {
    if (!this.client) {
      console.error('MQTT client not connected')
      return false
    }

    const topic = `lwsc/sensors/${sensorId}/command`
    const message = JSON.stringify({ command, ...payload, timestamp: new Date().toISOString() })

    this.client.publish(topic, message, { qos: 1 }, (err: Error | null) => {
      if (err) {
        console.error(`Failed to send command to ${sensorId}:`, err)
      } else {
        console.log(`Command sent to ${sensorId}: ${command}`)
      }
    })

    return true
  }

  // Set callbacks
  onData(callback: (data: SensorData) => void) {
    this.onDataCallback = callback
  }

  onAlert(callback: (alert: SensorAlert) => void) {
    this.onAlertCallback = callback
  }

  onStatus(callback: (status: SensorStatus) => void) {
    this.onStatusCallback = callback
  }

  disconnect() {
    if (this.client) {
      this.client.end()
      this.client = null
    }
  }
}

// Singleton instance for server-side use
let mqttClient: MQTTSensorClient | null = null

export function getMQTTClient(): MQTTSensorClient {
  if (!mqttClient) {
    mqttClient = new MQTTSensorClient()
  }
  return mqttClient
}

// Simulated sensor data for demo/development
export function generateSimulatedSensorData(sensorId: string, dma: string): SensorData {
  return {
    sensorId,
    dma,
    timestamp: new Date().toISOString(),
    flowRate: 50 + Math.random() * 100,
    pressure: 2.5 + Math.random() * 3,
    temperature: 20 + Math.random() * 10,
    battery: 60 + Math.random() * 40,
    signal: -60 + Math.random() * 30,
    tamperDetected: false
  }
}

// WebSocket bridge for client-side real-time updates
// Use this in API routes to forward MQTT data to browser clients
export interface WebSocketMessage {
  type: 'sensor_data' | 'alert' | 'status'
  payload: SensorData | SensorAlert | SensorStatus
}
