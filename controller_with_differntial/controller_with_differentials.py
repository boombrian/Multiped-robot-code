import pygame
import serial
import time
import math

# ==========================
# CONFIGURATION
# ==========================
SERIAL_PORT = 'COM3'  # Update to your port
STEER_CENTER = 90
STEER_RANGE = 65    
DEADZONE = 0.12  
DEADZONE_GAS = 0.12       # 12% buffer for triggers/sticks
DEADZONE_BRAKE = 0.12

MAX_SPEED_NORMAL = 70
MAX_SPEED_BOOST = 90
SAFE_MODE_SPEED = 40

ACCEL_STEP = 3             # Smooth acceleration ramp per tick

# ----- Robot Geometry (from keyboard code) -----
# L: wheelbase (mm), W: track width (mm)
# R: servo arm radius (mm), L_eff: effective steering link length (mm)
ROBOT_SPECS = {
    "L": 158.0,
    "W": 180.0,
    "R": 28.0,
    "L_eff": 27.0
}
# Pre-calculate geometry constant: C = (W * R) / (2 * L * L_eff)
GEOMETRY_CONSTANT = (ROBOT_SPECS["W"] * ROBOT_SPECS["R"]) / (2.0 * ROBOT_SPECS["L"] * ROBOT_SPECS["L_eff"])

# ==========================
# INITIALIZATION
# ==========================
try:
    arduino = serial.Serial(SERIAL_PORT, 9600, timeout=0.1)
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT}")
except:
    print(f"Serial Connection Failed on {SERIAL_PORT}!")
    exit()

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# --- AUTO-CALIBRATION ---
print("\n[CALIBRATING] Keep triggers at rest...")
time.sleep(1.5)
pygame.event.pump()
RT_HOME = joystick.get_axis(5) 
LT_HOME = joystick.get_axis(2)
print(f"Calibration Done. RT Home: {RT_HOME:.2f}, LT Home: {LT_HOME:.2f}")
print("-" * 40)
print("RT: Gas | LT: Brake/Reverse | A: EMERGENCY STOP")
print("LB: Safe | RB: Boost")
print("-" * 40)

current_speed = 0.0  # Ramped speed (smoothed toward throttle target)

try:
    while True:
        pygame.event.pump()

        # 1. READ INPUTS
        raw_rt = joystick.get_axis(5)
        raw_lt = joystick.get_axis(2)
        raw_steer = joystick.get_axis(0)

        # 2. MAP TRIGGERS to 0.0–1.0 range
        #    Handles both axis directions (rest at -1 or rest at +1)
        gas_val = abs(raw_rt - RT_HOME) / max(abs(1.0 - RT_HOME), abs(-1.0 - RT_HOME), 0.001)
        brake_val = abs(raw_lt - LT_HOME) / max(abs(1.0 - LT_HOME), abs(-1.0 - LT_HOME), 0.001)

        # 3. APPLY DEADZONES
        if gas_val < DEADZONE_GAS: gas_val = 0
        if brake_val < DEADZONE_BRAKE: brake_val = 0
        if abs(raw_steer) < DEADZONE: raw_steer = 0

        # Buttons
        stop_btn = joystick.get_button(0) # A Button
        boost = joystick.get_button(5)    # RB
        safe = joystick.get_button(4)     # LB

        # 4. SPEED LOGIC
        limit = MAX_SPEED_BOOST if boost else (SAFE_MODE_SPEED if safe else MAX_SPEED_NORMAL)
        
        # RT moves forward (+), LT moves backward (-)
        target_speed = (gas_val * limit) - (brake_val * limit)

        # Emergency Override
        if stop_btn:
            target_speed = 0
            current_speed = 0  # Immediate stop
            mode_tag = "!!!STOP!!!"
        else:
            mode_tag = "BOOST" if boost else ("SAFE " if safe else "NORM ")

        # 4b. RAMP SPEED (smooth acceleration/deceleration)
        if current_speed < target_speed:
            current_speed = min(current_speed + ACCEL_STEP, target_speed)
        elif current_speed > target_speed:
            current_speed = max(current_speed - ACCEL_STEP, target_speed)

        # 5. SPEED-DEPENDENT STEERING CONSTRAINT
        # Reduces max steering angle at high speeds to prevent tipping
        speed_ratio = abs(current_speed) / max(MAX_SPEED_BOOST, 1)
        steering_factor = 1.0 - speed_ratio * 0.5  # 50% reduction at max speed

        # 6. STEERING ANGLE (with speed constraint applied)
        constrained_steer = raw_steer * steering_factor
        target_steer = int(STEER_CENTER + (constrained_steer * STEER_RANGE))

        # 7. KINEMATIC DIFFERENTIAL (from keyboard code)
        # Uses actual robot geometry instead of an arbitrary factor.
        # delta_theta is the steering deviation from center in radians.
        # v_left  = v * (1 - C * sin(delta_theta))
        # v_right = v * (1 + C * sin(delta_theta))
        # This naturally works in reverse: negative speed flips which
        # wheel gets more/less power, so backward turns are correct.
        delta_theta_deg = target_steer - STEER_CENTER
        delta_theta_rad = math.radians(delta_theta_deg)
        differential_factor = GEOMETRY_CONSTANT * math.sin(delta_theta_rad)

        target_left  = current_speed * (1.0 - differential_factor)
        target_right = current_speed * (1.0 + differential_factor)

        # 8. SEND DATA
        data = f"{int(target_left)},{int(target_right)},{target_steer}\n"
        arduino.write(data.encode())

        # Feedback
        dir_tag = "FWD" if current_speed > 1 else ("REV" if current_speed < -1 else "IDLE")
        print(f"\r[{mode_tag}] {dir_tag} | L:{int(target_left):4} R:{int(target_right):4} | Steer:{target_steer:3}° | Gas:{gas_val:.2f} Brk:{brake_val:.2f} Spd:{current_speed:.0f} ", end="")

        time.sleep(0.04)

except KeyboardInterrupt:
    print("\nStopping...")
    arduino.write("0,0,90\n".encode())
    arduino.close()