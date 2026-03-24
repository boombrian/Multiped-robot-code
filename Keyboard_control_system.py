import keyboard
import serial
import time

arduino = serial.Serial('COM3', 9600)
time.sleep(2)

# ----- speed modes -----
SLOW_SPEED = 40
FAST_SPEED = 90
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
    message = f"{int(current_speed)},{int(current_steering)}\n"
    arduino.write(message.encode())

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
        # throttle
        if keyboard.is_pressed('w'):
            target_speed = MAX_SPEED
        elif keyboard.is_pressed('s'):
            target_speed = -MAX_SPEED
        else:
            target_speed = 0

        # steering
        if keyboard.is_pressed('a'):
            target_steering = MAX_STEER_LEFT
        elif keyboard.is_pressed('d'):
            target_steering = MAX_STEER_RIGHT
        else:
            target_steering = 90

    # ----- speed-dependent steering -----
    steering_factor = 1 - abs(current_speed)/MAX_SPEED * 0.5
    adjusted_target_steering = 90 + (target_steering - 90) * steering_factor

    # ----- ramp throttle -----
    if current_speed < target_speed:
        current_speed = min(current_speed + ACCEL_STEP, target_speed)
    elif current_speed > target_speed:
        current_speed = max(current_speed - ACCEL_STEP, target_speed)

    # ----- ramp steering -----
    if current_steering < adjusted_target_steering:
        current_steering += STEER_STEP
    elif current_steering > adjusted_target_steering:
        current_steering -= STEER_STEP

    send()

    if keyboard.is_pressed('esc'):
        break

    time.sleep(0.05)