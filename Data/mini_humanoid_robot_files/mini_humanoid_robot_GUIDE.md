## Tools
- 3D printer (PETG and PLA capable)
- M2 hex key / precision screwdriver set
- Soldering iron with fine tip
- Wire strippers
- Wire cutters
- Multimeter
- Precision tweezers
- Hobby knife / Deburring tool
- Small files / Sandpaper
- Brass insert installation tip (for soldering iron)

## Assumptions
- Basic soldering experience
- Familiarity with 3D printing and post-processing
- Computer with Arduino IDE or similar development environment installed
- USB cable compatible with main_mcu for programming
- Basic understanding of I2C communication protocols

## 1. Fabrication
### 1.1 3D print all structural and mounting components
*(not yet generated)*

### 1.2 Clean and deburr all 3D printed parts
*(not yet generated)*

### 1.3 Install M2 heat set inserts into all designated mounting points on printed parts
*(not yet generated)*

## 2. Wiring
### 2.1 Solder power leads to LiPo Battery and Charging Module
*(not yet generated)*

### 2.2 Solder power input/output and signal wires to Voltage Regulator
*(not yet generated)*

### 2.3 Solder power and I2C lines to Main Robot Controller and Orientation IMU
*(not yet generated)*

### 2.4 Solder power, I2C, and OE control lines to Servo Driver PWM Controller
*(not yet generated)*

### 2.5 Prepare and label individual servo power and PWM signal wires for all servos
*(not yet generated)*

### 2.6 Connect all servo power and PWM signals to the Servo Driver PWM Controller outputs
*(not yet generated)*

### 2.7 Perform continuity checks on all soldered connections and verify power buses with multimeter
*(not yet generated)*

## 3. Bring-up
### 3.1 Flash initial firmware to the Main Robot Controller (main_mcu)
*(not yet generated)*

### 3.2 Connect power and verify 3.3V and 5V rails using multimeter
*(not yet generated)*

### 3.3 Verify I2C communication with Orientation IMU and Servo Driver from main_mcu
*(not yet generated)*

### 3.4 Test individual servos by sending simple PWM commands through the servo_driver
*(not yet generated)*

### 3.5 Calibrate the Orientation IMU sensor
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the Main Robot Controller, Charging Module, Voltage Regulator, and Battery to their respective mounts in the Robot Torso Chassis
*(not yet generated)*

### 4.2 Mount the Servo Driver PWM Controller into its mount in the Robot Torso Chassis
*(not yet generated)*

### 4.3 Assemble the robot head by mounting the IMU and Head Tilt Servo, then connect to Head Pan Servo
*(not yet generated)*

### 4.4 Assemble the torso and pelvis, mounting the Torso Yaw Servo and attaching the Head Assembly
*(not yet generated)*

### 4.5 Assemble the robot arms: mount servos, attach segments using micro servo horns and screws
*(not yet generated)*

### 4.6 Assemble the robot legs: mount servos, attach segments and feet using micro servo horns and screws
*(not yet generated)*

### 4.7 Route and secure all electrical wiring within the robot for strain relief and neatness
*(not yet generated)*

### 4.8 Perform final system test and calibrate joint limits for all servos
*(not yet generated)*
