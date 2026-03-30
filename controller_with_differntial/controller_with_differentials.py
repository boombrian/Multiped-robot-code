import pygame
import serial
import time
import math

# ==========================
# CONFIGURATION
# ==========================
SERIAL_PORT = 'COM3'       # Update to your port
BAUD_RATE = 115200         # Faster baud rate to reduce serial delay

STEER_CENTER = 90
STEER_RANGE = 90           # Max degrees from center (90 ± 65)
DEADZONE_STEER = 0.12      # Left stick deadzone
DRIVE_SPEED = 90           # Full drive speed (servo units: 0-90 range from center)

# ----- Robot Geometry (from delta_v_documentation.txt) -----
# L: wheelbase (mm), W: track width (mm)
# R: servo arm radius (mm), L_eff: effective steering link length (mm)
L = 158.0
W = 180.0
R = 28.0
L_eff = 27.0

# Pre-calculate geometry constant: C = (W * R) / (2 * L * L_eff)
C = (W * R) / (2.0 * L * L_eff)

# ==========================
# INITIALIZATION
# ==========================
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
except:
    print(f"Serial Connection Failed on {SERIAL_PORT}!")
    exit()

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Controller: {joystick.get_name()}")
print(f"  Axes: {joystick.get_numaxes()}, Buttons: {joystick.get_numbuttons()}")

# --- CALIBRATION: sample trigger rest values ---
print("\n[CALIBRATING] Do NOT touch triggers...")
time.sleep(1.5)
pygame.event.pump()

# Sample all axes to find trigger rest positions
print("Axis values at rest:")
for i in range(joystick.get_numaxes()):
    print(f"  Axis {i}: {joystick.get_axis(i):.4f}")

RT_REST = joystick.get_axis(5)
LT_REST = joystick.get_axis(4)  # LT is axis 4 on Xbox One controller
TRIGGER_THRESHOLD = 0.15   # Must deviate this much from rest to count as "pressed"

print(f"\nRT rest (axis 5): {RT_REST:.4f}")
print(f"LT rest (axis 4): {LT_REST:.4f}")
print("-" * 40)
print("RT: Full Forward | LT: Full Reverse")
print("Left Stick: Steering")
print("-" * 40)

try:
    while True:
        pygame.event.pump()

        # 1. READ INPUTS
        raw_steer = joystick.get_axis(0)    # Left stick X
        raw_rt = joystick.get_axis(5)       # RT trigger axis
        raw_lt = joystick.get_axis(4)       # LT trigger axis (axis 4 on Xbox One)

        # Detect trigger press: any significant deviation from rest position
        rt_pressed = abs(raw_rt - RT_REST) > TRIGGER_THRESHOLD
        lt_pressed = abs(raw_lt - LT_REST) > TRIGGER_THRESHOLD

        # 2. STEERING (left stick X axis)
        if abs(raw_steer) < DEADZONE_STEER:
            raw_steer = 0

        # Steering servo angle (degrees)
        steer_angle = int(STEER_CENTER + (raw_steer * STEER_RANGE))

        # 3. SPEED: binary full-speed control (no ramping = no delay)
        if rt_pressed and not lt_pressed:
            speed = DRIVE_SPEED           # Full forward
        elif lt_pressed and not rt_pressed:
            speed = -DRIVE_SPEED          # Full reverse
        else:
            speed = 0                     # Idle (both or neither)

        # 4. KINEMATIC DIFFERENTIAL
        # From delta_v_documentation.txt:
        #   delta_theta = steering deviation from center
        #   v_left  = v * (1 - C * sin(delta_theta))
        #   v_right = v * (1 + C * sin(delta_theta))
        delta_theta_deg = steer_angle - STEER_CENTER
        delta_theta_rad = math.radians(delta_theta_deg)
        diff_factor = C * math.sin(delta_theta_rad)

        v_left  = speed * (1.0 - diff_factor)
        v_right = speed * (1.0 + diff_factor)

        # 5. MAP TO SERVO SIGNALS (computed on laptop, sent directly)
        # Continuous rotation servos: 90 = stop, >90 = forward, <90 = reverse
        # Right motor is mounted mirrored, so it needs inversion
        servo_left  = int(90 + v_left * 0.5)
        servo_right = int(90 - v_right * 0.5)   # Inverted for right motor
        servo_steer = int(steer_angle)

        # Constrain to valid servo range
        servo_left  = max(0, min(180, servo_left))
        servo_right = max(0, min(180, servo_right))
        servo_steer = max(45, min(135, servo_steer))

        # 6. SEND 3 SERVO VALUES (Arduino just writes them directly)
        data = f"{servo_left},{servo_right},{servo_steer}\n"
        arduino.write(data.encode())

        # Feedback (includes raw trigger values so you can verify detection)
        if speed > 0:
            dir_tag = "FWD"
        elif speed < 0:
            dir_tag = "REV"
        else:
            dir_tag = "---"
        print(f"\r[{dir_tag}] L:{servo_left:3} R:{servo_right:3} St:{servo_steer:3} | RT:{raw_rt:+.2f} LT:{raw_lt:+.2f} ", end="")

        time.sleep(0.03)  # ~33 Hz update rate

except KeyboardInterrupt:
    print("\nStopping...")
    arduino.write("90,90,90\n".encode())
    arduino.close()