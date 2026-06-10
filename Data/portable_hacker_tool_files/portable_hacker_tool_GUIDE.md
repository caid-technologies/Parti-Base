## Tools
- 3D printer (PETG and PLA capable)
- Soldering iron with fine tip
- Screwdriver set (small Philips/flathead)
- Wire strippers
- Flush cutters
- Multimeter
- Pliers or tweezers (for heat-set inserts)

## Assumptions
- Familiarity with 3D printing processes and settings
- Basic soldering skills for small components and wires
- Basic electronics knowledge and safe handling of LiPo batteries
- Access to a computer with ESP32 development environment (e.g., Arduino IDE, PlatformIO)

## 1. Fabrication
### 1.1 3D Print all enclosure halves and component mounts
*(not yet generated)*

### 1.2 Install M2 heat-set inserts into MCU standoffs, display mount, and RF module mounts
*(not yet generated)*

### 1.3 Install M3 heat-set inserts into the main enclosure bottom half for case assembly
*(not yet generated)*

### 1.4 Test-fit all electrical components into their respective 3D-printed mounts and frames
*(not yet generated)*

## 2. Wiring
### 2.1 Solder power wires from the 3.3V regulator output to main MCU, OLED display, all buttons, Sub-GHz RF module, and NFC/RFID module
*(not yet generated)*

### 2.2 Connect LiPo battery to the charging module and its output to the 3.3V regulator input
*(not yet generated)*

### 2.3 Solder I2C data wires (SDA, SCL) from main MCU to OLED display and NFC/RFID module
*(not yet generated)*

### 2.4 Solder digital input wires from main MCU to each tactile button
*(not yet generated)*

### 2.5 Connect analog input for battery voltage monitoring from LiPo battery to main MCU
*(not yet generated)*

### 2.6 Solder SPI data wires (MOSI, MISO, SCK, CS) from main MCU to Sub-GHz RF module
*(not yet generated)*

### 2.7 Connect external Wi-Fi/BT antenna to main MCU and Sub-GHz antenna to Sub-GHz RF module
*(not yet generated)*

### 2.8 Perform continuity checks on all soldered connections and power rails
*(not yet generated)*

## 3. Bring-up
### 3.1 Mount main MCU to its standoffs in the bottom enclosure half using M2 screws
*(not yet generated)*

### 3.2 Connect LiPo charger to USB power to verify charging LED and battery voltage with multimeter
*(not yet generated)*

### 3.3 Verify stable 3.3V output from the regulator after charging module
*(not yet generated)*

### 3.4 Upload initial test firmware to the main MCU to test OLED display, button inputs, and battery voltage reading
*(not yet generated)*

### 3.5 Test communication with Sub-GHz RF module and NFC/RFID module via respective interfaces
*(not yet generated)*

## 4. Assembly
### 4.1 Mount OLED display to its mount and secure into the main enclosure top half with M2 screws
*(not yet generated)*

### 4.2 Mount all tactile buttons into the button array frame and integrate into the main enclosure top half
*(not yet generated)*

### 4.3 Secure the LiPo battery in its holder within the main enclosure bottom half
*(not yet generated)*

### 4.4 Mount the LiPo charging module and 3.3V regulator onto their combined mount, then attach to bottom enclosure half
*(not yet generated)*

### 4.5 Mount the Sub-GHz RF module and NFC/RFID module to their respective mounts and position in the enclosure
*(not yet generated)*

### 4.6 Integrate both Wi-Fi/BT and Sub-GHz antenna ports into the main enclosure top half and connect antennas
*(not yet generated)*

### 4.7 Carefully close the main enclosure halves, ensuring no wires are pinched, and fasten with M3 screws
*(not yet generated)*

### 4.8 Perform a final power-on and comprehensive functional test of the assembled device
*(not yet generated)*
