import pygame
import serial
import time

# ==========================
# SERIAL CONNECTION
# ==========================
arduino = serial.Serial('COM3', 9600)  # CHANGE COM PORT
time.sleep(2)

# ==========================
# CONTROLLER INIT
# ==========================
pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Controller connected.")

# ==========================
# PARAMETERS
# ==========================
T_MAX = 100                  # Maximum throttle magnitude
MAX_SPEED_NORMAL = 70
MAX_SPEED_BOOST = 100
SAFE_MODE_SPEED = 40

RAMP_RATE = 3                # Acceleration smoothness
STEERING_REDUCTION = 0.5     # k coefficient (0 to 1)

current_left = 0
current_right = 0


# ==========================
# FUNCTIONS
# ==========================
def apply_deadzone(value, deadzone=0.08):
    if abs(value) < deadzone:
        return 0
    return value


def ramp(current, target):
    if current < target:
        current += RAMP_RATE
        if current > target:
            current = target
    elif current > target:
        current -= RAMP_RATE
        if current < target:
            current = target
    return current


# ==========================
# MAIN LOOP
# ==========================
while True:
    pygame.event.pump()

    # ---- Raw joystick input ----
    raw_throttle = joystick.get_axis(1)  # Forward/back
    raw_steering = joystick.get_axis(0)   # Left/right

    raw_throttle = apply_deadzone(raw_throttle)
    raw_steering = apply_deadzone(raw_steering)

    # ---- Button inputs ----
    boost = joystick.get_button(5)   # R1
    safe = joystick.get_button(4)    # L1
    brake = joystick.get_button(0)   # X button

    # ---- Select speed mode ----
    if boost:
        max_speed = MAX_SPEED_BOOST
    elif safe:
        max_speed = SAFE_MODE_SPEED
    else:
        max_speed = MAX_SPEED_NORMAL

    # ---- Scale throttle ----
    throttle = raw_throttle * max_speed
    steering = raw_steering * max_speed
    throttle_normalized = abs(throttle) / T_MAX
    throttle_normalized = min(throttle_normalized, 1)
    steering_gain = 1 - STEERING_REDUCTION * throttle_normalized
    steering_effective = steering * steering_gain

    # ---- Differential drive ----
    target_left = throttle + steering_effective
    target_right = throttle - steering_effective

    # ---- Clamp values ----
    target_left = max(-100, min(100, target_left))
    target_right = max(-100, min(100, target_right))

    # ---- Brake override ----
    if brake:
        target_left = 0
        target_right = 0

    # ---- Apply ramping ----
    current_left = ramp(current_left, target_left)
    current_right = ramp(current_right, target_right)

    # ---- Send to Arduino ----
    data = f"{int(current_left)},{int(current_right)}\n"
    arduino.write(data.encode())

    time.sleep(0.02)