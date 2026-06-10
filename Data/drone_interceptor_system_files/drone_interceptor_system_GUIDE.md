## Tools
- Soldering iron with fine tip
- Wire strippers
- Heat gun (for heat shrink)
- M3 hex key
- M2 hex key
- 3D printer (PETG and PLA capable)
- Multimeter
- Hobby knife / Precision cutters
- Tweezers
- Screwdriver set
- Adhesive (e.g., CA glue, epoxy for servos/mounts)

## Assumptions
- Basic soldering experience
- Familiarity with 3D printing processes and materials (PETG, PLA)
- Ability to flash firmware to microcontrollers (ESP32)
- Basic understanding of UART, I2C, and PWM communication protocols
- Access to a computer with necessary software for configuration and programming

## 1. Fabrication
### 1.1 3D print all missile body sections, nose cone, fins, and internal mounts
**3D print all custom missile structural and internal components.**
1. Print the Missile Front, Middle, and Rear Body Sections using PETG with 0.2mm layer height and 50% infill.
2. Print the Missile Nose Cone and all four Missile Fins using PETG with 0.15mm layer height and 100% infill.
3. Print the Fin Servo Mounts using PETG with 0.2mm layer height and 30% infill.
4. Print the Front Electronics Tray using PETG with 0.2mm layer height and 20% infill.
5. Print the Rocket Motor Mount using PETG with 0.2mm layer height, 50% infill, and 4 walls.
6. Inspect all 3D printed parts for defects and carefully remove any support material.
  > Tip: Ensure proper bed adhesion and temperature settings for PETG to prevent warping, especially for larger missile body sections.

### 1.2 3D print the Missile Rail Guides for the launch rail
**3D print the small guides for the missile launch rail.**
1. Load PLA filament into your 3D printer.
2. Print the Missile Rail Guides using PLA material with a 0.2mm layer height and 50% infill.
3. Allow the printed parts to cool completely on the build plate.
4. Carefully remove the printed Missile Rail Guides and inspect them for any imperfections.

### 1.3 3D print the Radar Enclosure and Mounting Bracket
**3D print the radar enclosure and its mounting bracket.**
1. Print the Separate Radar Enclosure using PETG with 0.2mm layer height and 20% infill.
2. Print the Radar Mounting Bracket using PETG with 0.2mm layer height and 25% infill.
3. Carefully remove any support material and inspect both parts for print quality.
  > Tip: Ensure printer calibration is good for small details on the enclosure, as it houses sensitive electronics.

### 1.4 Cut and prepare the Missile Launch Rail and Launch Rail Base Plate
**Cut and prepare the aluminum launch rail and plywood base plate.**
1. Measure and cut the aluminum Missile Launch Rail to 1000mm length (if needed).
2. Deburr the cut ends of the Missile Launch Rail to remove any sharp edges.
3. Measure and cut the Plywood Launch Rail Base Plate to 300x300mm dimensions (if needed).
4. Mark and drill mounting holes on the Launch Rail Base Plate for attaching the Rail Mount Bracket.

### 1.5 Test-fit the Missile Guidance MCU, GPS, and Comm Module onto the Front Electronics Tray
**Test-fit missile electronics onto the front tray.**
1. Place the Missile Guidance MCU onto the Front Electronics Tray, aligning its mounting holes with the M3 Missile Standoff locations.
2. Loosely insert the M3 Missile Standoffs through the tray and into the Missile Guidance MCU to confirm fit.
3. Position the Missile GPS Module on its designated spot on the tray and align its mounting holes.
4. Position the Missile Wireless Comm Module on its designated spot on the tray and align its mounting holes.
5. Use M2 Missile Screws to loosely secure the Missile GPS Module and Missile Wireless Comm Module to the tray.
6. Verify that all components fit well on the Front Electronics Tray without interference.
  > Tip: Avoid tightening screws or standoffs fully during test-fitting to prevent stripping plastic threads or damaging components.

### 1.6 Test-fit the Radar MCU, mmWave Radar Module, and Comm Module into the Radar Enclosure
*(not yet generated)*

## 2. Wiring
### 2.1 Solder Missile 5V Regulator to Missile Main LiPo Battery's power leads
*(not yet generated)*

### 2.2 Connect Missile GPS Module, Fin Actuator Servos, and Missile Comm Module to the 5V Regulator and Missile Guidance MCU
*(not yet generated)*

### 2.3 Wire the Igniter Trigger Module to the Missile Guidance MCU and Missile Main LiPo Battery
*(not yet generated)*

### 2.4 Solder Radar 3.3V Regulator to Radar LiPo Battery
*(not yet generated)*

### 2.5 Connect Millimeter-wave Radar Module and Radar Comm Module to the 3.3V Regulator and Radar System MCU
*(not yet generated)*

### 2.6 Attach the Radar Comm Whip Antenna to the Radar Wireless Comm Module
*(not yet generated)*

## 3. Bring-up
### 3.1 Flash and configure firmware for the Missile Guidance MCU
*(not yet generated)*

### 3.2 Verify Missile GPS Module functionality and calibrate servos
*(not yet generated)*

### 3.3 Test missile wireless communication link
*(not yet generated)*

### 3.4 Perform a safe functional test of the Igniter Trigger Module (without Solid-Fuel Rocket Motor connected)
*(not yet generated)*

### 3.5 Flash and configure firmware for the Radar System MCU
*(not yet generated)*

### 3.6 Test data acquisition from the Millimeter-wave Radar Module
*(not yet generated)*

### 3.7 Test radar system's wireless communication link
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the Missile Guidance MCU, GPS, Comm Module, and 5V Regulator onto the Front Electronics Tray
**Mount missile electronics and regulator to the front tray.**
1. Secure the Missile Guidance MCU to the Front Electronics Tray using M3 Missile Standoffs.
2. Mount the Missile GPS Module onto the Front Electronics Tray using M2 Missile Screws.
3. Mount the Missile Wireless Comm Module onto the Front Electronics Tray using M2 Missile Screws.
4. Affix the Missile 5V Regulator to the Front Electronics Tray using a strong adhesive, ensuring proper orientation.
5. Confirm all components are securely fastened and aligned on the tray.

### 4.2 Assemble the Missile Fin Actuator Servos into the Fin Servo Mounts and attach to the Missile Rear Body Section with Fins
*(not yet generated)*

### 4.3 Integrate the Rocket Motor Mount and Solid-Fuel Rocket Motor into the Missile Rear Body Section
*(not yet generated)*

### 4.4 Assemble the Missile Body Sections, Nose Cone, and internal components (electronics tray, main LiPo)
*(not yet generated)*

### 4.5 Assemble the Radar System components into the Radar Enclosure and attach the mounting bracket and antenna
*(not yet generated)*

### 4.6 Mount the Launch Rail to the Launch Rail Base Plate using the Rail Mount Bracket, and attach Missile Rail Guides to the missile body
*(not yet generated)*

### 4.7 Perform final checks of all connections, cable routing, and mechanical fastenings for both systems
*(not yet generated)*
