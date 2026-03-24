import keyboard
import serial
import time
import math

# Initialize serial connection with Arduino
try:
    arduino = serial.Serial('COM3', 9600)
    time.sleep(2) # Wait for Arduino to reset
except serial.SerialException:
    print("Warning: COM3 not found. Running without serial for testing.")
    arduino = None

# ----- Robot Specifications Dictionary -----
# This dictionary makes it easy to port the code to different size robots.
# L: wheelbase (mm), W: track width (mm)
# R: servo arm radius (mm), L_eff: effective steering link length (mm)
ROBOT_SPECS = {
    "L": 158.0,
    "W": 180.0,
    "R": 28.0,
    "L_eff": 27.0
}

# Pre-calculate the geometry constant C to save processing time
# C = (W * R) / (2 * L * L_eff)
GEOMETRY_CONSTANT = (ROBOT_SPECS["W"] * ROBOT_SPECS["R"]) / (2.0 * ROBOT_SPECS["L"] * ROBOT_SPECS["L_eff"])

# ----- Control Constants -----
SLOW_SPEED = 40
FAST_SPEED = 90 # Note: Servos map 90 to stop, 0/180 to max speed. Base target speed max should be tuned.
MAX_SPEED = FAST_SPEED

MAX_STEER_LEFT = 30
MAX_STEER_RIGHT = 150

ACCEL_STEP = 3
STEER_STEP = 10

target_speed = 0
current_speed = 0

target_steering = 90
current_steering = 90

def send():
    """
    Calculates differential speeds based on delta_theta and current speed,
    formats the message, and sends the exact servo commands to Arduino.
    """
    # 1. Calculate delta theta based on deviation from center (90 degrees)
    delta_theta_deg = current_steering - 90
    delta_theta_rad = math.radians(delta_theta_deg)
    
    # 2. Calculate the differential velocity multiplier based on the kinematic equation
    # v_left = v * (1 - C * sin(delta_theta))
    # v_right = v * (1 + C * sin(delta_theta))
    differential_factor = GEOMETRY_CONSTANT * math.sin(delta_theta_rad)
    
    v_left = current_speed * (1.0 - differential_factor)
    v_right = current_speed * (1.0 + differential_factor)
    
    # 3. Map velocities to continuous rotation servo signals (0 to 180)
    # Assuming 90 is stop, >90 is forward, <90 is reverse.
    # Note: driveSignal2 is inverted (90 - v_right) due to motor mounting symmetry.
    servo_left = int(90 + v_left)
    servo_right = int(90 - v_right)
    servo_steer = int(current_steering)
    
    # 4. Constrain values strictly to prevent hardware malfunction and mechanical damage
    servo_left = max(0, min(180, servo_left))
    servo_right = max(0, min(180, servo_right))
    
    # Strict mechanical boundary limit to prevent breaking the steering system
    servo_steer = max(MAX_STEER_LEFT, min(MAX_STEER_RIGHT, servo_steer))
    
    # 5. Send comma-separated string
    message = f"{servo_left},{servo_right},{servo_steer}\n"
    if arduino:
        arduino.write(message.encode())
    # print(f"Sent: {message.strip()} | v: {current_speed}, delta_theta: {delta_theta_deg}")

while True:
    # ----- speed mode switching -----
    if keyboard.is_pressed('1'):
        MAX_SPEED = SLOW_SPEED
    if keyboard.is_pressed('2'):
        MAX_SPEED = FAST_SPEED

    # ----- emergency stop -----
    if keyboard.is_pressed('space'):
        target_speed = 0
        target_steering = 90

    else:
        # throttle input
        if keyboard.is_pressed('w'):
            target_speed = MAX_SPEED
        elif keyboard.is_pressed('s'):
            target_speed = -MAX_SPEED
        else:
            target_speed = 0

        # steering input
        if keyboard.is_pressed('a'):
            target_steering = MAX_STEER_LEFT
        elif keyboard.is_pressed('d'):
            target_steering = MAX_STEER_RIGHT
        else:
            target_steering = 90

    # ----- speed-dependent steering constraint -----
    # Reduces maximum steering angle at high speeds to prevent tipping over
    steering_factor = 1.0 - (abs(current_speed) / max(FAST_SPEED, 1)) * 0.5
    adjusted_target_steering = 90 + (target_steering - 90) * steering_factor

    # ----- ramp throttle (linear acceleration) -----
    if current_speed < target_speed:
        current_speed = min(current_speed + ACCEL_STEP, target_speed)
    elif current_speed > target_speed:
        current_speed = max(current_speed - ACCEL_STEP, target_speed)

    # ----- ramp steering (smooth servo movement) -----
    if current_steering < adjusted_target_steering:
        current_steering += STEER_STEP
    elif current_steering > adjusted_target_steering:
        current_steering -= STEER_STEP

    send()

    if keyboard.is_pressed('esc'):
        if arduino:
            arduino.write(b"90,90,90\n") # Send safe stop before exiting
        break

    time.sleep(0.05)