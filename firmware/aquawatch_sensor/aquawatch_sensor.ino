/*
 * AquaWatch NRW - ESP32 Sensor Node Firmware
 * Non-Revenue Water Detection System for Zambia/South Africa
 * 
 * Hardware: ESP32-WROOM-32
 * Sensors: Flow meter (pulse), Pressure sensor (analog), Ultrasonic level
 * Communication: WiFi + MQTT to central dashboard
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

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

// Status LED
#define STATUS_LED_PIN 2

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

// Timing
unsigned long lastSensorRead = 0;
unsigned long lastMqttPublish = 0;
const unsigned long SENSOR_READ_INTERVAL = 1000;   // 1 second
const unsigned long MQTT_PUBLISH_INTERVAL = 5000;  // 5 seconds

// Status
bool wifiConnected = false;
bool mqttConnected = false;

// ==================== INTERRUPT SERVICE ROUTINE ====================
void IRAM_ATTR flowPulseISR() {
    flowPulseCount++;
}

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    Serial.println("\n========================================");
    Serial.println("AquaWatch NRW - Sensor Node Starting...");
    Serial.println("========================================\n");

    // Initialize EEPROM for persistent storage
    EEPROM.begin(512);

    // Configure pins
    pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);
    pinMode(PRESSURE_SENSOR_PIN, INPUT);
    pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
    pinMode(ULTRASONIC_ECHO_PIN, INPUT);
    pinMode(STATUS_LED_PIN, OUTPUT);

    // Attach flow sensor interrupt
    attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), flowPulseISR, FALLING);

    // Load saved total volume from EEPROM
    loadTotalVolume();

    // Connect to WiFi
    connectWiFi();

    // Configure MQTT
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(1024);

    // Connect to MQTT
    connectMQTT();

    Serial.println("\nSensor Node Ready!");
    blinkLED(3, 200);
}

// ==================== MAIN LOOP ====================
void loop() {
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
        lastSensorRead = millis();
    }

    // Publish data to MQTT
    if (millis() - lastMqttPublish >= MQTT_PUBLISH_INTERVAL) {
        publishSensorData();
        lastMqttPublish = millis();
    }

    // Update status LED
    updateStatusLED();
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
    doc["firmware_version"] = "1.0.0";

    String output;
    serializeJson(doc, output);

    String topic = "aquawatch/" + String(ZONE_ID) + "/" + String(DEVICE_ID) + "/status";
    mqttClient.publish(topic.c_str(), output.c_str(), true);
}

// ==================== SENSOR READING FUNCTIONS ====================
void readAllSensors() {
    readFlowSensor();
    readPressureSensor();
    readUltrasonicSensor();
    
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
