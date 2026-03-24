#include <Servo.h>

Servo driveServo1;
Servo driveServo2;
Servo steerServo;

String input;
int speed;
int steering;

unsigned long lastCommandTime = 0;
const int timeout = 500; // ms

void setup() {
  Serial.begin(9600);
  driveServo1.attach(9);
  driveServo2.attach(11);
  steerServo.attach(10);
}

void loop() {

  if (Serial.available()) {

    input = Serial.readStringUntil('\n');

    int commaIndex = input.indexOf(',');
    if (commaIndex > 0) {
      speed = input.substring(0, commaIndex).toInt();
      steering = input.substring(commaIndex + 1).toInt();
    }

    lastCommandTime = millis();

    int driveSignal1 = 90 + speed;   // adjust offset if needed
    int driveSignal2 = 90 - speed;

    driveServo1.write(driveSignal1);
    driveServo2.write(driveSignal2);
    steerServo.write(steering);
  }

  // ----- communication timeout safety -----
  if (millis() - lastCommandTime > timeout) {
    driveServo1.write(90);
    driveServo2.write(90);      // stop
    steerServo.write(90);      // center
  }
}