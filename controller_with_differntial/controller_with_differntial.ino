#include <Servo.h>

Servo leftRear;      // Pin 9
Servo steeringServo; // Pin 10
Servo rightRear;     // Pin 11

unsigned long lastSignalTime = 0;
const unsigned long TIMEOUT = 500;

void setup() {
  Serial.begin(115200);  // Match Python baud rate
  leftRear.attach(9);
  steeringServo.attach(10);
  rightRear.attach(11);

  // Safe start: all servos to neutral
  leftRear.write(90);
  rightRear.write(90);
  steeringServo.write(90);
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int firstComma = data.indexOf(',');
    int secondComma = data.lastIndexOf(',');

    if (firstComma > 0 && secondComma > firstComma) {
      int L = data.substring(0, firstComma).toInt();
      int R = data.substring(firstComma + 1, secondComma).toInt();
      int S = data.substring(secondComma + 1).toInt();

      // Write servo values directly (all computation done on laptop)
      leftRear.write(constrain(L, 0, 180));
      rightRear.write(constrain(R, 0, 180));
      steeringServo.write(constrain(S, 45, 135));

      lastSignalTime = millis();
    }
  }

  // Safety timeout: stop if no signal received
  if (millis() - lastSignalTime > TIMEOUT) {
    leftRear.write(90);
    rightRear.write(90);
    steeringServo.write(90);
  }
}