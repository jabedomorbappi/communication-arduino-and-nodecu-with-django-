#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <ESP8266HTTPClient.h>
#include <NTPClient.h> 
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// === I2C LCD SETUP (D1 = SCL, D2 = SDA) ===
LiquidCrystal_I2C lcd(0x27, 16, 2);  // Try 0x3F if blank screen

// === CONFIGURATION ===
const char* ssid = "jabed";
const char* password = "12345678";
const char* django_url = "http://192.168.227.94:8000/api/upload/"; 

// === NTP/Time Setup ===
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 5.5 * 3600, 60000); 

ESP8266WebServer server(80);
WiFiClient client;
HTTPClient http;

// === PINS ===
const int IR1_NODE = 14; 
const int IR2_NODE = 12; 
const int RELAY_NODE = 16;  // Active-LOW relay

// === RELAY STATES ===
bool arduinoRelayState = false;
bool nodemcuRelayState = false;

// === DATA STORAGE & TIMER ===
unsigned long lastSend = 0;
const long sendInterval = 70;

// Global storage for LATEST Arduino data
struct ArduinoSensorData {
    String ir1 = "0";
    String ir2 = "0";
    String piezo_raw = "0";
    String speed = "0.0";
    String arduino_relay = "0";
    String piezo_relay = "0";
};
ArduinoSensorData latestArduinoData;

// Function prototypes
String getFormattedTime();
void sendCombinedData();
void parseAndStoreArduinoData(char* packet);
void updateLCD();

// =================================================================
// SETUP
// =================================================================
void setup() {
    Serial.begin(9600); 
    pinMode(IR1_NODE, INPUT); 
    pinMode(IR2_NODE, INPUT); 
    pinMode(RELAY_NODE, OUTPUT);
    digitalWrite(RELAY_NODE, HIGH);  // HIGH = OFF (active-low)

    // Initialize I2C LCD (uses D1=SCL, D2=SDA by default on NodeMCU)
    Wire.begin(D2, D1);  // SDA = D2, SCL = D1
    lcd.init();
    lcd.backlight();
    lcd.clear();
    lcd.print("IoT Vehicle Sys");
    lcd.setCursor(0, 1);
    lcd.print("Starting...");
    delay(2000);
    lcd.clear();

    WiFi.begin(ssid, password);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        attempts++;
        if (attempts > 20) { 
            Serial.println("\n--- WiFi Connection FAILED! ---");
            break; 
        }
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.print("NodeMCU IP: ");
        Serial.println(WiFi.localIP()); 
        MDNS.begin("vehicle");
        timeClient.begin();
        timeClient.update();
    }

    // --- WEB CONTROL ENDPOINTS (ACTIVE-LOW) ---
    server.on("/relay/on", [](){
        digitalWrite(RELAY_NODE, LOW);   // LOW = ON
        nodemcuRelayState = true;
        updateLCD();
        Serial.println("RELAY_ON (NodeMCU)"); 
        server.send(200, "text/plain", "ON");
    });
    server.on("/relay/off", [](){
        digitalWrite(RELAY_NODE, HIGH);  // HIGH = OFF
        nodemcuRelayState = false;
        updateLCD();
        Serial.println("RELAY_OFF (NodeMCU)"); 
        server.send(200, "text/plain", "OFF");
    });
    server.on("/relay/arduino/on", [](){
        Serial.println("R_ON");
        server.send(200, "text/plain", "ARDUINO_ON_COMMAND_SENT");
    });
    server.on("/relay/arduino/off", [](){
        Serial.println("R_OFF");
        server.send(200, "text/plain", "ARDUINO_OFF_COMMAND_SENT");
    });
    server.begin();
}

// =================================================================
// LOOP
// =================================================================
char serialBuffer[120];
int bufPos = 0;

void loop() {
    server.handleClient();
    yield();

    timeClient.update(); 
    yield();

    if (WiFi.status() == WL_CONNECTED && millis() - lastSend >= sendInterval) {
        sendCombinedData();
        lastSend = millis();
    }
    yield();

    while (Serial.available()) {
        char c = Serial.read();
        
        if (c == 'Z' || bufPos >= 118) {
            serialBuffer[bufPos] = '\0';
            
            if (serialBuffer[0] == 'A') {
                parseAndStoreArduinoData(serialBuffer);
                updateLCD();  // Update LCD when new Arduino data arrives
            }
            bufPos = 0;
        } else if (c >= ' ') { 
            serialBuffer[bufPos++] = c;
        }
        yield();
    }
}

// =================================================================
// LCD UPDATE FUNCTION
// =================================================================
void updateLCD() {
    lcd.clear();
    
    // Line 1: Individual relays
    lcd.setCursor(0, 0);
    lcd.print("ARD:");
    lcd.print(arduinoRelayState ? "ON " : "OFF");
    lcd.print(" NMC:");
    lcd.print(nodemcuRelayState ? "ON " : "OFF");

    // Line 2: Combined state
    lcd.setCursor(0, 1);
    lcd.print("COMMON: ");
    if (arduinoRelayState && nodemcuRelayState) {
        lcd.print("ON ");
    } else {
        lcd.print("OFF");
    }
}

// =================================================================
// COMBINED POST FUNCTION
// =================================================================
void sendCombinedData() {
    int node_ir1 = !digitalRead(IR1_NODE); 
    int node_ir2 = !digitalRead(IR2_NODE); 
    int node_relay_state = digitalRead(RELAY_NODE);
    String currentTime = getFormattedTime(); 

    DynamicJsonDocument doc(512); 

    JsonObject nodemcu = doc.createNestedObject("nodemcu");
    nodemcu["sensor_id"] = "NMCU_01";
    nodemcu["device_capture_time"] = currentTime;
    nodemcu["ir1"] = node_ir1;
    nodemcu["ir2"] = node_ir2;
    nodemcu["nodemcu_relay"] = (node_relay_state == LOW);

    JsonObject arduino = doc.createNestedObject("arduino");
    arduino["sensor_id"] = "ARDU_01";
    arduino["device_capture_time"] = currentTime;
    arduino["ir1"] = latestArduinoData.ir1.toInt();
    arduino["ir2"] = latestArduinoData.ir2.toInt();
    arduino["piezo"] = latestArduinoData.piezo_raw.toInt();
    arduino["speed"] = latestArduinoData.speed.toFloat();
    arduino["arduino_relay"] = (latestArduinoData.arduino_relay == "1");
    arduino["piezo_relay"] = (latestArduinoData.piezo_relay == "1");

    String jsonString;
    serializeJson(doc, jsonString);

    if (http.begin(client, django_url)) {
        http.setTimeout(10000); 
        http.addHeader("Content-Type", "application/json"); 
        int code = http.POST(jsonString);
        yield();
        http.end(); 
    }
}

// =================================================================
// ARDUINO SERIAL PARSER
// =================================================================
void parseAndStoreArduinoData(char* packet) {
    char* t = strtok(packet + 1, ","); 
    String vals[6];
    int i = 0;

    while (t && i < 6) {
        vals[i++] = String(t);
        t = strtok(NULL, ",");
    }

    if (i >= 6) {
        latestArduinoData.ir1 = vals[0];
        latestArduinoData.ir2 = vals[1];
        latestArduinoData.piezo_raw = vals[2];
        latestArduinoData.arduino_relay = vals[3];
        latestArduinoData.piezo_relay = vals[4];
        latestArduinoData.speed = vals[5];
        
        arduinoRelayState = (vals[3] == "1");  // Update global state
    }
}

String getFormattedTime() {
    return timeClient.getFormattedTime();
}