#include <Servo.h>

// Define 4 motors (assuming continuous rotation servos)
Servo frontLeft;
Servo backLeft;
Servo frontRight;
Servo backRight;

// Pins for the servos (you can change these to match your wiring)
const int PIN_FL = 9;
const int PIN_BL = 10;
const int PIN_FR = 11;
const int PIN_BR = 12;

unsigned long lastSignalTime = 0;
const unsigned long TIMEOUT = 500; // Stop robot if no signal received in 500ms

void setup() {
  Serial.begin(115200);  // High baud rate for low latency
  
  frontLeft.attach(PIN_FL);
  backLeft.attach(PIN_BL);
  frontRight.attach(PIN_FR);
  backRight.attach(PIN_BR);

  // Safe start: all servos to neutral (90 is usually stop for continuous servos)
  stopMotors();
}

void stopMotors() {
  frontLeft.write(90);
  backLeft.write(90);
  frontRight.write(90);
  backRight.write(90);
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    
    // Parse 4 comma-separated values (FL,BL,FR,BR)
    int comma1 = data.indexOf(',');
    int comma2 = data.indexOf(',', comma1 + 1);
    int comma3 = data.indexOf(',', comma2 + 1);

    if (comma1 > 0 && comma2 > comma1 && comma3 > comma2) {
      int fl = data.substring(0, comma1).toInt();
      int bl = data.substring(comma1 + 1, comma2).toInt();
      int fr = data.substring(comma2 + 1, comma3).toInt();
      int br = data.substring(comma3 + 1).toInt();

      // Write servo values directly (computation is done on laptop)
      frontLeft.write(constrain(fl, 0, 180));
      backLeft.write(constrain(bl, 0, 180));
      frontRight.write(constrain(fr, 0, 180));
      backRight.write(constrain(br, 0, 180));

      lastSignalTime = millis();
    }
  }

  // Safety timeout: stop if no commands are received from Python (e.g. laptop disconnected)
  if (millis() - lastSignalTime > TIMEOUT) {
    stopMotors();
  }
}
