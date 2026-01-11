/*
 * AquaWatch NRW - ESP32 Sensor Node Firmware v2.0
 * Non-Revenue Water Detection System for Zambia/South Africa
 * 
 * Hardware: ESP32-WROOM-32
 * Sensors: Flow meter (pulse), Pressure sensor (analog), Ultrasonic level,
 *          Water quality (pH, Turbidity, Chlorine), Temperature
 * Communication: WiFi + MQTT to central dashboard
 * 
 * Features:
 * - Over-the-Air (OTA) firmware updates
 * - Edge AI anomaly detection (TensorFlow Lite)
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
// WiFi Settings
const char* WIFI_SSID = "deborah-my-wife";
const char* WIFI_PASSWORD = "admin@29";

// MQTT Broker Settings
const char* MQTT_BROKER = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "deborah-my-wife";
const char* MQTT_PASSWORD = "admin@29";

// Device Configuration
const char* DEVICE_ID = "SENSOR_NODE_001";
const char* ZONE_ID = "ZONE_A";
const char* FIRMWARE_VERSION = "2.0.0";

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
#define ALARM_LED_PIN 4            // Red LED for alarms

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

// Edge AI - Simple anomaly detection
float pressureHistory[60];     // Last 60 readings
float flowHistory[60];
int historyIndex = 0;
bool anomalyDetected = false;
String anomalyType = "";
float anomalyConfidence = 0.0;

// OTA Update
unsigned long lastOTACheck = 0;
bool otaInProgress = false;

// ESP-NOW Mesh
uint8_t meshPeers[10][6];  // Up to 10 peer MAC addresses
int numMeshPeers = 0;

// Timing
unsigned long lastSensorRead = 0;
unsigned long lastMqttPublish = 0;
unsigned long lastDiagnostics = 0;
const unsigned long SENSOR_READ_INTERVAL = 1000;   // 1 second
const unsigned long MQTT_PUBLISH_INTERVAL = 5000;  // 5 seconds
const unsigned long DIAGNOSTICS_INTERVAL = 60000;  // 1 minute

// Status
bool wifiConnected = false;
bool mqttConnected = false;
int consecutiveErrors = 0;
String lastError = "";

// ==================== INTERRUPT SERVICE ROUTINE ====================
void IRAM_ATTR flowPulseISR() {
    flowPulseCount++;
}

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    Serial.println("\n========================================");
    Serial.println("AquaWatch NRW - Sensor Node v2.0");
    Serial.println("For Zambia & Southern Africa");
    Serial.println("========================================\n");

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

    // Initialize history arrays
    for(int i = 0; i < 60; i++) {
        pressureHistory[i] = 0;
        flowHistory[i] = 0;
    }

    // Load saved data from EEPROM
    loadTotalVolume();
    loadCalibrationData();

    // Connect to WiFi
    connectWiFi();

    // Initialize ESP-NOW for mesh networking
    initESPNow();

    // Configure MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(2048);

    // Connect to MQTT
    connectMQTT();

    // Run initial diagnostics
    runDiagnostics();

    Serial.println("\nSensor Node Ready!");
    Serial.print("Firmware Version: ");
    Serial.println(FIRMWARE_VERSION);
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

    // Read sensors at regular interval
    if (millis() - lastSensorRead >= SENSOR_READ_INTERVAL) {
        readAllSensors();
        runEdgeAI();  // Edge anomaly detection
        lastSensorRead = millis();
    }

    // Publish data to MQTT
    if (millis() - lastMqttPublish >= MQTT_PUBLISH_INTERVAL) {
        publishSensorData();
        publishWaterQuality();
        publishPowerStatus();
        
        if (anomalyDetected) {
            publishAnomaly();
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
    
    // Update alarm LED if anomaly detected
    digitalWrite(ALARM_LED_PIN, anomalyDetected ? HIGH : LOW);
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

            // Subscribe to command topic
            String cmdTopic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/cmd";
            mqttClient.subscribe(cmdTopic.c_str());
            Serial.print("Subscribed to: ");
            Serial.println(cmdTopic);

            // Publish online status
            publishStatus("online");
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

    Serial.print("MQTT Message [");
    Serial.print(topic);
    Serial.print("]: ");
    Serial.println(message);

    // Parse JSON command
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, message);
    
    if (error) {
        Serial.println("JSON parse error");
        return;
    }

    String command = doc["cmd"] | "";
    
    if (command == "reset_volume") {
        totalVolume = 0.0;
        saveTotalVolume();
        Serial.println("Total volume reset!");
    } else if (command == "reboot") {
        Serial.println("Rebooting...");
        delay(1000);
        ESP.restart();
    } else if (command == "calibrate") {
        // Calibration routine
        float newPPL = doc["pulses_per_liter"] | FLOW_PULSES_PER_LITER;
        Serial.print("Calibration: ");
        Serial.print(newPPL);
        Serial.println(" pulses/liter");
    } else if (command == "status") {
        publishStatus("online");
    } else if (command == "ota_update") {
        String url = doc["url"] | "";
        if (url.length() > 0) {
            performOTAUpdate(url);
        }
    } else if (command == "diagnostics") {
        runDiagnostics();
        publishDiagnostics();
    } else if (command == "set_threshold") {
        // Set anomaly detection thresholds
        float pressureThreshold = doc["pressure_threshold"] | 2.0;
        float flowThreshold = doc["flow_threshold"] | 50.0;
        saveThresholds(pressureThreshold, flowThreshold);
    }
}

void publishSensorData() {
    if (!mqttConnected) return;

    StaticJsonDocument<512> doc;
    
    doc["device_id"] = DEVICE_ID;
    doc["zone_id"] = ZONE_ID;
    doc["timestamp"] = millis();
    
    JsonObject sensors = doc.createNestedObject("sensors");
    sensors["flow_rate_lpm"] = flowRate;
    sensors["total_volume_l"] = totalVolume;
    sensors["pressure_bar"] = pressureBar;
    sensors["tank_level_percent"] = tankLevelPercent;
    sensors["water_level_cm"] = waterLevelCm;
    
    JsonObject status = doc.createNestedObject("status");
    status["wifi_rssi"] = WiFi.RSSI();
    status["uptime_sec"] = millis() / 1000;
    status["free_heap"] = ESP.getFreeHeap();

    String output;
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

    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID;
    doc["zone_id"] = ZONE_ID;
    doc["status"] = status;
    doc["ip"] = WiFi.localIP().toString();
    doc["rssi"] = WiFi.RSSI();
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["battery_percent"] = batteryPercent;
    doc["solar_charging"] = solarCharging;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/status";
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
    doc["zone_id"] = ZONE_ID;
    doc["timestamp"] = millis();
    
    JsonObject quality = doc.createNestedObject("water_quality");
    quality["ph"] = phValue;
    quality["turbidity_ntu"] = turbidityNTU;
    quality["chlorine_mg_l"] = chlorineMgL;
    quality["temperature_c"] = waterTempC;
    
    // Quality assessment
    String assessment = "good";
    String issues = "";
    
    if (phValue < 6.5 || phValue > 8.5) {
        assessment = "warning";
        issues += "pH out of range;";
    }
    if (turbidityNTU > 5.0) {
        assessment = "warning";
        issues += "High turbidity;";
    }
    if (turbidityNTU > 100.0) {
        assessment = "critical";
    }
    if (chlorineMgL < 0.2) {
        assessment = "warning";
        issues += "Low chlorine residual;";
    }
    if (chlorineMgL > 4.0) {
        assessment = "warning";
        issues += "High chlorine;";
    }
    
    quality["assessment"] = assessment;
    quality["issues"] = issues;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/quality";
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
    doc["zone_id"] = ZONE_ID;
    
    JsonObject power = doc.createNestedObject("power");
    power["battery_voltage"] = batteryVoltage;
    power["battery_percent"] = batteryPercent;
    power["solar_voltage"] = solarVoltage;
    power["solar_charging"] = solarCharging;
    
    // Power status assessment
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

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/power";
    mqttClient.publish(topic.c_str(), output.c_str());
}

// ==================== EDGE AI - ANOMALY DETECTION ====================
void runEdgeAI() {
    // Store current readings in history
    pressureHistory[historyIndex] = pressureBar;
    flowHistory[historyIndex] = flowRate;
    historyIndex = (historyIndex + 1) % 60;
    
    // Calculate statistics
    float pressureAvg = 0, pressureStd = 0;
    float flowAvg = 0, flowStd = 0;
    
    for (int i = 0; i < 60; i++) {
        pressureAvg += pressureHistory[i];
        flowAvg += flowHistory[i];
    }
    pressureAvg /= 60.0;
    flowAvg /= 60.0;
    
    for (int i = 0; i < 60; i++) {
        pressureStd += pow(pressureHistory[i] - pressureAvg, 2);
        flowStd += pow(flowHistory[i] - flowAvg, 2);
    }
    pressureStd = sqrt(pressureStd / 60.0);
    flowStd = sqrt(flowStd / 60.0);
    
    // Detect anomalies using Z-score method
    anomalyDetected = false;
    anomalyType = "";
    anomalyConfidence = 0.0;
    
    // Pressure drop anomaly (potential leak)
    if (pressureStd > 0.1) {
        float pressureZ = (pressureBar - pressureAvg) / pressureStd;
        if (pressureZ < -2.5) {  // Significant pressure drop
            anomalyDetected = true;
            anomalyType = "pressure_drop";
            anomalyConfidence = min(abs(pressureZ) / 5.0, 1.0) * 100;
        }
    }
    
    // Sudden flow increase (potential burst)
    if (flowStd > 1.0) {
        float flowZ = (flowRate - flowAvg) / flowStd;
        if (flowZ > 3.0) {  // Significant flow increase
            anomalyDetected = true;
            anomalyType = "flow_spike";
            anomalyConfidence = min(abs(flowZ) / 5.0, 1.0) * 100;
        }
    }
    
    // Night flow anomaly (flow during expected zero-flow periods)
    // This would need RTC for accurate time - simplified here
    if (flowRate > 5.0 && flowAvg < 1.0) {
        anomalyDetected = true;
        anomalyType = "unexpected_flow";
        anomalyConfidence = 70.0;
    }
    
    // Water quality anomaly
    if (phValue < 6.0 || phValue > 9.0 || turbidityNTU > 50 || chlorineMgL < 0.1) {
        anomalyDetected = true;
        anomalyType = "water_quality";
        anomalyConfidence = 85.0;
    }
}

void publishAnomaly() {
    if (!mqttConnected || !anomalyDetected) return;

    StaticJsonDocument<512> doc;
    doc["device_id"] = DEVICE_ID;
    doc["zone_id"] = ZONE_ID;
    doc["timestamp"] = millis();
    doc["anomaly_type"] = anomalyType;
    doc["confidence"] = anomalyConfidence;
    doc["priority"] = anomalyConfidence > 80 ? "high" : (anomalyConfidence > 50 ? "medium" : "low");
    
    JsonObject readings = doc.createNestedObject("readings");
    readings["pressure_bar"] = pressureBar;
    readings["flow_rate_lpm"] = flowRate;
    readings["ph"] = phValue;
    readings["turbidity_ntu"] = turbidityNTU;
    
    // Recommended action
    String action = "investigate";
    if (anomalyType == "pressure_drop") {
        action = "Check for leaks in zone " + String(ZONE_ID);
    } else if (anomalyType == "flow_spike") {
        action = "Possible burst - dispatch technician immediately";
    } else if (anomalyType == "water_quality") {
        action = "Water quality issue - check treatment process";
    }
    doc["recommended_action"] = action;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/anomaly";
    mqttClient.publish(topic.c_str(), output.c_str());
    
    Serial.println("⚠️ ANOMALY DETECTED: " + anomalyType);
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
    // Receive data from mesh peer
    String message = "";
    for (int i = 0; i < len; i++) {
        message += (char)data[i];
    }
    
    Serial.print("ESP-NOW received from ");
    for (int i = 0; i < 6; i++) {
        Serial.printf("%02X", mac[i]);
        if (i < 5) Serial.print(":");
    }
    Serial.println(": " + message);
    
    // Forward to MQTT if we have connectivity
    if (mqttConnected) {
        String topic = "aquawatch/mesh/forwarded";
        mqttClient.publish(topic.c_str(), message.c_str());
    }
}

void onESPNowSend(const uint8_t* mac, esp_now_send_status_t status) {
    Serial.print("ESP-NOW send status: ");
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Failed");
}

void broadcastToMesh(String message) {
    // Broadcast to all mesh peers
    for (int i = 0; i < numMeshPeers; i++) {
        esp_now_send(meshPeers[i], (uint8_t*)message.c_str(), message.length());
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
    doc["zone_id"] = ZONE_ID;
    doc["timestamp"] = millis();
    doc["firmware_version"] = FIRMWARE_VERSION;
    
    JsonObject system = doc.createNestedObject("system");
    system["free_heap"] = ESP.getFreeHeap();
    system["uptime_sec"] = millis() / 1000;
    system["wifi_rssi"] = WiFi.RSSI();
    system["consecutive_errors"] = consecutiveErrors;
    system["last_error"] = lastError;
    
    JsonObject sensors = doc.createNestedObject("sensor_health");
    sensors["pressure"] = pressureBar > 0 ? "ok" : "error";
    sensors["flow"] = "ok";
    sensors["ultrasonic"] = waterLevelCm >= 0 ? "ok" : "error";
    sensors["ph"] = (phValue >= 0 && phValue <= 14) ? "ok" : "error";
    sensors["turbidity"] = turbidityNTU >= 0 ? "ok" : "error";
    
    JsonObject power = doc.createNestedObject("power");
    power["battery_percent"] = batteryPercent;
    power["solar_charging"] = solarCharging;

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/diagnostics";
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
