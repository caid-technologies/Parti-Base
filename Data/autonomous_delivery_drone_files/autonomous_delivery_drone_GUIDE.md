## Tools
- 3D printer (PETG and PLA capable)
- M3 hex key/screwdriver
- Soldering iron (fine tip recommended)
- Solder
- Flux
- Wire strippers
- Wire cutters
- Heat shrink gun
- Precision tweezers
- Small pliers
- Multimeter
- Propeller wrench (or adjustable wrench)

## Assumptions
- Basic electronics knowledge including polarity and voltage identification
- Basic soldering experience for fine pitch components and power connections
- Familiarity with drone flight controller firmware configuration (e.g., ArduPilot, Betaflight)
- Ability to safely handle and discharge LiPo batteries
- Access to a computer for firmware flashing and configuration

## 1. Fabrication
### 1.1 3D print all custom mounts and enclosures
*(not yet generated)*

### 1.2 Clean and deburr all 3D printed parts, removing support material
*(not yet generated)*

## 2. Wiring
### 2.1 Solder XT60 power connector and ESC power leads to the Power Distribution Board
*(not yet generated)*

### 2.2 Solder motor phase wires to the corresponding ESCs
*(not yet generated)*

### 2.3 Connect ESC signal wires to the Flight Controller's PWM/DShot outputs
*(not yet generated)*

### 2.4 Wire power (5V from PDB) and data (UART, I2C) from the Flight Controller to the GPS module
*(not yet generated)*

### 2.5 Wire power (5V from PDB) and data (UART) from the Flight Controller to the Telemetry Radio Module
*(not yet generated)*

### 2.6 Wire power (5V from PDB) and data (SBUS) from the RC Receiver to the Flight Controller
*(not yet generated)*

### 2.7 Wire power (5V from PDB) to the FPV Camera and wire its Video Out to the Video Transmitter's Video In
*(not yet generated)*

### 2.8 Wire power (12V from PDB) to the Video Transmitter and its SmartAudio/IRC Tramp to the Flight Controller
*(not yet generated)*

## 3. Bring-up
### 3.1 Perform initial power-on without propellers and verify PDB 5V/12V outputs
*(not yet generated)*

### 3.2 Connect Flight Controller to PC and flash latest stable firmware (e.g., ArduPilot)
*(not yet generated)*

### 3.3 Configure basic Flight Controller parameters, including ESC protocol and motor order/direction
*(not yet generated)*

### 3.4 Verify RC receiver input, GPS lock, and compass functionality in the Flight Controller software
*(not yet generated)*

### 3.5 Test motor spin direction and throttle response for each motor individually (props removed)
*(not yet generated)*

### 3.6 Verify FPV camera video output and Video Transmitter functionality
*(not yet generated)*

### 3.7 Calibrate IMU (accelerometer/gyro) and compass sensors
*(not yet generated)*

## 4. Assembly
### 4.1 Attach frame arms and landing gear to the Frame Bottom Plate
*(not yet generated)*

### 4.2 Mount motor mounts and motors onto the frame arms, then attach ESC mounts and ESCs to the frame arms
*(not yet generated)*

### 4.3 Mount the Power Distribution Board onto the Frame Bottom Plate (if not integrated)
*(not yet generated)*

### 4.4 Install the Flight Controller into its enclosure and mount it to the Frame Top Plate with vibration dampeners
*(not yet generated)*

### 4.5 Mount GPS, Telemetry Radio, RC Receiver, Camera, and Video Transmitter modules to their respective mounts and attach to the Frame Top Plate
*(not yet generated)*

### 4.6 Route and secure all electrical wiring using zip ties or electrical tape for strain relief
*(not yet generated)*

### 4.7 Attach the Frame Top Plate to the Frame Bottom Plate using standoffs and screws
*(not yet generated)*

### 4.8 Mount the Battery Tray and the Package Delivery Mechanism to the frame, then install propellers
*(not yet generated)*
