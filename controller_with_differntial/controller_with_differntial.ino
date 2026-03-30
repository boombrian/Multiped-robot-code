#include <Servo.h>

Servo leftRear;      // Pin 9
Servo steeringServo; // Pin 10
Servo rightRear;     // Pin 11

unsigned long lastSignalTime = 0;
const unsigned long TIMEOUT = 500; 

void setup() {
  Serial.begin(9600);
  leftRear.attach(9);
  steeringServo.attach(10); 
  rightRear.attach(11);    
  
  stopMotors();
}

void setMotor(Servo &motor, int power, bool invert = false) {
  power = constrain(power, -100, 100);
  int signal = (invert) ? (90 - power * 0.5) : (90 + power * 0.5);
  motor.write(signal);
}

void stopMotors() {
  setMotor(leftRear, 0);
  setMotor(rightRear, 0);
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

      setMotor(leftRear, L);
      setMotor(rightRear, R, true); // Pin 11 motor
      steeringServo.write(constrain(S, 45, 135)); // Pin 10 servo
      
      lastSignalTime = millis();
    }
  }

  if (millis() - lastSignalTime > TIMEOUT) {
    stopMotors();
  }
}