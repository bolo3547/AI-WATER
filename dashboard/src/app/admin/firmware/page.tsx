'use client'

import { useState } from 'react'
import { 
  Cpu, Download, Copy, Check, RefreshCw, Wifi, 
  Radio, Droplets, Gauge, Thermometer, Volume2,
  MapPin, Settings, Code, FileCode, Zap
} from 'lucide-react'

type SensorType = 'flow' | 'pressure' | 'acoustic' | 'level' | 'quality'

interface SensorConfig {
  deviceId: string
  deviceName: string
  sensorType: SensorType
  wifiSSID: string
  wifiPassword: string
  apiEndpoint: string
  mqttBroker: string
  mqttPort: number
  mqttTopic: string
  readingInterval: number
  location: {
    lat: number
    lng: number
    dma: string
  }
  calibration: {
    offset: number
    multiplier: number
  }
}

const SENSOR_TYPES = [
  { id: 'flow', name: 'Flow Meter', icon: Droplets, unit: 'm³/h', pin: 'GPIO34' },
  { id: 'pressure', name: 'Pressure Sensor', icon: Gauge, unit: 'bar', pin: 'GPIO35' },
  { id: 'acoustic', name: 'Acoustic Sensor', icon: Volume2, unit: 'dB', pin: 'GPIO32' },
  { id: 'level', name: 'Level Sensor', icon: Thermometer, unit: 'm', pin: 'GPIO33' },
  { id: 'quality', name: 'Water Quality', icon: Droplets, unit: 'NTU', pin: 'GPIO36' },
]

const DEFAULT_CONFIG: SensorConfig = {
  deviceId: '',
  deviceName: '',
  sensorType: 'flow',
  wifiSSID: '',
  wifiPassword: '',
  apiEndpoint: 'http://your-server:8000',
  mqttBroker: 'your-mqtt-broker',
  mqttPort: 1883,
  mqttTopic: 'aquawatch/sensors',
  readingInterval: 30,
  location: { lat: -15.4167, lng: 28.2833, dma: 'DMA-001' },
  calibration: { offset: 0, multiplier: 1.0 }
}

