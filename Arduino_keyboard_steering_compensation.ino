#include <Servo.h>

Servo driveServo1; // Left rear wheel
Servo driveServo2; // Right rear wheel
Servo steerServo;  // Front steering mechanism

String input;
int servoLeftVal = 90;
int servoRightVal = 90;
int servoSteerVal = 90;

unsigned long lastCommandTime = 0;
const int timeout = 500; // ms communication timeout

void setup() {
  Serial.begin(9600);
  // Attach servos to PWM pins
  driveServo1.attach(9);
  driveServo2.attach(11);
  steerServo.attach(10);
  
  // Initialize to stationary and centered positions
  driveServo1.write(90);
  driveServo2.write(90);
  steerServo.write(90);
}

void loop() {
  // Check if there is incoming serial data from PC
  if (Serial.available()) {
    input = Serial.readStringUntil('\n');

    // Parse the 3 comma-separated values: left_speed, right_speed, steering_angle
    int firstComma = input.indexOf(',');
    int secondComma = input.indexOf(',', firstComma + 1);

    if (firstComma > 0 && secondComma > 0) {
      servoLeftVal = input.substring(0, firstComma).toInt();
      servoRightVal = input.substring(firstComma + 1, secondComma).toInt();
      servoSteerVal = input.substring(secondComma + 1).toInt();
    }

    lastCommandTime = millis();

    // Write the exact pre-calculated signals to the servos
    driveServo1.write(servoLeftVal);
    driveServo2.write(servoRightVal);
    steerServo.write(servoSteerVal);
  }

  // ----- communication timeout safety -----
  // If PC disconnects or crashes, stop all motors immediately
  if (millis() - lastCommandTime > timeout) {
    driveServo1.write(90); // stop
    driveServo2.write(90); // stop
    steerServo.write(90);  // center
  }
}