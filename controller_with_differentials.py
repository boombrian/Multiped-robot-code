import pygame
import serial
import time

# ==========================
# CONFIGURATION
# ==========================
SERIAL_PORT = 'COM7'  # Update to your port
STEER_CENTER = 90
STEER_RANGE = 65    
DEADZONE = 0.12  
DEADZONE_GAS = 0.12       # 12% buffer for triggers/sticks
DEADZONE_BRAKE = 0.12

MAX_SPEED_NORMAL = 70
MAX_SPEED_BOOST = 90
SAFE_MODE_SPEED = 40

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
        throttle = (gas_val * limit) - (brake_val * limit)

        # Emergency Override
        if stop_btn:
            throttle = 0
            mode_tag = "!!!STOP!!!"
        else:
            mode_tag = "BOOST" if boost else ("SAFE " if safe else "NORM ")

        # 5. FIXED ELECTRONIC DIFFERENTIAL
        # Inner wheel slows down based on steering direction
        diff_reduction = 0.4 * abs(raw_steer)
        target_left = throttle
        target_right = throttle
        
        if raw_steer > 0.1: # Steering RIGHT
            # The RIGHT wheel is the inner wheel
            target_right *= (1 - diff_reduction)
        elif raw_steer < -0.1: # Steering LEFT
            # The LEFT wheel is the inner wheel
            target_left *= (1 - diff_reduction)

        # 6. STEERING ANGLE
        target_steer = int(STEER_CENTER + (raw_steer * STEER_RANGE))

        # 7. SEND DATA
        data = f"{int(target_left)},{int(target_right)},{target_steer}\n"
        arduino.write(data.encode())

        # Feedback
        dir_tag = "FWD" if throttle > 1 else ("REV" if throttle < -1 else "IDLE")
        print(f"\r[{mode_tag}] {dir_tag} | L:{int(target_left):4} R:{int(target_right):4} | Steer:{target_steer:3}° | Gas:{gas_val:.2f} Brk:{brake_val:.2f} ", end="")

        time.sleep(0.04)

except KeyboardInterrupt:
    print("\nStopping...")
    arduino.write("0,0,90\n".encode())
    arduino.close()

print(f"LT raw={raw_lt:.2f}  LT_home={LT_HOME:.2f}  brake_val={brake_val:.2f}")