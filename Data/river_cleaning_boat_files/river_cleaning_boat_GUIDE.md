## Tools
- 3D printer (PETG capable)
- M3 hex key set
- Screwdriver set (Phillips/Flathead)
- Wire strippers
- Crimping tool (if using crimp connectors)
- Soldering iron with fine tip
- Solder (lead-free recommended)
- Multimeter
- Hobby knife or deburring tool
- Pliers (needle-nose)
- Heat gun (for heat shrink tubing)
- Drill and drill bits (for boat hull modifications)
- Adhesive/Sealant (for shaft seals)
- Cable ties/Velcro straps

## Assumptions
- Basic soldering experience
- Familiarity with 3D printer operation and PETG printing
- Basic understanding of DC electronics and safe battery handling (LiPo)
- Access to a computer with Arduino IDE or similar development environment for microcontroller programming
- Ability to compile and upload firmware to the Main Controller (main_mcu)
- Access to a 12V DC power supply for initial testing (optional, but recommended)

## 1. Fabrication
### 1.1 3D print all custom parts (mounts, frames, gears, enclosure)
*(not yet generated)*

### 1.2 Clean and deburr all 3D printed parts
*(not yet generated)*

### 1.3 Prepare boat hull: Mark and drill mounting holes for internal plate, conveyor frames, debris scoop/bin, solar panel frame, and propulsion shaft components.
*(not yet generated)*

### 1.4 Install waterproof cable glands into the electronics enclosure base.
*(not yet generated)*

## 2. Wiring
### 2.1 Solder motor phase wires to Left and Right Propulsion Motors.
*(not yet generated)*

### 2.2 Solder VCC and GND wires to the Conveyor Belt Motor.
*(not yet generated)*

### 2.3 Prepare power wiring: Solar Panel to MPPT, MPPT to LiPo, MPPT to PDB, PDB to ESCs, PDB to 5V Regulator.
*(not yet generated)*

### 2.4 Prepare 5V power wiring: 5V Regulator to RC Receiver, Main Controller, and Conveyor Motor Driver (VCC).
*(not yet generated)*

### 2.5 Prepare signal wiring: Main Controller to ESCs (PWM), RC Receiver to Main Controller (UART), Main Controller to Conveyor Motor Driver (GPIO).
*(not yet generated)*

### 2.6 Connect Conveyor Motor to Conveyor Motor Driver outputs.
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect Solar Panel and LiPo battery to MPPT Charge Controller; verify charging functionality.
*(not yet generated)*

### 3.2 Power the Power Distribution Board from the MPPT; verify 5V and 12V outputs from PDB and 5V Regulator using a multimeter.
*(not yet generated)*

### 3.3 Upload basic firmware to Main Controller (main_mcu) to test GPIOs and UART communication.
*(not yet generated)*

### 3.4 Connect RC Receiver to Main Controller; verify signal reception and mapping in firmware.
*(not yet generated)*

### 3.5 Connect ESCs to Main Controller; perform initial motor calibration and test propulsion motors without propellers.
*(not yet generated)*

### 3.6 Connect Conveyor Motor Driver to Main Controller and Conveyor Motor; test basic motor function (forward/reverse).
*(not yet generated)*

## 4. Assembly
### 4.1 Mount Left and Right Propulsion Motor Mounts to the Internal Mounting Plate, then attach propulsion motors to mounts.
*(not yet generated)*

### 4.2 Assemble propeller shafts: Attach shaft couplings to motor shafts, then slide shafts through bearings and seals in the boat hull, securing propellers.
*(not yet generated)*

### 4.3 Mount ESCs, Main Controller, RC Receiver, and Conveyor Motor Driver to their respective 3D printed mounts, then attach mounts to the Internal Mounting Plate.
*(not yet generated)*

### 4.4 Assemble the Conveyor Belt mechanism: Mount conveyor frames to the boat hull, attach rollers and gears, then mount the conveyor motor with its gear. Wrap conveyor belt material around rollers.
*(not yet generated)*

### 4.5 Mount the Internal Mounting Plate, Debris Scoop, Debris Storage Bin, and Solar Panel Mount Frame to the Boat Hull.
*(not yet generated)*

### 4.6 Install the Main Solar Panel onto its mount frame.
*(not yet generated)*

### 4.7 Place the LiPo Battery in its compartment and secure it with the LiPo Battery Strap.
*(not yet generated)*

### 4.8 Route all electrical cables through cable glands, tidy wiring, and secure the Electronics Enclosure Lid with the gasket to its base.
*(not yet generated)*
