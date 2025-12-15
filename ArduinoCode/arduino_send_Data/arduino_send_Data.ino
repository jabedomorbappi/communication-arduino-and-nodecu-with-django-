#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2); // LCD address 0x27, 16x2

// Pin definitions
const int IR1 = 2;
const int IR2 = 3;
const int PIEZO = A3;
const int RELAY_ARDUINO = 8; // Active LOW
const int RELAY_PIEZO = 7;   // Active LOW

// Relay timing
const unsigned long MIN_ON_TIME = 2000;  // 2 sec
const unsigned long MIN_OFF_TIME = 1000; // 1 sec
const int PIEZO_THRESHOLD = 900;

// State variables
bool relayPiezoState = false;      // current state
unsigned long relayPiezoTimer = 0; // timer for ON/OFF logic
bool relayArduinoState = false;

// Speed variables
unsigned long entryTime = 0;
unsigned long exitTime = 0;
float speed_kmh = 0.0;
const float vehicle_length_m = 0.1;
const float ms_to_kmh_factor = 3.6;

// LCD timing
unsigned long lastLCDUpdate = 0;
const unsigned long lcdUpdateInterval = 500;

// Serial send timing
unsigned long lastSend = 0;
const unsigned long sendInterval = 300;

void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("IoT Vehicle Sys");
  lcd.setCursor(0,1);
  lcd.print("Initializing...");
  delay(2000);
  lcd.clear();

  pinMode(IR1, INPUT);
  pinMode(IR2, INPUT);
  pinMode(RELAY_ARDUINO, OUTPUT);
  pinMode(RELAY_PIEZO, OUTPUT);

  // Active LOW relays: start OFF (HIGH)
  digitalWrite(RELAY_ARDUINO, HIGH);
  digitalWrite(RELAY_PIEZO, HIGH);

  relayPiezoTimer = millis();

  Serial.println("Arduino + I2C LCD + Piezo Ready.");
}

void loop() {
  unsigned long currentTime = millis();

  // === 1. Receive commands from NodeMCU ===
  while (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "R_ON") {
      digitalWrite(RELAY_ARDUINO, LOW);
      relayArduinoState = true;
    } else if (cmd == "R_OFF") {
      digitalWrite(RELAY_ARDUINO, HIGH);
      relayArduinoState = false;
    }
  }

  // === 2. Read sensors ===
  int ir1_val = !digitalRead(IR1);
  int ir2_val = !digitalRead(IR2);
  int piezo_val = analogRead(PIEZO);

  // === 3. Piezo relay logic with reset timer ===
  if (relayPiezoState) {
    // Relay is ON
    if (piezo_val > PIEZO_THRESHOLD) {
      relayPiezoTimer = currentTime; // reset timer whenever threshold is crossed
    }
    // Turn OFF only if 2 sec passed without threshold crossing
    if (currentTime - relayPiezoTimer >= MIN_ON_TIME) {
      digitalWrite(RELAY_PIEZO, HIGH); // OFF
      relayPiezoState = false;
      relayPiezoTimer = currentTime; // start OFF timer
    }
  } else {
    // Relay is OFF
    // Turn ON if threshold crossed and minimum OFF time passed
    if (piezo_val > PIEZO_THRESHOLD && (currentTime - relayPiezoTimer >= MIN_OFF_TIME)) {
      digitalWrite(RELAY_PIEZO, LOW); // ON
      relayPiezoState = true;
      relayPiezoTimer = currentTime; // start ON timer
    }
  }

  // === 4. Speed calculation ===
  if (ir1_val && entryTime == 0) {
    entryTime = currentTime;
    speed_kmh = 0.0;
  }

  if (!ir1_val && entryTime != 0) {
    exitTime = currentTime;
    unsigned long time_ms = exitTime - entryTime;

    if (time_ms > 50 && time_ms < 3000) {
      float speed_mps = vehicle_length_m / (time_ms / 1000.0);
      speed_kmh = speed_mps * ms_to_kmh_factor;
    } else {
      speed_kmh = 0.0;
    }
    entryTime = 0;
    exitTime = 0;
  }

  if (entryTime != 0 && currentTime - entryTime > 2000) {
    entryTime = 0;
    speed_kmh = 0.0;
  }

  // === 5. Update LCD every 500ms ===
  if (currentTime - lastLCDUpdate >= lcdUpdateInterval) {
    lcd.setCursor(0,0);
    lcd.print("P:");
    if (piezo_val < 1000) lcd.print(" ");
    if (piezo_val < 100) lcd.print(" ");
    if (piezo_val < 10) lcd.print(" ");
    lcd.print(piezo_val);
    lcd.print(" IR1:");
    lcd.print(ir1_val);
    lcd.print("   ");

    lcd.setCursor(0,1);
    lcd.print("Spd:");
    if (speed_kmh < 100) lcd.print(" ");
    if (speed_kmh < 10) lcd.print(" ");
    lcd.print(speed_kmh,1);
    lcd.print("kmh IR2:");
    lcd.print(ir2_val);
    lcd.print(" ");
    lcd.print(relayPiezoState ? "ON " : "OFF");

    lastLCDUpdate = currentTime;
  }

  // === 6. Send data to NodeMCU every 300ms ===
  if (currentTime - lastSend >= sendInterval) {
    Serial.print("A");
    Serial.print(ir1_val); Serial.print(",");
    Serial.print(ir2_val); Serial.print(",");
    Serial.print(piezo_val); Serial.print(",");
    Serial.print(relayArduinoState ? 1 : 0); Serial.print(",");
    Serial.print(relayPiezoState ? 1 : 0); Serial.print(",");
    Serial.print(speed_kmh,1);
    Serial.println("Z");
    lastSend = currentTime;
  }
}