function generateDeviceId(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  let result = 'ESP32-'
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

function generateFirmwareCode(config: SensorConfig): string {
  const sensorTypeInfo = SENSOR_TYPES.find(s => s.id === config.sensorType)
  
  return `/*
 * AquaWatch NRW Detection System
 * ESP32 Sensor Firmware
 * 
 * Device ID: ${config.deviceId}
 * Device Name: ${config.deviceName}
 * Sensor Type: ${sensorTypeInfo?.name || config.sensorType}
 * Generated: ${new Date().toISOString()}
 * 
 * IMPORTANT: Update WiFi credentials before uploading!
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>

// ============== DEVICE CONFIGURATION ==============
const char* DEVICE_ID = "${config.deviceId}";
const char* DEVICE_NAME = "${config.deviceName}";
const char* SENSOR_TYPE = "${config.sensorType}";

// ============== NETWORK CONFIGURATION ==============
const char* WIFI_SSID = "${config.wifiSSID}";
const char* WIFI_PASSWORD = "${config.wifiPassword}";

// ============== API CONFIGURATION ==============
const char* API_ENDPOINT = "${config.apiEndpoint}/api/esp32/data";
const char* API_REGISTER = "${config.apiEndpoint}/api/esp32/register";

// ============== MQTT CONFIGURATION ==============
const char* MQTT_BROKER = "${config.mqttBroker}";
const int MQTT_PORT = ${config.mqttPort};
const char* MQTT_TOPIC = "${config.mqttTopic}/${config.deviceId}";
const char* MQTT_STATUS_TOPIC = "${config.mqttTopic}/status/${config.deviceId}";

// ============== SENSOR CONFIGURATION ==============
const int SENSOR_PIN = ${sensorTypeInfo?.pin || 'GPIO34'};
const int READING_INTERVAL = ${config.readingInterval} * 1000; // milliseconds
const char* SENSOR_UNIT = "${sensorTypeInfo?.unit || 'units'}";

// ============== LOCATION ==============
const float LATITUDE = ${config.location.lat};
const float LONGITUDE = ${config.location.lng};
const char* DMA_ID = "${config.location.dma}";

// ============== CALIBRATION ==============
const float CAL_OFFSET = ${config.calibration.offset};
const float CAL_MULTIPLIER = ${config.calibration.multiplier};

// ============== GLOBALS ==============
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
unsigned long lastReadingTime = 0;
unsigned long lastMqttReconnect = 0;
bool isRegistered = false;
int readingCount = 0;

// ============== LED INDICATORS ==============
const int LED_WIFI = 2;      // Built-in LED for WiFi status
const int LED_STATUS = 4;    // External LED for data status

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println();
  Serial.println("╔══════════════════════════════════════╗");
  Serial.println("║   AquaWatch NRW Detection System     ║");
  Serial.println("║        ESP32 Sensor Module           ║");
  Serial.println("╚══════════════════════════════════════╝");
  Serial.println();
  Serial.print("Device ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Sensor Type: ");
  Serial.println(SENSOR_TYPE);
  
  // Initialize pins
  pinMode(LED_WIFI, OUTPUT);
  pinMode(LED_STATUS, OUTPUT);
  pinMode(SENSOR_PIN, INPUT);
  
  // Blink LEDs on startup
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_WIFI, HIGH);
    digitalWrite(LED_STATUS, HIGH);
    delay(200);
    digitalWrite(LED_WIFI, LOW);
    digitalWrite(LED_STATUS, LOW);
    delay(200);
  }
  
  // Connect to WiFi
  connectWiFi();
  
  // Setup MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  // Register device with server
  registerDevice();
  
  Serial.println("Setup complete. Starting sensor readings...");
  Serial.println();
}

void loop() {
  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LED_WIFI, LOW);
    connectWiFi();
  }
  
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Take sensor readings at interval
  unsigned long currentTime = millis();
  if (currentTime - lastReadingTime >= READING_INTERVAL) {
    lastReadingTime = currentTime;
    takeSensorReading();
  }
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_WIFI, !digitalRead(LED_WIFI));
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("✓ WiFi connected!");
    Serial.print("  IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("  Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
    digitalWrite(LED_WIFI, HIGH);
  } else {
    Serial.println();
    Serial.println("✗ WiFi connection failed!");
    digitalWrite(LED_WIFI, LOW);
  }
}

void reconnectMQTT() {
  unsigned long currentTime = millis();
  if (currentTime - lastMqttReconnect < 5000) return;
  lastMqttReconnect = currentTime;
  
  Serial.print("Connecting to MQTT broker...");
  
  String clientId = "AquaWatch-" + String(DEVICE_ID);
  
  if (mqttClient.connect(clientId.c_str())) {
    Serial.println(" connected!");
    
    // Subscribe to command topic
    String commandTopic = String(MQTT_TOPIC) + "/commands";
    mqttClient.subscribe(commandTopic.c_str());
    
    // Publish online status
    publishStatus("online");
  } else {
    Serial.print(" failed, rc=");
    Serial.println(mqttClient.state());
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("MQTT message received on topic: ");
  Serial.println(topic);
  
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Message: ");
  Serial.println(message);
  
  // Handle commands
  if (message == "restart") {
    Serial.println("Restart command received. Restarting...");
    ESP.restart();
  } else if (message == "status") {
    publishStatus("online");
  } else if (message == "reading") {
    takeSensorReading();
  }
}

void publishStatus(const char* status) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["status"] = status;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["uptime"] = millis() / 1000;
  doc["readings_sent"] = readingCount;
  doc["free_heap"] = ESP.getFreeHeap();
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  mqttClient.publish(MQTT_STATUS_TOPIC, buffer);
}

void registerDevice() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  Serial.println("Registering device with server...");
  
  HTTPClient http;
  http.begin(API_REGISTER);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<512> doc;
  doc["device_id"] = DEVICE_ID;
  doc["device_name"] = DEVICE_NAME;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["firmware_version"] = "2.0.0";
  doc["mac_address"] = WiFi.macAddress();
  doc["ip_address"] = WiFi.localIP().toString();
  
  JsonObject location = doc.createNestedObject("location");
  location["lat"] = LATITUDE;
  location["lng"] = LONGITUDE;
  location["dma_id"] = DMA_ID;
  
  JsonObject capabilities = doc.createNestedObject("capabilities");
  capabilities["mqtt"] = true;
  capabilities["http"] = true;
  capabilities["ota"] = true;
  
  char buffer[512];
  serializeJson(doc, buffer);
  
  int httpCode = http.POST(buffer);
  
  if (httpCode == 200 || httpCode == 201) {
    Serial.println("✓ Device registered successfully!");
    isRegistered = true;
  } else {
    Serial.print("✗ Registration failed. HTTP code: ");
    Serial.println(httpCode);
  }
  
  http.end();
}

float readSensor() {
  // Read analog value
  int rawValue = analogRead(SENSOR_PIN);
  
  // Convert to voltage (ESP32 ADC is 12-bit, 0-4095)
  float voltage = (rawValue / 4095.0) * 3.3;
  
  // Apply calibration
  float calibratedValue = (voltage * CAL_MULTIPLIER) + CAL_OFFSET;
  
  // Sensor-specific conversion
  float finalValue = 0;
  
  if (strcmp(SENSOR_TYPE, "flow") == 0) {
    // Flow meter: voltage to m³/h
    finalValue = calibratedValue * 100.0;
  } else if (strcmp(SENSOR_TYPE, "pressure") == 0) {
    // Pressure sensor: voltage to bar (0.5-4.5V = 0-10 bar typical)
    finalValue = (calibratedValue - 0.5) * 2.5;
  } else if (strcmp(SENSOR_TYPE, "acoustic") == 0) {
    // Acoustic sensor: voltage to dB
    finalValue = calibratedValue * 30.0;
  } else if (strcmp(SENSOR_TYPE, "level") == 0) {
    // Level sensor: voltage to meters
    finalValue = calibratedValue * 5.0;
  } else if (strcmp(SENSOR_TYPE, "quality") == 0) {
    // Water quality: voltage to NTU
    finalValue = calibratedValue * 1000.0;
  } else {
    finalValue = calibratedValue;
  }
  
  return finalValue;
}

void takeSensorReading() {
  float sensorValue = readSensor();
  
  Serial.println("─────────────────────────────────");
  Serial.print("Reading #");
  Serial.println(++readingCount);
  Serial.print("Value: ");
  Serial.print(sensorValue, 2);
  Serial.print(" ");
  Serial.println(SENSOR_UNIT);
  
  // Blink status LED
  digitalWrite(LED_STATUS, HIGH);
  
  // Send via MQTT (primary)
  if (mqttClient.connected()) {
    sendViaMQTT(sensorValue);
  }
  
  // Send via HTTP (backup)
  sendViaHTTP(sensorValue);
  
  digitalWrite(LED_STATUS, LOW);
}

void sendViaMQTT(float value) {
  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["value"] = value;
  doc["unit"] = SENSOR_UNIT;
  doc["timestamp"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  JsonObject loc = doc.createNestedObject("location");
  loc["lat"] = LATITUDE;
  loc["lng"] = LONGITUDE;
  loc["dma_id"] = DMA_ID;
  
  char buffer[384];
  serializeJson(doc, buffer);
  
  if (mqttClient.publish(MQTT_TOPIC, buffer)) {
    Serial.println("✓ MQTT: Data sent");
  } else {
    Serial.println("✗ MQTT: Send failed");
  }
}

void sendViaHTTP(float value) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ HTTP: No WiFi connection");
    return;
  }
  
  HTTPClient http;
  http.begin(API_ENDPOINT);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(10000);
  
  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;
  doc["sensor_type"] = SENSOR_TYPE;
  doc["value"] = value;
  doc["unit"] = SENSOR_UNIT;
  
  JsonObject loc = doc.createNestedObject("location");
  loc["lat"] = LATITUDE;
  loc["lng"] = LONGITUDE;
  loc["dma_id"] = DMA_ID;
  
  JsonObject meta = doc.createNestedObject("metadata");
  meta["wifi_rssi"] = WiFi.RSSI();
  meta["free_heap"] = ESP.getFreeHeap();
  meta["uptime"] = millis() / 1000;
  
  char buffer[384];
  serializeJson(doc, buffer);
  
  int httpCode = http.POST(buffer);
  
  if (httpCode == 200 || httpCode == 201) {
    Serial.println("✓ HTTP: Data sent");
  } else {
    Serial.print("✗ HTTP: Failed, code ");
    Serial.println(httpCode);
  }
  
  http.end();
}
`
}

export default function FirmwareGeneratorPage() {
  const [config, setConfig] = useState<SensorConfig>({
    ...DEFAULT_CONFIG,
    deviceId: generateDeviceId()
  })
  const [generatedCode, setGeneratedCode] = useState<string>('')
  const [copied, setCopied] = useState(false)
  const [showCode, setShowCode] = useState(false)

  const handleGenerateCode = () => {
    const code = generateFirmwareCode(config)
    setGeneratedCode(code)
    setShowCode(true)
  }

  const handleCopyCode = async () => {
    await navigator.clipboard.writeText(generatedCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([generatedCode], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${config.deviceId}_firmware.ino`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleNewDevice = () => {
    setConfig({
      ...DEFAULT_CONFIG,
      deviceId: generateDeviceId()
    })
    setGeneratedCode('')
    setShowCode(false)
  }

  const selectedSensorType = SENSOR_TYPES.find(s => s.id === config.sensorType)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-900 via-purple-900 to-slate-900 p-6 text-white">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
              <Cpu className="w-6 h-6 text-indigo-300" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">ESP32 Firmware Generator</h1>
              <p className="text-slate-400 text-sm">Generate custom Arduino code for AquaWatch sensors</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2">
              <Settings className="w-5 h-5 text-slate-600" />
              Sensor Configuration
            </h2>
          </div>
          
          <div className="p-6 space-y-5">
            {/* Device Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Device ID</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={config.deviceId}
                    onChange={(e) => setConfig({ ...config, deviceId: e.target.value })}
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono bg-slate-50"
                  />
                  <button
                    onClick={() => setConfig({ ...config, deviceId: generateDeviceId() })}
                    className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                    title="Generate new ID"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Device Name</label>
                <input
                  type="text"
                  value={config.deviceName}
                  onChange={(e) => setConfig({ ...config, deviceName: e.target.value })}
                  placeholder="e.g., Main Inlet Flow Meter"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>

            {/* Sensor Type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Sensor Type</label>
              <div className="grid grid-cols-5 gap-2">
                {SENSOR_TYPES.map((type) => {
                  const Icon = type.icon
                  return (
                    <button
                      key={type.id}
                      onClick={() => setConfig({ ...config, sensorType: type.id as SensorType })}
                      className={`p-3 rounded-xl border-2 transition-all flex flex-col items-center gap-1 ${
                        config.sensorType === type.id
                          ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                          : 'border-slate-200 hover:border-slate-300 text-slate-600'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-xs font-medium">{type.name.split(' ')[0]}</span>
                    </button>
                  )
                })}
              </div>
              {selectedSensorType && (
                <p className="text-xs text-slate-500 mt-2">
                  Unit: {selectedSensorType.unit} • Pin: {selectedSensorType.pin}
                </p>
              )}
            </div>

            {/* WiFi Settings */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <Wifi className="w-4 h-4" />
                WiFi Configuration
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">SSID</label>
                  <input
                    type="text"
                    value={config.wifiSSID}
                    onChange={(e) => setConfig({ ...config, wifiSSID: e.target.value })}
                    placeholder="Your WiFi network"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
                  <input
                    type="password"
                    value={config.wifiPassword}
                    onChange={(e) => setConfig({ ...config, wifiPassword: e.target.value })}
                    placeholder="WiFi password"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Server Settings */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <Radio className="w-4 h-4" />
                Server Configuration
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">API Endpoint</label>
                  <input
                    type="text"
                    value={config.apiEndpoint}
                    onChange={(e) => setConfig({ ...config, apiEndpoint: e.target.value })}
                    placeholder="http://your-server:8000"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">MQTT Broker</label>
                    <input
                      type="text"
                      value={config.mqttBroker}
                      onChange={(e) => setConfig({ ...config, mqttBroker: e.target.value })}
                      placeholder="mqtt.example.com"
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">MQTT Port</label>
                    <input
                      type="number"
                      value={config.mqttPort}
                      onChange={(e) => setConfig({ ...config, mqttPort: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                Location
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={config.location.lat}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      location: { ...config.location, lat: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={config.location.lng}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      location: { ...config.location, lng: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">DMA ID</label>
                  <input
                    type="text"
                    value={config.location.dma}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      location: { ...config.location, dma: e.target.value }
                    })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Advanced */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Advanced Settings
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Reading Interval (s)</label>
                  <input
                    type="number"
                    value={config.readingInterval}
                    onChange={(e) => setConfig({ ...config, readingInterval: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Cal. Offset</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.calibration.offset}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      calibration: { ...config.calibration, offset: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Cal. Multiplier</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.calibration.multiplier}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      calibration: { ...config.calibration, multiplier: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Generate Button */}
            <div className="pt-4 flex gap-3">
              <button
                onClick={handleGenerateCode}
                disabled={!config.deviceId || !config.deviceName}
                className="flex-1 px-4 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Code className="w-5 h-5" />
                Generate Firmware Code
              </button>
              <button
                onClick={handleNewDevice}
                className="px-4 py-3 bg-slate-100 text-slate-700 font-medium rounded-xl hover:bg-slate-200 transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Code Preview Panel */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2">
              <FileCode className="w-5 h-5 text-slate-600" />
              Generated Code
            </h2>
            {showCode && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyCode}
                  className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button
                  onClick={handleDownload}
                  className="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4" />
                  Download .ino
                </button>
              </div>
            )}
          </div>
          
          <div className="flex-1 overflow-auto p-4 bg-slate-900">
            {showCode ? (
              <pre className="text-sm font-mono text-slate-300 whitespace-pre-wrap">
                <code>{generatedCode}</code>
              </pre>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <FileCode className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg font-medium">No code generated yet</p>
                <p className="text-sm mt-1">Configure your sensor and click Generate</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-amber-50 rounded-xl border border-amber-200 p-5">
        <h3 className="font-semibold text-amber-900 mb-2">📋 How to use the generated firmware:</h3>
        <ol className="text-sm text-amber-800 space-y-1 list-decimal list-inside">
          <li>Download the generated .ino file or copy the code</li>
          <li>Open Arduino IDE and paste the code into a new sketch</li>
          <li>Install required libraries: <code className="bg-amber-100 px-1 rounded">WiFi</code>, <code className="bg-amber-100 px-1 rounded">HTTPClient</code>, <code className="bg-amber-100 px-1 rounded">ArduinoJson</code>, <code className="bg-amber-100 px-1 rounded">PubSubClient</code></li>
          <li>Select your ESP32 board in Tools → Board</li>
          <li>Connect your ESP32 and select the correct COM port</li>
          <li>Click Upload to flash the firmware</li>
        </ol>
      </div>
    </div>
  )
}
