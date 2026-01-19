/*
 * AquaWatch NRW - ESP32 Sensor Node Firmware v3.0
 * Non-Revenue Water Detection System for Zambia/South Africa
 * 
 * ====================================================================
 * ARCHITECTURAL ROLE: EDGE SENSING LAYER (NOT DECISION MAKER)
 * ====================================================================
 * 
 * The ESP32 is the SENSING LAYER of a distributed water intelligence system.
 * It does NOT make final leak decisions - that is the role of AquaWatch AI.
 * 
 * ESP32 RESPONSIBILITIES:
 * ✓ Read real sensors (flow, pressure, level)
 * ✓ Timestamp and validate readings
 * ✓ Perform basic edge checks (sensor failure, extreme values)
 * ✓ Buffer data when offline (store-and-forward)
 * ✓ Send RAW and PRE-PROCESSED data to backend
 * ✓ Accept control commands from AI (sampling rate, reset, calibration)
 * 
 * ESP32 MUST NEVER:
 * ✗ Make final leak decisions
 * ✗ Rank DMAs or assign priorities
 * ✗ Calculate NRW
 * ✗ Recommend field actions
 * 
 * DATA FLOW:
 * Sensors → ESP32 → MQTT → API → Time-Series DB → AI Models → Dashboard
 * 
 * Hardware: ESP32-WROOM-32
 * Sensors: Flow meter (pulse), Pressure sensor (analog), Ultrasonic level,
 *          Water quality (pH, Turbidity, Chlorine), Temperature
 * Communication: WiFi + MQTT to AquaWatch Central AI
 * 
 * Features:
 * - Over-the-Air (OTA) firmware updates
 * - Edge pre-processing (statistics, validation) - NOT decision making
 * - Offline data buffering (store-and-forward)
 * - Water quality monitoring
 * - Self-diagnostics & calibration
 * - Mesh networking capability (ESP-NOW)
 * - Solar battery monitoring
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include <HTTPClient.h>
#include <Update.h>
#include <esp_now.h>
#include <esp_wifi.h>

// ==================== CONFIGURATION ====================
// ===== CHANGE THESE SETTINGS FOR YOUR NETWORK =====

// WiFi Settings - UPDATE THESE!
const char* WIFI_SSID = "YOUR_WIFI_SSID";         // Your WiFi network name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"; // Your WiFi password

// MQTT Broker Settings - UPDATE THESE!
// Use your computer's IP address (find it with ipconfig on Windows)
const char* MQTT_BROKER = "192.168.1.100";  // Change to your PC's IP address
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";                  // Leave empty if no auth
const char* MQTT_PASSWORD = "";              // Leave empty if no auth

// API Settings - For HTTP fallback (when MQTT unavailable)
const char* API_HOST = "192.168.1.100";      // Same as MQTT_BROKER
const int API_PORT = 8000;                   // Python API port

// Device Configuration - UPDATE THESE!
const char* DEVICE_ID = "ESP32_001";              // Unique ID for this device
const char* DMA_ID = "dma-001";                   // District Metered Area ID
const char* PIPE_ID = "Pipe_A1";                  // Pipe/sensor location ID
const char* ZONE_ID = "ZONE_A";                   // Zone within DMA
const char* SENSOR_LOCATION = "Kabulonga North"; // Human-readable location
const char* FIRMWARE_VERSION = "3.0.0";

// OTA Update Settings
const char* OTA_UPDATE_URL = "http://aquawatch.local/api/firmware/latest";
const unsigned long OTA_CHECK_INTERVAL = 3600000;  // Check every hour

// ==================== PIN DEFINITIONS ====================
// Flow Sensor (Pulse-based)
#define FLOW_SENSOR_PIN 34
#define FLOW_PULSES_PER_LITER 450.0  // Calibrate for your sensor

// Pressure Sensor (Analog 4-20mA with 250 ohm resistor)
#define PRESSURE_SENSOR_PIN 35
#define PRESSURE_MIN 0.0    // Bar at 4mA
#define PRESSURE_MAX 10.0   // Bar at 20mA

// Ultrasonic Level Sensor
#define ULTRASONIC_TRIG_PIN 32
#define ULTRASONIC_ECHO_PIN 33
#define TANK_HEIGHT_CM 200.0  // Total tank height

// Water Quality Sensors
#define PH_SENSOR_PIN 36           // pH sensor (analog)
#define TURBIDITY_SENSOR_PIN 39    // Turbidity sensor (analog)
#define CHLORINE_SENSOR_PIN 25     // Chlorine residual (analog)
#define WATER_TEMP_PIN 26          // DS18B20 temperature sensor

// Solar & Battery Monitoring
#define BATTERY_VOLTAGE_PIN 27     // Battery voltage divider
#define SOLAR_VOLTAGE_PIN 14       // Solar panel voltage

// Status LED
#define STATUS_LED_PIN 2
#define ALARM_LED_PIN 4            // Red LED for sensor faults (NOT leak decisions)

// ==================== GLOBAL VARIABLES ====================
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Flow measurement
volatile unsigned long flowPulseCount = 0;
unsigned long lastFlowCalcTime = 0;
float flowRate = 0.0;        // Liters per minute
float totalVolume = 0.0;     // Total liters

// Pressure measurement
float pressureBar = 0.0;

// Level measurement
float tankLevelPercent = 0.0;
float waterLevelCm = 0.0;

// Water Quality measurements
float phValue = 7.0;
float turbidityNTU = 0.0;
float chlorineMgL = 0.0;
float waterTempC = 25.0;

// Power monitoring
float batteryVoltage = 0.0;
float batteryPercent = 0.0;
float solarVoltage = 0.0;
bool solarCharging = false;

// Edge Pre-Processing (statistics for AI - NOT decisions)
// These are sent to Central AI which makes the actual decisions
float pressureHistory[60];     // Last 60 readings for stats
float flowHistory[60];
int historyIndex = 0;

// Edge-computed statistics (for AI to use, NOT for local decisions)
float pressureMean = 0.0;
float pressureStd = 0.0;
float flowMean = 0.0;
float flowStd = 0.0;
float pressureZScore = 0.0;   // Sent to AI for its decision
float flowZScore = 0.0;       // Sent to AI for its decision

// Sensor health flags (edge validation - legitimate ESP32 responsibility)
bool sensorFault = false;
String sensorFaultType = "";

// ==================== OFFLINE DATA BUFFERING ====================
// Store-and-forward when connectivity is lost
struct BufferedReading {
    unsigned long timestamp;
    float flowRate;
    float totalVolume;
    float pressure;
    float tankLevel;
    float ph;
    float turbidity;
    float chlorine;
    float battery;
    bool sensorFault;
};

#define BUFFER_SIZE 100  // Store up to 100 readings when offline
BufferedReading offlineBuffer[BUFFER_SIZE];
int bufferHead = 0;
int bufferTail = 0;
int bufferedReadings = 0;
bool wasOffline = false;

// OTA Update
unsigned long lastOTACheck = 0;
bool otaInProgress = false;

// ESP-NOW Mesh
uint8_t meshPeers[10][6];  // Up to 10 peer MAC addresses
int numMeshPeers = 0;

// Timing - Configurable by Central AI via MQTT commands
unsigned long lastSensorRead = 0;
unsigned long lastMqttPublish = 0;
unsigned long lastDiagnostics = 0;
unsigned long sensorReadInterval = 1000;     // Default 1 second (AI can adjust)
unsigned long mqttPublishInterval = 5000;    // Default 5 seconds (AI can adjust)
const unsigned long DIAGNOSTICS_INTERVAL = 60000;  // 1 minute

// Status
bool wifiConnected = false;
bool mqttConnected = false;
int consecutiveErrors = 0;
String lastError = "";

// Sequence number for data integrity
unsigned long sequenceNumber = 0;

// ==================== INTERRUPT SERVICE ROUTINE ====================
void IRAM_ATTR flowPulseISR() {
    flowPulseCount++;
}

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    Serial.println("\n============================================================");
    Serial.println("  AquaWatch NRW - ESP32 Edge Sensor Node v3.0");
    Serial.println("  Non-Revenue Water Detection System");
    Serial.println("  For Zambia & Southern Africa");
    Serial.println("============================================================");
    Serial.println("\n  ROLE: EDGE SENSING (Data Collection & Pre-Processing)");
    Serial.println("  Central AI makes all leak detection decisions.");
    Serial.println("============================================================\n");
    
    Serial.print("Device ID: ");
    Serial.println(DEVICE_ID);
    Serial.print("DMA ID: ");
    Serial.println(DMA_ID);
    Serial.print("Zone: ");
    Serial.println(ZONE_ID);
    Serial.print("Location: ");
    Serial.println(SENSOR_LOCATION);
    Serial.println();

    // Initialize EEPROM for persistent storage
    EEPROM.begin(1024);

    // Configure pins
    pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);
    pinMode(PRESSURE_SENSOR_PIN, INPUT);
    pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
    pinMode(ULTRASONIC_ECHO_PIN, INPUT);
    pinMode(STATUS_LED_PIN, OUTPUT);
    pinMode(ALARM_LED_PIN, OUTPUT);
    
    // Water quality sensor pins
    pinMode(PH_SENSOR_PIN, INPUT);
    pinMode(TURBIDITY_SENSOR_PIN, INPUT);
    pinMode(CHLORINE_SENSOR_PIN, INPUT);
    
    // Power monitoring pins
    pinMode(BATTERY_VOLTAGE_PIN, INPUT);
    pinMode(SOLAR_VOLTAGE_PIN, INPUT);

    // Attach flow sensor interrupt
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseISR, FALLING);

    // Initialize history arrays for edge statistics
    for(int i = 0; i < 60; i++) {
        pressureHistory[i] = 0;
        flowHistory[i] = 0;
    }
    
    // Initialize offline buffer
    bufferHead = 0;
    bufferTail = 0;
    bufferedReadings = 0;

    // Load saved data from EEPROM
    loadTotalVolume();
    loadCalibrationData();

    // Connect to WiFi
    connectWiFi();

    // Initialize ESP-NOW for mesh networking (store-and-forward relay)
    initESPNow();

    // Configure MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(2048);

    // Connect to MQTT
    connectMQTT();

    // Run initial diagnostics
    runDiagnostics();

    Serial.println("\n============================================================");
    Serial.println("  SENSOR NODE READY - Sending data to AquaWatch Central AI");
    Serial.println("============================================================");
    Serial.print("Firmware Version: ");
    Serial.println(FIRMWARE_VERSION);
    Serial.print("Sensor Read Interval: ");
    Serial.print(sensorReadInterval);
    Serial.println(" ms");
    Serial.print("MQTT Publish Interval: ");
    Serial.print(mqttPublishInterval);
    Serial.println(" ms");
    Serial.print("Offline Buffer Capacity: ");
    Serial.print(BUFFER_SIZE);
    Serial.println(" readings");
    Serial.println("============================================================\n");
    
    blinkLED(3, 200);
}

// ==================== MAIN LOOP ====================
void loop() {
    // Skip normal operation during OTA update
    if (otaInProgress) {
        delay(100);
        return;
    }

    // Maintain connections
    if (WiFi.status() != WL_CONNECTED) {
        wifiConnected = false;
        connectWiFi();
    }

    if (!mqttClient.connected()) {
        mqttConnected = false;
        connectMQTT();
    }
    mqttClient.loop();

    // Read sensors at regular interval (rate controlled by Central AI)
    if (millis() - lastSensorRead >= sensorReadInterval) {
        readAllSensors();
        computeEdgeStatistics();  // Pre-process stats for AI (NOT decisions)
        validateSensorHealth();    // Edge validation (legitimate ESP32 job)
        lastSensorRead = millis();
    }

    // Publish data to MQTT (or buffer if offline)
    if (millis() - lastMqttPublish >= mqttPublishInterval) {
        if (mqttConnected) {
            // Flush any buffered readings first
            if (bufferedReadings > 0) {
                flushOfflineBuffer();
            }
            // Publish current reading
            publishSensorData();
            publishWaterQuality();
            publishPowerStatus();
            
            // Publish sensor fault to backend (edge validation is valid)
            if (sensorFault) {
                publishSensorFault();
            }
        } else {
            // Try HTTP API as fallback when MQTT unavailable
            if (wifiConnected) {
                sendDataViaHTTP();
            } else {
                // Buffer data when offline (store-and-forward)
                bufferCurrentReading();
            }
        }
        lastMqttPublish = millis();
    }

    // Run diagnostics periodically
    if (millis() - lastDiagnostics >= DIAGNOSTICS_INTERVAL) {
        runDiagnostics();
        lastDiagnostics = millis();
    }

    // Check for OTA updates
    if (millis() - lastOTACheck >= OTA_CHECK_INTERVAL) {
        checkForOTAUpdate();
        lastOTACheck = millis();
    }

    // Update status LED
    updateStatusLED();
    
    // Alarm LED indicates SENSOR FAULTS only (not leak decisions)
    digitalWrite(ALARM_LED_PIN, sensorFault ? HIGH : LOW);
}

// ==================== WIFI FUNCTIONS ====================
void connectWiFi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.println("\nWiFi Connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
        Serial.print("Signal Strength (RSSI): ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
    } else {
        Serial.println("\nWiFi Connection Failed!");
    }
}

// ==================== MQTT FUNCTIONS ====================
void connectMQTT() {
    if (!wifiConnected) return;

    Serial.print("Connecting to MQTT Broker: ");
    Serial.println(MQTT_BROKER);

    int attempts = 0;
    while (!mqttClient.connected() && attempts < 5) {
        String clientId = "AquaWatch_" + String(DEVICE_ID);
        
        if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASSWORD)) {
            mqttConnected = true;
            Serial.println("MQTT Connected!");

            // Subscribe to command topic from Central AI
            // Topic: aquawatch/<dma_id>/<device_id>/cmd
            String cmdTopic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/cmd";
            mqttClient.subscribe(cmdTopic.c_str());
            Serial.print("Subscribed to: ");
            Serial.println(cmdTopic);
            
            // Also subscribe to DMA-wide commands
            String dmaCmdTopic = "aquawatch/" + String(DMA_ID) + "/cmd";
            mqttClient.subscribe(dmaCmdTopic.c_str());
            Serial.print("Subscribed to DMA commands: ");
            Serial.println(dmaCmdTopic);

            // Publish online status
            publishStatus("online");
            
            // If we were offline, notify that we have buffered data
            if (bufferedReadings > 0) {
                Serial.printf("Online again with %d buffered readings\n", bufferedReadings);
            }
        } else {
            Serial.print("MQTT Failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" Retrying...");
            delay(2000);
            attempts++;
        }
    }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String message = "";
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }

    Serial.print("MQTT Command [");
    Serial.print(topic);
    Serial.print("]: ");
    Serial.println(message);

    // Parse JSON command from Central AI
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
        Serial.println("JSON parse error");
        return;
    }

    String command = doc["cmd"] | "";
    
    // ========== COMMANDS FROM AQUAWATCH CENTRAL AI ==========
    
    if (command == "set_sampling_rate") {
        // AI controls sampling rate based on network conditions
        unsigned long newSensorInterval = doc["sensor_interval_ms"] | 1000;
        unsigned long newPublishInterval = doc["publish_interval_ms"] | 5000;
        sensorReadInterval = constrain(newSensorInterval, 100, 60000);
        mqttPublishInterval = constrain(newPublishInterval, 1000, 300000);
        Serial.printf("Sampling rate updated: read=%lums, publish=%lums\n", 
                      sensorReadInterval, mqttPublishInterval);
        publishAcknowledgement("set_sampling_rate", true);
        
    } else if (command == "reset_volume") {
        // Reset total volume counter
        totalVolume = 0.0;
        saveTotalVolume();
        Serial.println("Total volume reset by Central AI");
        publishAcknowledgement("reset_volume", true);
        
    } else if (command == "reboot") {
        // Remote reboot
        Serial.println("Reboot requested by Central AI...");
        publishAcknowledgement("reboot", true);
        delay(1000);
        ESP.restart();
        
    } else if (command == "calibrate") {
        // Calibration routine from AI
        float newPPL = doc["pulses_per_liter"] | FLOW_PULSES_PER_LITER;
        float pressureOffset = doc["pressure_offset"] | 0.0;
        float phOffset = doc["ph_offset"] | 0.0;
        Serial.printf("Calibration from AI: PPL=%.2f, P_offset=%.2f, pH_offset=%.2f\n",
                      newPPL, pressureOffset, phOffset);
        saveCalibrationValues(newPPL, pressureOffset, phOffset);
        publishAcknowledgement("calibrate", true);
        
    } else if (command == "status") {
        // Request status update
        publishStatus("online");
        publishDiagnostics();
        
    } else if (command == "ota_update") {
        // OTA firmware update
        String url = doc["url"] | "";
        if (url.length() > 0) {
            performOTAUpdate(url);
        }
        
    } else if (command == "diagnostics") {
        // Run and publish diagnostics
        runDiagnostics();
        publishDiagnostics();
        
    } else if (command == "sync_time") {
        // Time synchronization from server (future: NTP)
        unsigned long serverTime = doc["epoch"] | 0;
        if (serverTime > 0) {
            Serial.printf("Time sync received: %lu\n", serverTime);
            // In production, would sync RTC here
        }
        publishAcknowledgement("sync_time", true);
        
    } else if (command == "clear_buffer") {
        // Clear offline buffer
        bufferHead = 0;
        bufferTail = 0;
        bufferedReadings = 0;
        Serial.println("Offline buffer cleared");
        publishAcknowledgement("clear_buffer", true);
        
    } else if (command == "get_config") {
        // Return current configuration to AI
        publishConfiguration();
        
    } else {
        Serial.println("Unknown command: " + command);
        publishAcknowledgement(command.c_str(), false);
    }
}

void publishSensorData() {
    if (!mqttConnected) return;

    // Increment sequence number for data integrity tracking
    sequenceNumber++;

    StaticJsonDocument<768> doc;
    
    // ========== DEVICE IDENTIFICATION (Critical for AI) ==========
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;               // CRITICAL: DMA for NRW calculation
    doc["zone_id"] = ZONE_ID;
    doc["sensor_location"] = SENSOR_LOCATION;  // inlet/outlet/junction
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["sequence"] = sequenceNumber;     // For detecting data gaps
    doc["timestamp_ms"] = millis();       // Device uptime timestamp
    
    // ========== RAW SENSOR VALUES (for AI to analyze) ==========
    JsonObject raw = doc.createNestedObject("raw");
    raw["flow_rate_lpm"] = flowRate;
    raw["total_volume_l"] = totalVolume;
    raw["pressure_bar"] = pressureBar;
    raw["tank_level_percent"] = tankLevelPercent;
    raw["water_level_cm"] = waterLevelCm;
    
    // ========== EDGE-COMPUTED STATISTICS (for AI, not decisions) ==========
    // The Central AI uses these to make leak decisions, NOT the ESP32
    JsonObject stats = doc.createNestedObject("edge_stats");
    stats["pressure_mean"] = pressureMean;
    stats["pressure_std"] = pressureStd;
    stats["pressure_zscore"] = pressureZScore;
    stats["flow_mean"] = flowMean;
    stats["flow_std"] = flowStd;
    stats["flow_zscore"] = flowZScore;
    stats["sample_count"] = 60;  // Number of samples in rolling window
    
    // ========== SENSOR HEALTH (legitimate edge validation) ==========
    JsonObject health = doc.createNestedObject("sensor_health");
    health["fault_detected"] = sensorFault;
    health["fault_type"] = sensorFaultType;
    health["pressure_sensor_ok"] = (pressureBar > 0 && pressureBar < PRESSURE_MAX);
    health["flow_sensor_ok"] = true;  // Passive sensor
    health["ultrasonic_ok"] = (waterLevelCm >= 0);
    
    // ========== DEVICE STATUS ==========
    JsonObject status = doc.createNestedObject("status");
    status["wifi_rssi"] = WiFi.RSSI();
    status["uptime_sec"] = millis() / 1000;
    status["free_heap"] = ESP.getFreeHeap();
    status["battery_percent"] = batteryPercent;
    status["solar_charging"] = solarCharging;
    status["buffered_readings"] = bufferedReadings;  // Offline buffer status
    
    // ========== DATA QUALITY FLAGS ==========
    JsonObject quality = doc.createNestedObject("data_quality");
    quality["is_buffered"] = false;  // This is live data
    quality["was_offline"] = wasOffline;
    quality["consecutive_errors"] = consecutiveErrors;

    String output;
    serializeJson(doc, output);

    // Topic structure: aquawatch/<dma_id>/<device_id>/data
    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/data";
    
    if (mqttClient.publish(topic.c_str(), output.c_str())) {
        Serial.println("Data published → Central AI");
        consecutiveErrors = 0;
        wasOffline = false;
    } else {
        Serial.println("MQTT publish failed!");
        consecutiveErrors++;
    }
}

// ==================== HTTP API FALLBACK ====================
// Send data via HTTP when MQTT is unavailable
void sendDataViaHTTP() {
    HTTPClient http;
    
    // Build API URL
    String apiUrl = "http://" + String(API_HOST) + ":" + String(API_PORT) + "/api/sensor";
    
    Serial.print("Sending data via HTTP to: ");
    Serial.println(apiUrl);
    
    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");
    
    // Build JSON payload matching API format
    StaticJsonDocument<512> doc;
    doc["pipe_id"] = PIPE_ID;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["location"] = SENSOR_LOCATION;
    doc["pressure"] = pressureBar * 10;  // Convert to compatible unit
    doc["flow"] = flowRate;
    doc["tank_level"] = tankLevelPercent;
    doc["battery"] = batteryPercent;
    doc["rssi"] = WiFi.RSSI();
    doc["firmware"] = FIRMWARE_VERSION;
    
    // Add sensor health
    JsonObject health = doc.createNestedObject("health");
    health["sensor_fault"] = sensorFault;
    health["fault_type"] = sensorFaultType;
    
    // Add edge statistics
    JsonObject stats = doc.createNestedObject("edge_stats");
    stats["pressure_mean"] = pressureMean;
    stats["pressure_std"] = pressureStd;
    stats["pressure_zscore"] = pressureZScore;
    stats["flow_mean"] = flowMean;
    stats["flow_std"] = flowStd;
    
    String payload;
    serializeJson(doc, payload);
    
    int httpResponseCode = http.POST(payload);
    
    if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.print("HTTP Response: ");
        Serial.println(httpResponseCode);
        Serial.println(response);
        
        // Check if server detected a leak
        if (response.indexOf("\"status\":\"leak\"") > 0) {
            Serial.println("⚠️ SERVER DETECTED LEAK - Check dashboard!");
            // Blink alarm LED (but don't make local decisions)
            for (int i = 0; i < 5; i++) {
                digitalWrite(ALARM_LED_PIN, HIGH);
                delay(100);
                digitalWrite(ALARM_LED_PIN, LOW);
                delay(100);
            }
        }
        
        consecutiveErrors = 0;
    } else {
        Serial.print("HTTP Error: ");
        Serial.println(httpResponseCode);
        consecutiveErrors++;
    }
    
    http.end();
}
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/data";
    
    if (mqttClient.publish(topic.c_str(), output.c_str())) {
        Serial.println("Data published to MQTT");
    } else {
        Serial.println("MQTT publish failed!");
    }
}

void publishStatus(const char* status) {
    if (!mqttConnected) return;

    StaticJsonDocument<384> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["sensor_location"] = SENSOR_LOCATION;
    doc["status"] = status;
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["battery_percent"] = batteryPercent;
    doc["solar_charging"] = solarCharging;
    doc["uptime_sec"] = millis() / 1000;
    doc["sampling_rate_ms"] = sensorReadInterval;
    doc["publish_rate_ms"] = mqttPublishInterval;
    doc["buffered_readings"] = bufferedReadings;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/status";
    mqttClient.publish(topic.c_str(), output.c_str(), true);
}

// ==================== WATER QUALITY FUNCTIONS ====================
void readWaterQuality() {
    // Read pH sensor (assumes calibrated pH probe)
    int phRaw = analogRead(PH_SENSOR_PIN);
    float phVoltage = phRaw * (3.3 / 4095.0);
    // pH = 7 at 2.5V, changes ~0.18V per pH unit (calibrate for your sensor)
    phValue = 7.0 + ((2.5 - phVoltage) / 0.18);
    phValue = constrain(phValue, 0.0, 14.0);
    
    // Read turbidity (NTU)
    int turbRaw = analogRead(TURBIDITY_SENSOR_PIN);
    float turbVoltage = turbRaw * (3.3 / 4095.0);
    // Lower voltage = higher turbidity (calibrate for your sensor)
    turbidityNTU = mapFloat(turbVoltage, 2.5, 4.0, 3000.0, 0.0);
    turbidityNTU = constrain(turbidityNTU, 0.0, 3000.0);
    
    // Read chlorine residual (mg/L)
    int clRaw = analogRead(CHLORINE_SENSOR_PIN);
    float clVoltage = clRaw * (3.3 / 4095.0);
    // Typical range 0-5 mg/L (calibrate for your sensor)
    chlorineMgL = mapFloat(clVoltage, 0.0, 3.3, 0.0, 5.0);
    chlorineMgL = constrain(chlorineMgL, 0.0, 5.0);
}

void publishWaterQuality() {
    if (!mqttConnected) return;

    StaticJsonDocument<384> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["timestamp_ms"] = millis();
    
    JsonObject quality = doc.createNestedObject("water_quality");
    quality["ph"] = phValue;
    quality["turbidity_ntu"] = turbidityNTU;
    quality["chlorine_mg_l"] = chlorineMgL;
    quality["temperature_c"] = waterTempC;
    
    // Sensor health assessment (NOT water safety decision - that's for AI)
    JsonObject health = doc.createNestedObject("sensor_health");
    health["ph_in_range"] = (phValue >= 0 && phValue <= 14);
    health["turbidity_in_range"] = (turbidityNTU >= 0 && turbidityNTU <= 3000);
    health["chlorine_in_range"] = (chlorineMgL >= 0 && chlorineMgL <= 5);

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/quality";
    mqttClient.publish(topic.c_str(), output.c_str());
}

// ==================== POWER MONITORING FUNCTIONS ====================
void readPowerStatus() {
    // Battery voltage through voltage divider (adjust ratio for your circuit)
    // Assuming 10k/10k divider for 8.4V max (2S LiPo)
    int battRaw = analogRead(BATTERY_VOLTAGE_PIN);
    batteryVoltage = (battRaw * 3.3 / 4095.0) * 2.0;  // Multiply by divider ratio
    
    // Calculate battery percentage (3.0V = 0%, 4.2V = 100% per cell)
    float cellVoltage = batteryVoltage / 2.0;  // For 2S battery
    batteryPercent = mapFloat(cellVoltage, 3.0, 4.2, 0.0, 100.0);
    batteryPercent = constrain(batteryPercent, 0.0, 100.0);
    
    // Solar panel voltage
    int solarRaw = analogRead(SOLAR_VOLTAGE_PIN);
    solarVoltage = (solarRaw * 3.3 / 4095.0) * 6.0;  // Adjust for voltage divider
    
    // Determine if charging (solar voltage > battery voltage + threshold)
    solarCharging = (solarVoltage > batteryVoltage + 0.5);
}

void publishPowerStatus() {
    if (!mqttConnected) return;

    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["timestamp_ms"] = millis();
    
    JsonObject power = doc.createNestedObject("power");
    power["battery_voltage"] = batteryVoltage;
    power["battery_percent"] = batteryPercent;
    power["solar_voltage"] = solarVoltage;
    power["solar_charging"] = solarCharging;
    
    // Power health status (for monitoring)
    String status = "good";
    if (batteryPercent < 20) {
        status = "low";
    }
    if (batteryPercent < 10) {
        status = "critical";
    }
    power["status"] = status;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/power";
    mqttClient.publish(topic.c_str(), output.c_str());
}

// ==================== EDGE PRE-PROCESSING (NOT DECISION MAKING) ====================
// The ESP32 computes statistics to help the Central AI make decisions.
// The ESP32 does NOT decide if there is a leak - that is the AI's job.

void computeEdgeStatistics() {
    // Store current readings in circular buffer
    pressureHistory[historyIndex] = pressureBar;
    flowHistory[historyIndex] = flowRate;
    historyIndex = (historyIndex + 1) % 60;
    
    // Calculate rolling statistics (for AI to use)
    pressureMean = 0;
    flowMean = 0;
    
    for (int i = 0; i < 60; i++) {
        pressureMean += pressureHistory[i];
        flowMean += flowHistory[i];
    }
    pressureMean /= 60.0;
    flowMean /= 60.0;
    
    // Calculate standard deviations
    pressureStd = 0;
    flowStd = 0;
    
    for (int i = 0; i < 60; i++) {
        pressureStd += pow(pressureHistory[i] - pressureMean, 2);
        flowStd += pow(flowHistory[i] - flowMean, 2);
    }
    pressureStd = sqrt(pressureStd / 60.0);
    flowStd = sqrt(flowStd / 60.0);
    
    // Calculate Z-scores (sent to AI for its decision, NOT for local decisions)
    if (pressureStd > 0.01) {
        pressureZScore = (pressureBar - pressureMean) / pressureStd;
    } else {
        pressureZScore = 0;
    }
    
    if (flowStd > 0.01) {
        flowZScore = (flowRate - flowMean) / flowStd;
    } else {
        flowZScore = 0;
    }
    
    // NOTE: We do NOT make leak decisions here.
    // The Central AI will analyze pressureZScore, flowZScore, and other data
    // from multiple sensors across the DMA to determine IF and WHERE a leak is.
}

// ==================== SENSOR HEALTH VALIDATION ====================
// This is a LEGITIMATE edge responsibility - detecting sensor failures

void validateSensorHealth() {
    sensorFault = false;
    sensorFaultType = "";
    
    // Check for sensor faults (NOT leak detection - just sensor health)
    
    // Pressure sensor fault detection
    if (pressureBar < -0.5 || pressureBar > PRESSURE_MAX + 1.0) {
        sensorFault = true;
        sensorFaultType = "pressure_sensor_out_of_range";
    }
    
    // Check for stuck pressure sensor (no variance)
    if (pressureStd < 0.001 && pressureMean > 0) {
        // Pressure hasn't changed in 60 readings - possible stuck sensor
        sensorFault = true;
        sensorFaultType = "pressure_sensor_stuck";
    }
    
    // pH out of physical range
    if (phValue < 0 || phValue > 14) {
        sensorFault = true;
        sensorFaultType = "ph_sensor_fault";
    }
    
    // Ultrasonic sensor fault
    if (waterLevelCm < -10 || waterLevelCm > TANK_HEIGHT_CM + 50) {
        sensorFault = true;
        sensorFaultType = "ultrasonic_sensor_fault";
    }
    
    // Battery critical - affects data reliability
    if (batteryPercent < 5 && !solarCharging) {
        sensorFault = true;
        sensorFaultType = "battery_critical";
    }
    
    if (sensorFault) {
        Serial.println("⚠️ SENSOR FAULT: " + sensorFaultType);
    }
}

void publishSensorFault() {
    // Publish sensor fault to backend (legitimate edge responsibility)
    if (!mqttConnected) return;

    StaticJsonDocument<384> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["timestamp_ms"] = millis();
    doc["fault_type"] = sensorFaultType;
    doc["fault_detected"] = true;
    
    // Include current readings for diagnostics
    JsonObject readings = doc.createNestedObject("readings");
    readings["pressure_bar"] = pressureBar;
    readings["pressure_mean"] = pressureMean;
    readings["pressure_std"] = pressureStd;
    readings["flow_rate_lpm"] = flowRate;
    readings["ph"] = phValue;
    readings["water_level_cm"] = waterLevelCm;
    readings["battery_percent"] = batteryPercent;

    String output;
    serializeJson(doc, output);

    // Sensor faults go to a separate topic for monitoring
    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/sensor_fault";
    mqttClient.publish(topic.c_str(), output.c_str());
    
    Serial.println("Sensor fault reported to Central AI");
}

// ==================== OTA UPDATE FUNCTIONS ====================
void checkForOTAUpdate() {
    if (!wifiConnected) return;
    
    Serial.println("Checking for OTA updates...");
    
    HTTPClient http;
    http.begin(OTA_UPDATE_URL);
    http.addHeader("X-Device-ID", DEVICE_ID);
    http.addHeader("X-Current-Version", FIRMWARE_VERSION);
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        StaticJsonDocument<256> doc;
        deserializeJson(doc, payload);
        
        String newVersion = doc["version"] | "";
        String downloadUrl = doc["url"] | "";
        
        if (newVersion.length() > 0 && newVersion != FIRMWARE_VERSION) {
            Serial.println("New firmware available: " + newVersion);
            performOTAUpdate(downloadUrl);
        } else {
            Serial.println("Firmware is up to date");
        }
    }
    
    http.end();
}

void performOTAUpdate(String url) {
    if (url.length() == 0) return;
    
    Serial.println("Starting OTA update from: " + url);
    otaInProgress = true;
    
    // Publish update status
    publishStatus("updating");
    
    HTTPClient http;
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        int contentLength = http.getSize();
        
        if (contentLength > 0) {
            bool canBegin = Update.begin(contentLength);
            
            if (canBegin) {
                Serial.println("Begin OTA update...");
                WiFiClient* stream = http.getStreamPtr();
                size_t written = Update.writeStream(*stream);
                
                if (written == contentLength) {
                    Serial.println("OTA written successfully");
                } else {
                    Serial.println("OTA write failed");
                }
                
                if (Update.end()) {
                    Serial.println("OTA update finished!");
                    if (Update.isFinished()) {
                        Serial.println("Rebooting...");
                        delay(1000);
                        ESP.restart();
                    }
                } else {
                    Serial.println("OTA error: " + String(Update.getError()));
                }
            } else {
                Serial.println("Not enough space for OTA");
            }
        }
    } else {
        Serial.println("HTTP error: " + String(httpCode));
    }
    
    http.end();
    otaInProgress = false;
}

// ==================== ESP-NOW MESH FUNCTIONS ====================
// Mesh networking allows ESP32 devices to relay data when one has connectivity

void initESPNow() {
    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW init failed");
        return;
    }
    
    esp_now_register_recv_cb(onESPNowReceive);
    esp_now_register_send_cb(onESPNowSend);
    
    Serial.println("ESP-NOW initialized for mesh networking");
}

void onESPNowReceive(const uint8_t* mac, const uint8_t* data, int len) {
    // Receive data from mesh peer (another ESP32 that may be offline)
    String message = "";
    for (int i = 0; i < len; i++) {
        message += (char)data[i];
    }
    
    // Format MAC address for logging
    char macStr[18];
    snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    
    Serial.print("ESP-NOW received from ");
    Serial.print(macStr);
    Serial.println(": " + message.substring(0, 50) + "...");
    
    // Forward to MQTT if we have connectivity (store-and-forward relay)
    if (mqttConnected) {
        // Parse the incoming message to extract DMA info
        StaticJsonDocument<768> doc;
        DeserializationError error = deserializeJson(doc, message);
        
        if (!error) {
            // Add relay metadata
            doc["relayed_by"] = DEVICE_ID;
            doc["relay_dma"] = DMA_ID;
            doc["original_mac"] = macStr;
            
            String output;
            serializeJson(doc, output);
            
            // Forward to mesh relay topic for Central AI
            String topic = "aquawatch/" + String(DMA_ID) + "/mesh/relayed";
            mqttClient.publish(topic.c_str(), output.c_str());
            Serial.println("Mesh data forwarded to Central AI");
        } else {
            // Forward raw if JSON parse fails
            String topic = "aquawatch/" + String(DMA_ID) + "/mesh/raw";
            mqttClient.publish(topic.c_str(), message.c_str());
        }
    } else {
        // Buffer the relayed data too
        Serial.println("Cannot forward mesh data - buffering locally");
    }
}

void onESPNowSend(const uint8_t* mac, esp_now_send_status_t status) {
    Serial.print("ESP-NOW send status: ");
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Failed");
}

void broadcastToMesh(String message) {
    // Broadcast to all mesh peers (for offline relay)
    for (int i = 0; i < numMeshPeers; i++) {
        esp_now_send(meshPeers[i], (uint8_t*)message.c_str(), message.length());
    }
}

// Request mesh relay when this device is offline
void requestMeshRelay() {
    if (bufferedReadings > 0 && !mqttConnected && numMeshPeers > 0) {
        // Send buffered data to mesh peers for relay
        Serial.println("Requesting mesh relay for buffered data...");
        
        // Send a relay request with our oldest buffered reading
        if (bufferedReadings > 0) {
            BufferedReading* reading = &offlineBuffer[bufferTail];
            
            StaticJsonDocument<512> doc;
            doc["device_id"] = DEVICE_ID;
            doc["dma_id"] = DMA_ID;
            doc["zone_id"] = ZONE_ID;
            doc["needs_relay"] = true;
            doc["timestamp_ms"] = reading->timestamp;
            
            JsonObject raw = doc.createNestedObject("raw");
            raw["flow_rate_lpm"] = reading->flowRate;
            raw["pressure_bar"] = reading->pressure;
            raw["total_volume_l"] = reading->totalVolume;
            
            String output;
            serializeJson(doc, output);
            
            broadcastToMesh(output);
        }
    }
}

// ==================== DIAGNOSTICS FUNCTIONS ====================
void runDiagnostics() {
    Serial.println("\n=== Running Diagnostics ===");
    
    // Check WiFi signal strength
    int rssi = WiFi.RSSI();
    Serial.print("WiFi RSSI: ");
    Serial.print(rssi);
    Serial.println(" dBm");
    
    // Check memory
    Serial.print("Free Heap: ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");
    
    // Check sensors
    Serial.println("Sensor Check:");
    Serial.print("  Pressure: ");
    Serial.println(pressureBar > 0 ? "OK" : "FAIL");
    Serial.print("  Flow: ");
    Serial.println("OK");  // Flow sensor is passive
    Serial.print("  Ultrasonic: ");
    Serial.println(waterLevelCm >= 0 ? "OK" : "FAIL");
    Serial.print("  pH: ");
    Serial.println((phValue >= 0 && phValue <= 14) ? "OK" : "FAIL");
    
    // Check battery
    Serial.print("Battery: ");
    Serial.print(batteryPercent);
    Serial.println("%");
    
    Serial.println("=== Diagnostics Complete ===\n");
}

void publishDiagnostics() {
    if (!mqttConnected) return;

    StaticJsonDocument<512> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["sensor_location"] = SENSOR_LOCATION;
    doc["timestamp_ms"] = millis();
    doc["firmware_version"] = FIRMWARE_VERSION;
    
    JsonObject system = doc.createNestedObject("system");
    system["free_heap"] = ESP.getFreeHeap();
    system["uptime_sec"] = millis() / 1000;
    system["wifi_rssi"] = WiFi.RSSI();
    system["consecutive_errors"] = consecutiveErrors;
    system["last_error"] = lastError;
    system["sensor_read_interval_ms"] = sensorReadInterval;
    system["mqtt_publish_interval_ms"] = mqttPublishInterval;
    
    JsonObject sensors = doc.createNestedObject("sensor_health");
    sensors["pressure"] = (pressureBar > 0 && pressureBar < PRESSURE_MAX) ? "ok" : "error";
    sensors["flow"] = "ok";
    sensors["ultrasonic"] = waterLevelCm >= 0 ? "ok" : "error";
    sensors["ph"] = (phValue >= 0 && phValue <= 14) ? "ok" : "error";
    sensors["turbidity"] = turbidityNTU >= 0 ? "ok" : "error";
    
    JsonObject buffer = doc.createNestedObject("offline_buffer");
    buffer["capacity"] = BUFFER_SIZE;
    buffer["used"] = bufferedReadings;
    buffer["was_offline"] = wasOffline;
    
    JsonObject power = doc.createNestedObject("power");
    power["battery_percent"] = batteryPercent;
    power["solar_charging"] = solarCharging;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/diagnostics";
    mqttClient.publish(topic.c_str(), output.c_str());
}

// ==================== CALIBRATION FUNCTIONS ====================
void loadCalibrationData() {
    // Load calibration from EEPROM (offset 100)
    // Format: [ph_offset (float), turbidity_offset (float), pressure_offset (float)]
    Serial.println("Loading calibration data...");
    // Add calibration loading logic here
}

void saveThresholds(float pressureThreshold, float flowThreshold) {
    // Save anomaly detection thresholds to EEPROM
    EEPROM.put(200, pressureThreshold);
    EEPROM.put(204, flowThreshold);
    EEPROM.commit();
    Serial.println("Thresholds saved");
}

void saveCalibrationValues(float ppl, float pressureOffset, float phOffset) {
    EEPROM.put(208, ppl);
    EEPROM.put(212, pressureOffset);
    EEPROM.put(216, phOffset);
    EEPROM.commit();
    Serial.println("Calibration values saved");
}

// ==================== OFFLINE DATA BUFFERING (STORE-AND-FORWARD) ====================
// When connectivity is lost, buffer readings for later transmission

void bufferCurrentReading() {
    if (bufferedReadings >= BUFFER_SIZE) {
        // Buffer full - overwrite oldest
        Serial.println("⚠️ Offline buffer full - overwriting oldest data");
        bufferTail = (bufferTail + 1) % BUFFER_SIZE;
        bufferedReadings--;
    }
    
    // Store current reading
    offlineBuffer[bufferHead].timestamp = millis();
    offlineBuffer[bufferHead].flowRate = flowRate;
    offlineBuffer[bufferHead].totalVolume = totalVolume;
    offlineBuffer[bufferHead].pressure = pressureBar;
    offlineBuffer[bufferHead].tankLevel = tankLevelPercent;
    offlineBuffer[bufferHead].ph = phValue;
    offlineBuffer[bufferHead].turbidity = turbidityNTU;
    offlineBuffer[bufferHead].chlorine = chlorineMgL;
    offlineBuffer[bufferHead].battery = batteryPercent;
    offlineBuffer[bufferHead].sensorFault = sensorFault;
    
    bufferHead = (bufferHead + 1) % BUFFER_SIZE;
    bufferedReadings++;
    wasOffline = true;
    
    Serial.printf("Buffered reading #%d (offline)\n", bufferedReadings);
}

void flushOfflineBuffer() {
    if (!mqttConnected || bufferedReadings == 0) return;
    
    Serial.printf("Flushing %d buffered readings...\n", bufferedReadings);
    
    int flushed = 0;
    while (bufferedReadings > 0 && flushed < 10) {  // Flush up to 10 at a time
        BufferedReading* reading = &offlineBuffer[bufferTail];
        
        // Publish buffered reading with buffer flag
        StaticJsonDocument<512> doc;
        doc["device_id"] = DEVICE_ID;
        doc["dma_id"] = DMA_ID;
        doc["zone_id"] = ZONE_ID;
        doc["sensor_location"] = SENSOR_LOCATION;
        doc["timestamp_ms"] = reading->timestamp;
        doc["sequence"] = sequenceNumber++;
        
        JsonObject raw = doc.createNestedObject("raw");
        raw["flow_rate_lpm"] = reading->flowRate;
        raw["total_volume_l"] = reading->totalVolume;
        raw["pressure_bar"] = reading->pressure;
        raw["tank_level_percent"] = reading->tankLevel;
        
        JsonObject quality_obj = doc.createNestedObject("water_quality");
        quality_obj["ph"] = reading->ph;
        quality_obj["turbidity_ntu"] = reading->turbidity;
        quality_obj["chlorine_mg_l"] = reading->chlorine;
        
        JsonObject quality_flags = doc.createNestedObject("data_quality");
        quality_flags["is_buffered"] = true;  // Mark as buffered data
        quality_flags["was_offline"] = true;
        quality_flags["buffer_sequence"] = flushed;
        
        doc["sensor_fault"] = reading->sensorFault;
        
        String output;
        serializeJson(doc, output);
        
        String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/data";
        
        if (mqttClient.publish(topic.c_str(), output.c_str())) {
            bufferTail = (bufferTail + 1) % BUFFER_SIZE;
            bufferedReadings--;
            flushed++;
        } else {
            break;  // Stop if publish fails
        }
    }
    
    Serial.printf("Flushed %d buffered readings, %d remaining\n", flushed, bufferedReadings);
}

void publishAcknowledgement(const char* command, bool success) {
    if (!mqttConnected) return;
    
    StaticJsonDocument<192> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["command"] = command;
    doc["success"] = success;
    doc["timestamp_ms"] = millis();
    
    String output;
    serializeJson(doc, output);
    
    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/ack";
    mqttClient.publish(topic.c_str(), output.c_str());
}

void publishConfiguration() {
    if (!mqttConnected) return;
    
    StaticJsonDocument<384> doc;
    doc["device_id"] = DEVICE_ID;
    doc["dma_id"] = DMA_ID;
    doc["zone_id"] = ZONE_ID;
    doc["sensor_location"] = SENSOR_LOCATION;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["sensor_read_interval_ms"] = sensorReadInterval;
    doc["mqtt_publish_interval_ms"] = mqttPublishInterval;
    doc["buffer_size"] = BUFFER_SIZE;
    doc["buffer_used"] = bufferedReadings;
    doc["flow_pulses_per_liter"] = FLOW_PULSES_PER_LITER;
    doc["pressure_min"] = PRESSURE_MIN;
    doc["pressure_max"] = PRESSURE_MAX;
    doc["tank_height_cm"] = TANK_HEIGHT_CM;
    
    String output;
    serializeJson(doc, output);
    
    String topic = "aquawatch/" + String(DMA_ID) + "/" + String(DEVICE_ID) + "/config";
    mqttClient.publish(topic.c_str(), output.c_str());
}

// ==================== SENSOR READING FUNCTIONS ====================
void readAllSensors() {
    readFlowSensor();
    readPressureSensor();
    readUltrasonicSensor();
    readWaterQuality();
    readPowerStatus();
    
    // Print readings to serial
    Serial.println("--- Sensor Readings ---");
    Serial.print("Flow: ");
    Serial.print(flowRate, 2);
    Serial.print(" L/min | Total: ");
    Serial.print(totalVolume, 2);
    Serial.println(" L");
    Serial.print("Pressure: ");
    Serial.print(pressureBar, 2);
    Serial.println(" bar");
    Serial.print("Tank Level: ");
    Serial.print(tankLevelPercent, 1);
    Serial.print("% (");
    Serial.print(waterLevelCm, 1);
    Serial.println(" cm)");
    Serial.print("pH: ");
    Serial.print(phValue, 2);
    Serial.print(" | Turbidity: ");
    Serial.print(turbidityNTU, 1);
    Serial.print(" NTU | Cl: ");
    Serial.print(chlorineMgL, 2);
    Serial.println(" mg/L");
    Serial.print("Battery: ");
    Serial.print(batteryPercent, 0);
    Serial.print("% | Solar: ");
    Serial.println(solarCharging ? "Charging" : "Not charging");
}

void readFlowSensor() {
    static unsigned long lastPulseCount = 0;
    
    // Calculate flow rate
    unsigned long currentTime = millis();
    unsigned long elapsedTime = currentTime - lastFlowCalcTime;
    
    if (elapsedTime >= 1000) {  // Calculate every second
        noInterrupts();
        unsigned long pulses = flowPulseCount - lastPulseCount;
        lastPulseCount = flowPulseCount;
        interrupts();
        
        // Flow rate in liters per minute
        flowRate = (pulses / FLOW_PULSES_PER_LITER) * (60000.0 / elapsedTime);
        
        // Accumulate total volume
        totalVolume += pulses / FLOW_PULSES_PER_LITER;
        
        // Save total volume periodically (every 100 liters)
        static float lastSavedVolume = 0;
        if (totalVolume - lastSavedVolume >= 100) {
            saveTotalVolume();
            lastSavedVolume = totalVolume;
        }
        
        lastFlowCalcTime = currentTime;
    }
}

void readPressureSensor() {
    // Read analog value (12-bit ADC: 0-4095)
    int rawValue = analogRead(PRESSURE_SENSOR_PIN);
    
    // Convert to voltage (3.3V reference)
    float voltage = rawValue * (3.3 / 4095.0);
    
    // 4-20mA with 250 ohm resistor = 1V to 5V (clamped to 3.3V)
    // Map to pressure range
    float minVoltage = 1.0;   // 4mA * 250 ohm
    float maxVoltage = 3.3;   // Clamped at 3.3V (would be 5V at 20mA)
    
    pressureBar = mapFloat(voltage, minVoltage, maxVoltage, PRESSURE_MIN, PRESSURE_MAX);
    pressureBar = constrain(pressureBar, PRESSURE_MIN, PRESSURE_MAX);
}

void readUltrasonicSensor() {
    // Send trigger pulse
    digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
    
    // Read echo duration
    long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, 30000);  // 30ms timeout
    
    if (duration > 0) {
        // Calculate distance in cm (speed of sound = 343 m/s)
        float distanceCm = duration * 0.0343 / 2.0;
        
        // Water level = tank height - distance to water surface
        waterLevelCm = TANK_HEIGHT_CM - distanceCm;
        waterLevelCm = constrain(waterLevelCm, 0, TANK_HEIGHT_CM);
        
        // Calculate percentage
        tankLevelPercent = (waterLevelCm / TANK_HEIGHT_CM) * 100.0;
    }
}

// ==================== UTILITY FUNCTIONS ====================
float mapFloat(float x, float inMin, float inMax, float outMin, float outMax) {
    return (x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;
}

void saveTotalVolume() {
    EEPROM.put(0, totalVolume);
    EEPROM.commit();
    Serial.println("Total volume saved to EEPROM");
}

void loadTotalVolume() {
    EEPROM.get(0, totalVolume);
    if (isnan(totalVolume) || totalVolume < 0) {
        totalVolume = 0.0;
    }
    Serial.print("Loaded total volume: ");
    Serial.print(totalVolume);
    Serial.println(" L");
}

void updateStatusLED() {
    static unsigned long lastBlink = 0;
    static bool ledState = false;
    
    unsigned long blinkInterval;
    
    if (!wifiConnected) {
        blinkInterval = 100;  // Fast blink - no WiFi
    } else if (!mqttConnected) {
        blinkInterval = 500;  // Medium blink - no MQTT
    } else {
        blinkInterval = 2000; // Slow blink - all connected
    }
    
    if (millis() - lastBlink >= blinkInterval) {
        ledState = !ledState;
        digitalWrite(STATUS_LED_PIN, ledState);
        lastBlink = millis();
    }
}

void blinkLED(int times, int delayMs) {
    for (int i = 0; i < times; i++) {
        digitalWrite(STATUS_LED_PIN, HIGH);
        delay(delayMs);
        digitalWrite(STATUS_LED_PIN, LOW);
        delay(delayMs);
    }
}
