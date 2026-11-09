/*
 * Anti-Theft Electricity Monitoring System — ESP32 Firmware Sketch
 *
 * Hardware connections:
 * - CT Sensor 1 (Incoming Line): Analog Pin A0 (GPIO 34)
 * - CT Sensor 2 (Meter Output) : Analog Pin A1 (GPIO 35)
 * - Buzzer Pin                 : GPIO 25
 * - Status LED Pin             : GPIO 2
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ============================================================
// CONFIGURATION
// ============================================================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// Server API Endpoint
const char* API_URL = "http://192.168.1.100:5000/api/sensor/data";

// Consumer Config
const int CONSUMER_ID = 1;

// Pins
const int CT_SENSOR_1_PIN = 34; // Incoming Current (I_in)
const int CT_SENSOR_2_PIN = 35; // Meter Output (I_out)
const int BUZZER_PIN      = 25;
const int LED_PIN         = 2;

// Calibration & Thresholds
const float VOLTAGE_RATING = 230.0;
const float THEFT_THRESHOLD = 2.0; // Current difference threshold in Amps
const float CALIBRATION_FACTOR = 30.0; // Calibration factor for CT sensor (e.g. SCT-013)

unsigned long lastPostTime = 0;
const unsigned long POST_INTERVAL = 5000; // Post every 5 seconds


void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==============================================");
    Serial.println("⚡ ESP32 Anti-Theft Electricity Monitor");
    Serial.println("==============================================");

    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);

    // Connect to WiFi
    connectWiFi();
}

void loop() {
    // Reconnect WiFi if lost
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    if (millis() - lastPostTime >= POST_INTERVAL) {
        lastPostTime = millis();

        // 1. Read Current Sensors
        float i_in  = readCTSensor(CT_SENSOR_1_PIN);
        float i_out = readCTSensor(CT_SENSOR_2_PIN);
        float diff  = abs(i_in - i_out);

        Serial.printf("\n[Readings] I_in: %.2f A | I_out: %.2f A | Difference: %.2f A\n", i_in, i_out, diff);

        // 2. Local Theft Alarm Check
        if (diff > THEFT_THRESHOLD) {
            Serial.println("🚨 THEFT DETECTED LOCAL ALARM TRIGGERED!");
            triggerBuzzer(true);
            digitalWrite(LED_PIN, HIGH);
        } else {
            triggerBuzzer(false);
            digitalWrite(LED_PIN, LOW);
        }

        // 3. Post to API Server
        postSensorData(i_in, i_out, VOLTAGE_RATING);
    }
}

// Read and convert ADC value to RMS Current (Amps)
float readCTSensor(int pin) {
    long sum = 0;
    int samples = 500;

    for (int i = 0; i < samples; i++) {
        int raw = analogRead(pin);
        sum += (raw - 2048) * (raw - 2048); // Center around 1.65V (2048 raw)
        delayMicroseconds(100);
    }

    float rmsVoltage = sqrt(sum / (float)samples) * (3.3 / 4095.0);
    float current = rmsVoltage * CALIBRATION_FACTOR;

    return (current < 0.1) ? 0.0 : current; // Filter noise
}

// Connect to WiFi network
void connectWiFi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int attempts = 0;

    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ WiFi Connected!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n❌ WiFi Connection Failed!");
    }
}

// Send HTTP POST payload to API
void postSensorData(float i_in, float i_out, float voltage) {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");

    String jsonPayload = "{";
    jsonPayload += "\"consumer_id\":" + String(CONSUMER_ID) + ",";
    jsonPayload += "\"i_in\":" + String(i_in, 2) + ",";
    jsonPayload += "\"i_out\":" + String(i_out, 2) + ",";
    jsonPayload += "\"voltage\":" + String(voltage, 1);
    jsonPayload += "}";

    int httpCode = http.POST(jsonPayload);

    if (httpCode > 0) {
        String response = http.getString();
        Serial.printf("HTTP Response [%d]: %s\n", httpCode, response.c_str());
    } else {
        Serial.printf("❌ HTTP POST Failed, Error: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
}

// Sound buzzer tone
void triggerBuzzer(bool enable) {
    if (enable) {
        tone(BUZZER_PIN, 2000); // 2kHz tone
    } else {
        noTone(BUZZER_PIN);
    }
}
