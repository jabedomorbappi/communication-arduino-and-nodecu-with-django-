#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// LCD setup
LiquidCrystal_I2C lcd(0x27,16,2);

// WiFi credentials
const char* ssid = "jabed";
const char* password = "12345678";

// HTTP Client requires WiFiClient object
WiFiClient client;

// Buffer for Arduino serial data
String data = "";

void setup() {
  Serial.begin(9600);  // RX0 for Arduino TX
  lcd.init();
  lcd.backlight();
  lcd.clear();

  // Connect to WiFi
  WiFi.begin(ssid, password);
  lcd.setCursor(0,0); lcd.print("Connecting WiFi...");
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
  }
  lcd.clear();
  lcd.setCursor(0,0); lcd.print("WiFi Connected");
  delay(1000);
  lcd.clear();
}

void loop() {
  // Read incoming data from Arduino
  while(Serial.available()){
    char c = Serial.read();
    data += c;

    if(c == 'Z'){ // End marker received
      // Parse CSV: A<IR1>,<IR2>,<Piezo>,<Relay>,<Speed>Z
      int start = data.indexOf('A')+1;
      int comma1 = data.indexOf(',', start);
      int comma2 = data.indexOf(',', comma1+1);
      int comma3 = data.indexOf(',', comma2+1);
      int comma4 = data.indexOf(',', comma3+1);
      int end = data.indexOf('Z');

      if(start>0 && comma4>0 && end>0){
        String ir1 = data.substring(start, comma1);
        String ir2 = data.substring(comma1+1, comma2);
        String piezo = data.substring(comma2+1, comma3);
        String relay = data.substring(comma3+1, comma4);
        String speed = data.substring(comma4+1, end);

        // Show IR2 + Speed on NodeMCU LCD
        lcd.clear();
        lcd.setCursor(0,0); lcd.print("IR2:"); lcd.print(ir2);
        lcd.setCursor(0,1); lcd.print("Speed:"); lcd.print(speed);

        // Send all data to Django
        sendToDjango(ir1, ir2, piezo, relay, speed);
      }

      data = ""; // Clear buffer for next reading
    }
  }
}

// Function to send data to Django server
void sendToDjango(String ir1, String ir2, String piezo, String relay, String speed){
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(client, "http://192.168.91.94:8000/upload/"); // <-- Replace with your PC IP
    http.addHeader("Content-Type", "application/json");

    String json = "{\"device\":\"vehicle1\",\"ir1\":\""+ir1+"\",\"ir2\":\""+ir2+"\",\"piezo\":\""+piezo+"\",\"relay\":\""+relay+"\",\"speed\":\""+speed+"\"}";
    http.POST(json);
    http.end();
  }
}
