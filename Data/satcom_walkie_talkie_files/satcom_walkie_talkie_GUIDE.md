## Tools
- 3D printer (ABS and PETG capable)
- Soldering iron with fine tip
- Solder (fine gauge, lead-free recommended)
- Wire strippers/cutters
- Heat gun (for heat shrink)
- Multimeter
- M3 hex key
- Tweezers
- Small Phillips screwdriver
- Heat-set insert soldering tip or specialized tool
- USB-to-UART converter (if main_mcu lacks onboard debugger)

## Assumptions
- Basic soldering and electronics assembly experience
- Familiarity with microcontroller firmware development (e.g., Arduino IDE, PlatformIO, or vendor-specific toolchain)
- Understanding of I2C, UART, and SPI communication protocols
- Access to a computer for firmware flashing and testing
- A stable 5V USB power supply for charging and initial testing

## 1. Fabrication
### 1.1 3D Print all mechanical enclosure and mounting components
*(not yet generated)*

### 1.2 Install M3 heat-set inserts into PCB mounting plate and main enclosure rear
*(not yet generated)*

### 1.3 Clean and deburr all 3D printed parts, test-fit main enclosure halves
*(not yet generated)*

### 1.4 Test fit the OLED display, speaker, microphone, and tactile buttons into the front enclosure
*(not yet generated)*

## 2. Wiring
### 2.1 Prepare and tin wire leads for all electrical components
*(not yet generated)*

### 2.2 Solder power management IC, Li-ion charger, and Li-ion battery pack power connections
*(not yet generated)*

### 2.3 Solder all power (VCC/VDD, GND) connections from PMIC to main MCU, Iridium module, audio codec, microphone, and OLED display
*(not yet generated)*

### 2.4 Solder UART connections between main MCU and Iridium module
*(not yet generated)*

### 2.5 Solder I2S/PDM audio connections between main MCU, audio codec, microphone, and speaker
*(not yet generated)*

### 2.6 Solder I2C and GPIO control connections between main MCU, OLED display, and Li-ion charger
*(not yet generated)*

### 2.7 Perform continuity checks on all soldered power and data lines to prevent short circuits
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect main MCU to computer via programming interface and flash initial firmware
*(not yet generated)*

### 3.2 Apply power (via charger USB or battery) and verify stable voltage rails (3.3V) at all power consumers
*(not yet generated)*

### 3.3 Test I2C communication with OLED display, audio codec, and Li-ion charger
*(not yet generated)*

### 3.4 Verify UART communication with Iridium Satellite Transceiver module
*(not yet generated)*

### 3.5 Test audio path: record from microphone and play sound through speaker via audio codec
*(not yet generated)*

### 3.6 Verify Li-ion charger functionality and battery status reporting
*(not yet generated)*

### 3.7 Perform basic functional test of Iridium module (e.g., network registration check)
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the Main Microcontroller onto its mount, and the Audio Codec onto its mount
*(not yet generated)*

### 4.2 Mount the Iridium SBD Module into its mount and the Li-ion Battery Pack into its holder
*(not yet generated)*

### 4.3 Secure all mounted components (MCU, Audio Codec, Iridium Module, Battery Holder) onto the PCB mounting plate using M3 screws
*(not yet generated)*

### 4.4 Mount the PCB mounting plate assembly into the Main Enclosure Rear using M3 screws
*(not yet generated)*

### 4.5 Install OLED Display into its bezel, Microphone into its mount, and Speaker into its grille, then secure these into the Main Enclosure Front
*(not yet generated)*

### 4.6 Route all internal wires neatly, ensuring strain relief and avoiding interference with moving parts or enclosure closing
*(not yet generated)*

### 4.7 Place the enclosure sealing gasket, then carefully close the Main Enclosure Front and Rear shells using M3 screws
*(not yet generated)*

### 4.8 Mount the Satellite Antenna Mount Adapter to the Main Enclosure Rear
*(not yet generated)*
