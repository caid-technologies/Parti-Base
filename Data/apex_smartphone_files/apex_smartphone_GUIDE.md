## Tools
- 3D printer (PETG capable)
- Precision screwdriver set (M1.2 compatible)
- ESD safe tweezers (fine-tip)
- Spudger tool set (plastic and metal)
- Heat gun or equivalent for adhesive curing/softening
- Thermal paste applicator
- Adhesive applicator (for structural and thermal adhesives)
- Multimeter
- Microfiber cloth
- ESD mat and wrist strap

## Assumptions
- All electrical components are pre-assembled onto a main flexible PCB (FPCB) or rigid PCB, with interconnections designed for flex cables or ZIF connectors where applicable. No hand-soldering of SMD components is required.
- The 'main_soc', 'integrated_ram', 'internal_storage', 'power_management_ic_main', 'wireless_module', 'gnss_module', 'audio_codec', 'accelerometer_gyro', 'magnetometer', 'ambient_light_proximity', 'fingerprint_sensor', and 'usb_c_controller' are factory-mounted on one or more PCBs.
- The user has basic electronics assembly experience and familiarity with smartphone construction.
- Required drivers and a host PC are available for initial bring-up and flashing.

## 1. Fabrication
### 1.1 3D print all custom mounts and the vibration motor mount
*(not yet generated)*

### 1.2 Deburr and clean 3D printed parts, ensure fitment for respective components
*(not yet generated)*

### 1.3 Clean all glass panels and lens covers
*(not yet generated)*

## 2. Wiring
### 2.1 Connect Main SoC to LPDDR6 RAM and UFS Storage via flex cables (if not integrated)
*(not yet generated)*

### 2.2 Connect AMOLED Display, Cameras, Wireless Module, GNSS, Audio Codec, and Sensors to Main SoC/PCB via flex cables
*(not yet generated)*

### 2.3 Connect USB-C PD Controller to Main SoC and route VBUS to Power Management IC
*(not yet generated)*

### 2.4 Connect Power Management IC to all power-consuming components and Li-Po Battery
*(not yet generated)*

### 2.5 Connect Linear Haptic Vibrator to Power Management IC and Main SoC (PWM control)
*(not yet generated)*

### 2.6 Perform initial continuity checks on all power and ground lines
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect Li-Po Battery and apply power to the main PCB assembly
*(not yet generated)*

### 3.2 Verify power rails and voltages using a multimeter
*(not yet generated)*

### 3.3 Flash initial firmware/bootloader to Main SoC via USB-C or debug port
*(not yet generated)*

### 3.4 Test basic display functionality and touch input (if integrated with display)
*(not yet generated)*

### 3.5 Verify camera module detection and capture functionality for all cameras
*(not yet generated)*

### 3.6 Test Wireless (5G/Wi-Fi/BT) and GNSS module functionality
*(not yet generated)*

### 3.7 Verify sensor functionality (accelerometer, gyro, magnetometer, ambient light, fingerprint)
*(not yet generated)*

### 3.8 Test audio input (MIC) and output (SPK) via audio codec
*(not yet generated)*

## 4. Assembly
### 4.1 Mount Main SoC, RAM, Storage, Wireless, GNSS, Audio, USB-C Controller, and Sensors into their respective 3D printed mounts and secure mounts to internal midframe with M1.2 screws
*(not yet generated)*

### 4.2 Apply thermal paste to Main SoC and attach vapor chamber to internal midframe, then affix graphite thermal sheets
*(not yet generated)*

### 4.3 Mount linear haptic vibrator into its 3D printed mount and secure to internal midframe
*(not yet generated)*

### 4.4 Adhere Li-Po Battery to internal midframe using the battery adhesive strip
*(not yet generated)*

### 4.5 Install USB-C port gasket, speaker grills, power button, volume rocker, and SIM tray into the unibody chassis
*(not yet generated)*

### 4.6 Install internal midframe assembly into the unibody chassis and secure with M1.2 screws
*(not yet generated)*

### 4.7 Attach main, ultrawide, and telephoto camera modules with gaskets to internal midframe and secure respective lens covers to the rear glass panel, then adhere rear glass panel to unibody chassis
*(not yet generated)*

### 4.8 Attach front camera module with its lens cover, apply display adhesive seal, and carefully secure the AMOLED display and display glass panel to the unibody chassis
*(not yet generated)*
