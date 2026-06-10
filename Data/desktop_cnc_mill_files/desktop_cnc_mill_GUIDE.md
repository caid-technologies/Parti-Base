## Tools
- 3D printer (PETG/PLA capable)
- M3 hex key
- M5 hex key
- Wire strippers
- Small flathead screwdriver
- Soldering iron (optional, for custom wiring)
- Multimeter
- Measuring tape/ruler
- Deburring tool (for 3D prints)
- Lubricant/grease (for linear motion components)
- Safety glasses

## Assumptions
- Familiarity with 3D printing processes
- Basic understanding of electronics wiring
- Computer with USB port and Arduino IDE/PlatformIO installed
- Basic knowledge of GRBL firmware flashing and configuration
- Access to appropriate CAD software for 3D print file preparation if modifications are needed

## 1. Fabrication
### 1.1 3D print all custom parts (motor mounts, lead screw nut blocks, spindle mount, carriage plates, end-stop mounts, controller enclosure, tool holder)
*(not yet generated)*

### 1.2 Cut or prepare MDF spoilboard to size
*(not yet generated)*

### 1.3 Deburr and clean all 3D printed parts for smooth operation and fit
*(not yet generated)*

### 1.4 Test fit linear bearings (LM8UU) onto linear rods (8mm)
*(not yet generated)*

## 2. Wiring
### 2.1 Wire the main 24V power supply to the buck converter, all stepper drivers, and the spindle motor driver
**Wire 24V power from the main supply to the buck converter, stepper drivers, and spindle driver.**
1. Connect the V+ output of the Main 24V Power Supply to the VIN+ input of the 24V to 5V Converter.
2. Connect the V- (GND) output of the Main 24V Power Supply to the VIN- input of the 24V to 5V Converter.
3. Wire the V+ output of the Main 24V Power Supply to the VMOT pins of the X-Axis Stepper Driver, Y-Axis Stepper Driver, and Z-Axis Stepper Driver.
4. Wire the V- (GND) output of the Main 24V Power Supply to the GND pins of the X-Axis Stepper Driver, Y-Axis Stepper Driver, and Z-Axis Stepper Driver.
5. Connect the V+ output of the Main 24V Power Supply to the Vin+ input of the Spindle Motor Driver.
6. Connect the V- (GND) output of the Main 24V Power Supply to the Vin- input of the Spindle Motor Driver.
  > Tip: Ensure correct polarity for all 24V connections. Use appropriate wire gauge (e.g., 18-22 AWG) for power distribution to prevent voltage drop and overheating.

### 2.2 Connect the 5V output from the buck converter to the ESP32, logic VCC for all stepper drivers, and all end-stop switches
*(not yet generated)*

### 2.3 Connect stepper motors to their respective stepper drivers
*(not yet generated)*

### 2.4 Connect the spindle motor to the spindle motor driver
*(not yet generated)*

### 2.5 Wire ESP32 GPIO pins to stepper driver STEP, DIR, EN pins (D14/D12/D13 for X, D27/D26/D25 for Y, D33/D32/D16 for Z)
*(not yet generated)*

### 2.6 Connect ESP32 PWM pin (D4) to the spindle motor driver PWM input
*(not yet generated)*

### 2.7 Connect end-stop switch signal pins to ESP32 GPIO pins (D19 for X, D18 for Y, D5 for Z)
*(not yet generated)*

### 2.8 Perform continuity checks on all power and signal lines to verify correct wiring
*(not yet generated)*

## 3. Bring-up
### 3.1 Flash GRBL firmware onto the ESP32 microcontroller
*(not yet generated)*

### 3.2 Configure GRBL settings for stepper motor steps/mm, max feedrates, and acceleration
*(not yet generated)*

### 3.3 Test individual stepper motor movement and verify correct direction for X, Y, and Z axes
*(not yet generated)*

### 3.4 Verify end-stop switch functionality and homing sequence in GRBL
*(not yet generated)*

### 3.5 Test spindle motor ON/OFF and speed control via GRBL commands
*(not yet generated)*

## 4. Assembly
### 4.1 Assemble the base frame using aluminum extrusions (base_frame_x_front_back, base_frame_y_side) and corner brackets with M5 hardware
*(not yet generated)*

### 4.2 Mount Y-axis linear rods (y_linear_rods) to the base frame and install Y-axis lead screw (y_axis_lead_screw) with KP08 pillow block bearings
*(not yet generated)*

### 4.3 Assemble the Y-axis gantry (y_gantry_beam, y_gantry_plates) with LM8UU bearings and attach to the Y-axis lead screw via the printed nut block (y_lead_screw_nut_block)
*(not yet generated)*

### 4.4 Mount the Y-axis stepper motor (y_stepper_motor) to its mount (y_motor_mount) and connect to the lead screw with a shaft coupler
*(not yet generated)*

### 4.5 Assemble the X-axis carriage (x_carriage_plate), linear rods, lead screw, and bearings, then mount it to the Y-axis gantry beam
*(not yet generated)*

### 4.6 Mount the X-axis stepper motor (x_stepper_motor) and connect to its lead screw
*(not yet generated)*

### 4.7 Assemble the Z-axis (z_axis_vertical_extrusions, z_carriage_plate, z_linear_rods, z_axis_lead_screw, z_stepper_motor) and mount to the X-axis carriage plate; attach the spindle motor (spindle_motor) to the printed spindle mount (spindle_mount)
*(not yet generated)*

### 4.8 Install all end-stop switches onto their 3D printed mounts and attach mounts to the frame/axes at travel limits
*(not yet generated)*

### 4.9 Mount the spoilboard to the base frame and perform final cable management and routing
*(not yet generated)*
