#include <Servo.h>

Servo leftRear;
Servo rightRear;

// Future 4WD:
// Servo leftFront;
// Servo rightFront;

int leftPower = 0;
int rightPower = 0;

void setup() {
  Serial.begin(9600);

  leftRear.attach(9);
  rightRear.attach(10);

  // Future:
  // leftFront.attach(6);
  // rightFront.attach(7);
}

void setMotor(Servo &motor, int power, bool invert = false) {
  power = constrain(power, -100, 100);

  int signal;

  if (invert)
    signal = 90 - power * 0.5;
  else
    signal = 90 + power * 0.5;

  motor.write(signal);
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');

    int commaIndex = input.indexOf(',');
    if (commaIndex > 0) {
      leftPower = data.substring(0, commaIndex).toInt();
      rightPower = data.substring(commaIndex + 1).toInt();
    } 

    setMotor(leftRear, leftPower);
    setMotor(rightRear, rightPower, true);

    // Future 4WD:
    // setMotor(leftFront, leftPower);
    // setMotor(rightFront, rightPower, true);
  }
}