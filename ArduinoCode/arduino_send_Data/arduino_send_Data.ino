#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27,16,2);

// Pins
int IR1 = 2;
int IR2 = 3;
int piezo = A0;
int relay = 8;

unsigned long lastIR1Time = 0;
float speed = 0;

void setup() {
  Serial.begin(9600); // send to NodeMCU RX0
  pinMode(IR1, INPUT);
  pinMode(IR2, INPUT);
  pinMode(relay, OUTPUT);

  lcd.init();
  lcd.backlight();
  lcd.clear();
}

void loop() {
  int s1 = digitalRead(IR1);
  int s2 = digitalRead(IR2);
  int piezoVal = analogRead(piezo);
  int relayStatus = digitalRead(relay);

  // Simple speed calculation
  unsigned long currentTime = millis();
  if(s1 == HIGH && lastIR1Time == 0) lastIR1Time = currentTime;
  if(s2 == HIGH && lastIR1Time != 0) {
    speed = 1000.0 / ((currentTime - lastIR1Time) / 1000.0); // Example speed m/s
    lastIR1Time = 0;
  }

  // Show on Arduino LCD
  lcd.clear();
  lcd.setCursor(0,0); lcd.print("IR1:"); lcd.print(s1);
  lcd.setCursor(0,1); lcd.print("Piezo:"); lcd.print(piezoVal);

  // Send all data to NodeMCU
  Serial.print("A"); // start marker
  Serial.print(s1); Serial.print(",");
  Serial.print(s2); Serial.print(",");
  Serial.print(piezoVal); Serial.print(",");
  Serial.print(relayStatus); Serial.print(",");
  Serial.print(speed);
  Serial.println("Z"); // end marker

  delay(200);
}
