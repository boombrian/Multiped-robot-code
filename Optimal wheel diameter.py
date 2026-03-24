import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Estimated robot parameters
# -----------------------------

mass = 2.0                 # kg
g = 9.81
slope_deg = 18
theta = np.radians(slope_deg)

robot_length = 0.25        # m
robot_width = 0.18         # m
distance_bodycenter_wheels = 0.19     # m

wheel_mass = 0.1           # kg

# Motor parameters
stall_torque = 1.1        # Nm
free_rpm = 200             # RPM at wheel
free_speed = 2*np.pi*free_rpm/60   # rad/s
motor_max_power = 6  # Watts

# Competition constraints
max_height = 0.125
track_turn_radius = 0.20

max_radius = max_height/2

# -----------------------------
# Traction justification (if the robot will slip on the slope)
# -----------------------------

mu_available = 0.7
mu_required = np.tan(theta)

if mu_available < mu_required:
    print("Robot will slip on slope")

# -----------------------------
# Wheel sizes to test
# -----------------------------

radii = np.linspace(0.02, max_radius, 200)

speed = []
required_torque = []
available_torque = []
turning_agility = []
power_required = []
score = []

for r in radii:

    # Force required to climb slope
    F_slope = mass * g * np.sin(theta)

    # Required wheel torque
    tau_req = F_slope * r
    required_torque.append(tau_req)

    # Motor torque-speed relationship
    # solve for achievable speed where motor torque = load torque

    tau = tau_req

    if tau >= stall_torque:
        v = 0
        tau_motor = 0
    else:
        omega_wheel = free_speed * (1 - tau/stall_torque)
        v = omega_wheel * r
        tau_motor = tau

    speed.append(v)
    available_torque.append(tau_motor)

    # Robot turning footprint
    robot_radius = distance_bodycenter_wheels

    # Turning model
    I_body = (1/12)*mass*(robot_length**2 + robot_width**2)
    I_wheel = 0.5 * wheel_mass * r**2 + wheel_mass * robot_radius**2
    I_total = I_body + 4*I_wheel

    alpha = stall_torque / I_total
    turning_agility.append(alpha)

    # Power required to climb slope
    P_required = mass * g * np.sin(theta) * v
    power_required.append(P_required)

speed = np.array(speed)
required_torque = np.array(required_torque)
turning_agility = np.array(turning_agility)
power_required = np.array(power_required)

# -----------------------------
# Normalize metrics
# -----------------------------

speed_n = speed / np.max(speed) if np.max(speed) > 0 else speed
turning_n = turning_agility / np.max(turning_agility) if np.max(turning_agility) > 0 else turning_agility

# Combine metrics into score
w_speed = 0.5
w_turn  = 0.5
score = w_speed * speed_n + w_turn * turning_n

# Apply feasibility constraints
# Feasible wheels (can climb slope)
feasible = (required_torque < stall_torque) & (power_required < motor_max_power) & (distance_bodycenter_wheels <= track_turn_radius)
score[~feasible] = 0

# Find optimal wheel
best_index = np.argmax(score)
best_radius = radii[best_index]

print("Optimal wheel radius:", round(best_radius*1000,1),"mm")
print("Optimal wheel diameter:", round(best_radius*2000,1),"mm")

# Feasible wheels (can climb slope)
feasible = required_torque < stall_torque

# -----------------------------
# Plots
# -----------------------------

plt.figure()
plt.plot(radii*1000, speed)
plt.xlabel("Wheel Radius (mm)")
plt.ylabel("Robot Speed (m/s)")
plt.title("Speed vs Wheel Size")
plt.show()

plt.figure()
plt.plot(radii*1000, required_torque)
plt.axhline(stall_torque, linestyle="--")
plt.xlabel("Wheel Radius (mm)")
plt.ylabel("Torque (Nm)")
plt.title("Torque Required to Climb Slope")
plt.show()

plt.figure()
plt.plot(radii*1000, turning_agility)
plt.xlabel("Wheel Radius (mm)")
plt.ylabel("Turning Agility")
plt.title("Turning Performance")
plt.show()

plt.figure()
plt.plot(radii*1000, power_required)
plt.axhline(motor_max_power, linestyle="--")
plt.xlabel("Wheel Radius (mm)")
plt.ylabel("Power (W)")
plt.title("Power Required to Climb Slope")
plt.show()

plt.figure()
plt.plot(radii*1000, score)
plt.xlabel("Wheel Radius (mm)")
plt.ylabel("Performance Score")
plt.title("Overall Performance (Speed + Turning)")
plt.show()