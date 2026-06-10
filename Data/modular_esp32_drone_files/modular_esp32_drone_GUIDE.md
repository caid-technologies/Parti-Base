## Tools
- 3D printer (PETG/TPU capable)
- Soldering iron with fine tip
- Solder (lead-free recommended)
- Wire strippers
- Wire cutters
- Heat shrink tubing assortment
- Heat gun or lighter (for heat shrink)
- M3 hex key / screwdriver
- M2 hex key / screwdriver
- Hobby knife / Deburring tool
- Tweezers
- Multimeter
- Zip ties
- Cyanoacrylate adhesive (super glue)

## Assumptions
- Basic understanding of drone components and their function.
- Familiarity with 3D printing processes and post-processing.
- Competent in basic through-hole and surface-mount soldering techniques.
- Access to a computer with a USB port for flashing firmware.
- Knowledge of drone flight controller firmware (e.g., Betaflight, ArduPilot) and configuration software.

## 1. Fabrication
### 1.1 3D print all specified mechanical components
*(not yet generated)*

### 1.2 Clean and deburr all 3D printed parts for smooth fitment
*(not yet generated)*

### 1.3 Test fit motors into motor mounts and ESCs into ESC mounts
*(not yet generated)*

### 1.4 Test fit flight controller, IMU, PDB, and RC receiver into their respective mounts/trays
*(not yet generated)*

## 2. Wiring
### 2.1 Solder motor phase wires to ESC motor outputs
*(not yet generated)*

### 2.2 Solder LiPo battery main leads to Power Distribution Board (PDB) input
*(not yet generated)*

### 2.3 Solder ESC power input leads to PDB motor outputs
*(not yet generated)*

### 2.4 Solder PDB 5V outputs to 5V voltage regulator input, then regulator output to Flight Controller, IMU, and RC Receiver
*(not yet generated)*

### 2.5 Wire ESC PWM signal inputs to Flight Controller PWM outputs
*(not yet generated)*

### 2.6 Wire IMU I2C (SCL/SDA) and power lines to Flight Controller I2C port
*(not yet generated)*

### 2.7 Wire RC Receiver serial (iBUS) output and power lines to Flight Controller UART RX port
*(not yet generated)*

### 2.8 Perform continuity check on all soldered power connections to prevent shorts
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect Flight Controller to computer and flash appropriate drone firmware (e.g., Betaflight, ArduPilot)
*(not yet generated)*

### 3.2 Verify Flight Controller is recognized by the configuration software and basic settings are applied
*(not yet generated)*

### 3.3 Calibrate IMU sensor and verify correct orientation and sensor readings in software
*(not yet generated)*

### 3.4 Bind RC Receiver to transmitter and verify channel outputs are correctly registered by the Flight Controller
*(not yet generated)*

### 3.5 Perform initial ESC calibration and motor direction tests (without propellers for safety)
*(not yet generated)*

### 3.6 Configure flight modes, PID settings, and safety features in Flight Controller software
*(not yet generated)*

## 4. Assembly
### 4.1 Attach arms and landing skids to the central frame plate using M3 screws and nuts
*(not yet generated)*

### 4.2 Mount motor mounts and motors to the arms, and secure ESC mounts to the arms with zip ties/adhesive
*(not yet generated)*

### 4.3 Mount the PDB, 5V regulator, FC tray, IMU mount, RC receiver mount, and battery strap holder to the central frame plate with standoffs and screws
*(not yet generated)*

### 4.4 Install LiPo battery strap through the battery strap holder and secure LiPo battery to the frame
*(not yet generated)*

### 4.5 Route and secure all wiring with zip ties, ensuring no cables interfere with moving parts or propellers
*(not yet generated)*

### 4.6 Attach propellers to the motors, ensuring correct CW/CCW rotation as per motor direction tests
*(not yet generated)*

### 4.7 Attach payload module base plate to central frame (if applicable)
*(not yet generated)*

### 4.8 Perform a final visual inspection and system-level functional test (hover test) in a safe environment
*(not yet generated)*
