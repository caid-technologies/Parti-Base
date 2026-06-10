## Tools
- 3D printer (PETG capable)
- Filament (PETG)
- Philips head screwdriver (small)
- Philips head screwdriver (medium)
- Soldering iron with fine tip
- Solder wire (rosin core, thin gauge)
- Wire strippers
- Flush cutters
- Multimeter (for continuity and voltage checks)
- Super glue or strong adhesive
- Tweezers
- USB-C data cable
- Computer with USB-C port

## Assumptions
- Basic soldering experience with small components
- Familiarity with 3D printer operation and basic post-processing
- Basic understanding of microcontrollers and flashing firmware (ESP-IDF/Arduino IDE)
- Appropriate development environment (e.g., Arduino IDE, PlatformIO) installed on a computer
- USB-C power adapter for testing

## 1. Fabrication
### 1.1 3D print all main enclosure and display bezel parts
**3D print all main enclosure and display bezel components.**
1. Print the Main Enclosure Bottom Shell with PETG, 25% infill, and 0.2mm layer height.
2. Print the Main Enclosure Top Shell with PETG, 25% infill, and 0.2mm layer height.
3. Print the Circular Display Bezel with PETG, 100% infill, and 0.15mm layer height.
4. Print the Rectangular Display Bezel with PETG, 100% infill, and 0.15mm layer height.
5. Carefully remove all support material and deburr edges from the printed parts.
  > Tip: Ensure your 3D printer bed is perfectly leveled for the first layers of the large enclosure parts to prevent warping.

### 1.2 3D print all internal mounting brackets and small mechanical components
*(not yet generated)*

### 1.3 Clean and deburr all 3D printed parts, remove supports
*(not yet generated)*

### 1.4 Test fit circular display and rectangular display into their bezels
*(not yet generated)*

### 1.5 Insert rotary encoder bearing into main enclosure top and test fit rotary ring parts
*(not yet generated)*

## 2. Wiring
### 2.1 Solder power and data wires to Main Controller (ESP32-S3)
*(not yet generated)*

### 2.2 Solder power wires to Qi2/MagSafe Wireless Charging Module and USB-C Input
*(not yet generated)*

### 2.3 Solder data wires from Main Controller to Circular Clock Display and Rectangular Dashboard Display
*(not yet generated)*

### 2.4 Solder data wires for I2S Audio DAC and Microphone Module, and connect Speaker to DAC
*(not yet generated)*

### 2.5 Wire the Microphone Physical Mute Switch to the Microphone Module
*(not yet generated)*

### 2.6 Solder wires for Main Rotary Encoder and all flush buttons
*(not yet generated)*

### 2.7 Perform continuity checks on all soldered connections
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect Main Controller to computer via USB-C and verify recognition
*(not yet generated)*

### 3.2 Upload basic test firmware to Main Controller to verify GPIO, SPI, and I2S pin assignments
*(not yet generated)*

### 3.3 Test Circular and Rectangular Displays for functionality and backlight control
*(not yet generated)*

### 3.4 Verify Rotary Encoder and all Button inputs are recognized by the Main Controller
*(not yet generated)*

### 3.5 Test I2S Audio DAC and Speaker output; verify Microphone Module input and mute switch
*(not yet generated)*

### 3.6 Test Qi2/MagSafe Wireless Charging Module's power output via USB-C port (loop-through power)
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the USB-C Power Input Connector into its 3D printed mount and secure in main enclosure bottom
*(not yet generated)*

### 4.2 Mount the Main Controller to the MCU mount and secure the assembly in the main enclosure bottom
*(not yet generated)*

### 4.3 Mount I2S Audio DAC, Microphone Module, Speaker, and Microphone Mute Switch with their mounts/grilles into the main enclosure bottom
*(not yet generated)*

### 4.4 Adhere Non-Slip Rubber Feet to the underside of the main enclosure bottom
*(not yet generated)*

### 4.5 Mount the Qi2/MagSafe Wireless Charging Module into its mount and secure into the main enclosure top
*(not yet generated)*

### 4.6 Install Circular and Rectangular Displays into their bezels, then adhere bezels to the main enclosure top
*(not yet generated)*

### 4.7 Mount the Rotary Encoder and all small buttons into the main enclosure top, then place their respective caps
*(not yet generated)*

### 4.8 Route and manage all internal cables using Internal Cable Clips, then close and secure the main enclosure top to the bottom
*(not yet generated)*
