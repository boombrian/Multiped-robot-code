import keyboard
import serial
import time

# ==========================
# CONFIGURATION
# ==========================
SERIAL_PORT = 'COM3'       # Update to your port
BAUD_RATE = 115200         # Fast mode for low latency

# Continuous rotation servo settings
STOP_VAL = 90
MAX_SPEED_OFFSET = 90      # offset from 90 (0 to 180 max range)

# ==========================
# INITIALIZATION
# ==========================
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
except:
    print(f"Warning: Serial Connection Failed on {SERIAL_PORT}!")
    print("Running in test mode without serial connection.")
    arduino = None

print("========================================")
print("       4WD SKID-STEER CONTROLS          ")
print("========================================")
print(" [W] - Full Forward")
print(" [S] - Full Backward")
print(" [A] - Spot Turn Left")
print(" [D] - Spot Turn Right")
print(" [Space] - Emergency Stop")
print(" [Esc] - Quit Program")
print("========================================")

try:
    while True:
        v_left = 0
        v_right = 0
        
        # 1. READ KEYBOARD INPUT
        # Prioritize stop
        if keyboard.is_pressed('space'):
            v_left = 0
            v_right = 0
        elif keyboard.is_pressed('w'):
            v_left = MAX_SPEED_OFFSET
            v_right = MAX_SPEED_OFFSET
        elif keyboard.is_pressed('s'):
            v_left = -MAX_SPEED_OFFSET
            v_right = -MAX_SPEED_OFFSET
        elif keyboard.is_pressed('a'):
            # Rotate left: left side backward, right side forward
            v_left = -MAX_SPEED_OFFSET
            v_right = MAX_SPEED_OFFSET
        elif keyboard.is_pressed('d'):
            # Rotate right: left side forward, right side backward
            v_left = MAX_SPEED_OFFSET
            v_right = -MAX_SPEED_OFFSET

        # 2. MAP TO SERVO SIGNALS
        # Assuming continuous servos: 90 is stop
        # >90 is forward, <90 is backward
        # Right motors are mirrored, so we invert their signal direction
        servo_fl = STOP_VAL + v_left
        servo_bl = STOP_VAL + v_left
        servo_fr = STOP_VAL - v_right   # Inverted
        servo_br = STOP_VAL - v_right   # Inverted
        
        # Constrain to valid servo range (0-180) to be safe
        servo_fl = max(0, min(180, servo_fl))
        servo_bl = max(0, min(180, servo_bl))
        servo_fr = max(0, min(180, servo_fr))
        servo_br = max(0, min(180, servo_br))

        # 3. SEND TO ARDUINO
        # Format: FrontLeft,BackLeft,FrontRight,BackRight
        data = f"{servo_fl},{servo_bl},{servo_fr},{servo_br}\n"
        if arduino:
            arduino.write(data.encode())
            
        # 4. PRINT FEEDBACK
        if v_left > 0 and v_right > 0:
            status = "FWD "
        elif v_left < 0 and v_right < 0:
            status = "BACK"
        elif v_left < 0 and v_right > 0:
            status = "LEFT"
        elif v_left > 0 and v_right < 0:
            status = "RGHT"
        else:
            status = "STOP"
            
        print(f"\r[{status}] FL:{servo_fl:3} BL:{servo_bl:3} FR:{servo_fr:3} BR:{servo_br:3} ", end="")
        
        # 5. EXIT CONDITION
        if keyboard.is_pressed('esc'):
            break
            
        time.sleep(0.05) # ~20 Hz update rate (enough for keyboard)
        
except KeyboardInterrupt:
    pass
    
print("\nStopping...")
if arduino:
    arduino.write("90,90,90,90\n".encode())
    time.sleep(0.1)
    arduino.close()
