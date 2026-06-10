## Tools
- 3D printer (PETG capable)
- Heat gun or soldering iron with flat tip (for heat-set inserts)
- M2.5 hex key or screwdriver
- M3 hex key or screwdriver
- Wire strippers
- Soldering iron with fine tip
- Solder
- Multimeter
- Tweezers
- Small hobby knife or deburring tool
- USB-C power supply (5V, 3A recommended)
- Micro USB cable
- HDMI cable (suitable for SBC to display)
- USB-A to USB-Micro B cable (for display touch)
- USB-A extension cable or adapter (for WiFi adapter)

## Assumptions
- Basic 3D printing knowledge and printer calibration
- Basic soldering experience for small components and wires
- Familiarity with Linux command line for SBC configuration
- Micro SD card with a compatible operating system for the Main Controller SBC is prepared
- Appropriate GPIO breakout cables or jumper wires are available for connecting peripherals to the main_sbc

## 1. Fabrication
### 1.1 3D print all mechanical components according to specified settings
*(not yet generated)*

### 1.2 Clean and deburr all 3D printed parts, removing supports and imperfections
*(not yet generated)*

### 1.3 Install M3 brass heat-set inserts into designated holes in the enclosure bottom shell
*(not yet generated)*

### 1.4 Test-fit the SBC mount with the main_sbc and the display frame with the touch_display
*(not yet generated)*

### 1.5 Test-fit the joystick and button bezels with their respective input modules and buttons
*(not yet generated)*

## 2. Wiring
### 2.1 Prepare and solder wires to the joystick module pins (VCC, GND, VRX, VRY, SW)
*(not yet generated)*

### 2.2 Prepare and solder wires to each tactile button (Signal, GND)
*(not yet generated)*

### 2.3 Connect the Li-Po battery to the power management HAT via the JST-PH connector
*(not yet generated)*

### 2.4 Connect the power management HAT GPIO (I2C/Power) to the main_sbc GPIO (I2C) pins
*(not yet generated)*

### 2.5 Connect the joystick input and all button wires to the appropriate GPIO pins on the main_sbc
*(not yet generated)*

### 2.6 Connect the main_sbc to the touch_display via HDMI for video and USB for touch data
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect the main_sbc to external power (USB-C) and verify boot-up and OS functionality
*(not yet generated)*

### 3.2 Connect the external Wi-Fi adapter to the main_sbc and verify its recognition and connectivity
*(not yet generated)*

### 3.3 Power the touch_display externally (Micro USB) and verify video output from main_sbc via HDMI
*(not yet generated)*

### 3.4 Verify touch input functionality on the display via the USB connection to the main_sbc
*(not yet generated)*

### 3.5 Verify I2C communication and basic power management functions between main_sbc and power_management HAT
*(not yet generated)*

### 3.6 Test all joystick and tactile button inputs, ensuring correct GPIO assignment and responsiveness
*(not yet generated)*

### 3.7 Verify the system can power on and off using the power management HAT and Li-Po battery
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the main_sbc onto the SBC mount using appropriate screws
*(not yet generated)*

### 4.2 Mount the touch_display into the display frame, securing it with M2.5 screws if applicable
*(not yet generated)*

### 4.3 Mount the Li-Po battery into the battery tray and secure the power management HAT onto its mount
*(not yet generated)*

### 4.4 Mount the external Wi-Fi adapter onto its mount
*(not yet generated)*

### 4.5 Secure the SBC mount, Li-Po battery tray, power management mount, and Wi-Fi adapter mount into the enclosure bottom shell using M2.5 screws
*(not yet generated)*

### 4.6 Route all internal cables (HDMI, USB, GPIO, power) neatly and apply strain relief where necessary
*(not yet generated)*

### 4.7 Snap-fit the joystick and button bezels with their respective components into the enclosure top bezel
*(not yet generated)*

### 4.8 Attach the display frame with the touch_display to the enclosure top bezel (clips/M2.5 screws) and then close the enclosure top bezel onto the bottom shell using M3 flat head screws
*(not yet generated)*
