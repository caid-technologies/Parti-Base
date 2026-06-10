## Tools
- 3D printer (PLA filament)
- Soldering iron with fine tip
- Solder wire
- Wire strippers
- Flush cutters
- Small Phillips/flathead screwdriver
- Multimeter
- Heat shrink gun (optional, for insulated connections)
- Deburring tool (for 3D printed parts)
- Computer with USB-C cable (for ESP32-C3)

## Assumptions
- Basic 3D printing knowledge
- Basic soldering skills
- Familiarity with ESP32 development environment (e.g., Arduino IDE or ESP-IDF)
- Basic understanding of brushed motor control with MOSFETs
- Basic understanding of drone flight principles for calibration

## 1. Fabrication
### 1.1 Print the main drone frame
*(not yet generated)*

### 1.2 Deburr and clean the 3D printed frame
*(not yet generated)*

### 1.3 Test fit coreless motors into frame arms
*(not yet generated)*

## 2. Wiring
### 2.1 Solder individual SI2302 MOSFETs to motor negative leads and LiPo negative bus
**Solder motor negative leads to MOSFET drains, and all MOSFET sources to the LiPo negative.**
1. For each motor, solder the Negative lead of the Front Left Motor, Front Right Motor, Rear Left Motor, and Rear Right Motor to the Drain pin of its respective MOSFET (FL Motor MOSFET ESC, FR Motor MOSFET ESC, RL Motor MOSFET ESC, RR Motor MOSFET ESC).
2. Gather the Source pins from all four MOSFETs and create a common negative bus.
3. Solder the common negative bus from the MOSFET Sources directly to the JST_Negative terminal of the Main LiPo Battery.
4. Insulate all exposed solder joints with heat shrink tubing or electrical tape to prevent short circuits.

### 2.2 Connect all motor positive leads directly to the LiPo battery's positive terminal
**Solder all motor positive leads to the LiPo battery's positive terminal.**
1. Gather the Positive leads from the Front Left Motor, Front Right Motor, Rear Left Motor, and Rear Right Motor.
2. Twist the four motor positive leads together to form a common positive bus.
3. Solder this common positive motor bus directly to the JST_Positive terminal of the Main LiPo Battery.
4. Insulate the soldered connection with heat shrink tubing or electrical tape.

### 2.3 Wire the MPU6050 IMU to the ESP32-C3 (SCL to GPIO8, SDA to GPIO9, VCC to 3V3, GND to GND)
**Wire the Gyro/Accelerometer to the Flight Controller via I2C and power.**
1. Connect the SCL pin of the Gyro/Accelerometer to GPIO8 on the Flight Controller.
2. Connect the SDA pin of the Gyro/Accelerometer to GPIO9 on the Flight Controller.
3. Connect the VCC pin of the Gyro/Accelerometer to the 3V3 pin on the Flight Controller.
4. Connect the GND pin of the Gyro/Accelerometer to a GND pin on the Flight Controller.

### 2.4 Connect ESP32-C3 power (5V pin) and GND to the LiPo battery's positive and negative terminals
**Connect Flight Controller's 5V and GND to LiPo battery's positive and negative.**
1. Solder a wire from the JST_Positive terminal of the Main LiPo Battery to the 5V pin on the Flight Controller.
2. Solder a wire from the JST_Negative terminal of the Main LiPo Battery to a GND pin on the Flight Controller.
3. Ensure both soldered connections are secure and properly insulated.

### 2.5 Connect each MOSFET Gate pin to its respective ESP32-C3 GPIO pin (GPIO0, GPIO1, GPIO2, GPIO3) for PWM control
**Connect each MOSFET Gate to its dedicated Flight Controller GPIO pin.**
1. Solder a wire from the Gate pin of the FL Motor MOSFET ESC to GPIO0 on the Flight Controller.
2. Solder a wire from the Gate pin of the FR Motor MOSFET ESC to GPIO1 on the Flight Controller.
3. Solder a wire from the Gate pin of the RL Motor MOSFET ESC to GPIO2 on the Flight Controller.
4. Solder a wire from the Gate pin of the RR Motor MOSFET ESC to GPIO3 on the Flight Controller.
  > Tip: Keep these signal wires as short as possible to minimize electrical noise, and ensure good solder joints for reliable PWM control.

### 2.6 Perform continuity checks and verify for any short circuits on all power and data lines
**Verify all power and data line continuity and check for short circuits.**
1. Disconnect the Main LiPo Battery before performing any electrical tests.
2. Use a multimeter in continuity mode to confirm all positive power connections: from the Main LiPo Battery JST_Positive to the Flight Controller 5V pin, and to the Positive lead of each Front Left, Front Right, Rear Left, and Rear Right Motor.
3. Verify continuity for all ground connections: from the Main LiPo Battery JST_Negative to all Flight Controller GND pins, and to the Source pins of each FL, FR, RL, and RR Motor MOSFET ESC.
4. Confirm continuity for data lines: Flight Controller GPIO8 to Gyro/Accelerometer SCL, GPIO9 to Gyro/Accelerometer SDA, and Flight Controller GPIO0-GPIO3 to the Gate pins of their respective MOSFETs.
5. Switch the multimeter to resistance mode and check for short circuits (near 0 Ohms) between positive and negative terminals on the Main LiPo Battery, Flight Controller (5V/GND, 3V3/GND), and Gyro/Accelerometer (VCC/GND); all should read high resistance or open circuit.

## 3. Bring-up
### 3.1 Connect ESP32-C3 to computer and install necessary drivers
**Connect Flight Controller to PC and install USB drivers.**
1. Connect the Flight Controller (ESP32-C3 Super Mini) to your computer using a USB-C cable.
2. Check your operating system's Device Manager for new COM ports.
3. If a COM port is not detected, identify the USB-to-UART bridge chip on your Flight Controller (commonly CH340 or CP210x) and download/install the appropriate drivers from the chip manufacturer's website.
4. Verify the Flight Controller is recognized as a COM port in Device Manager once drivers are installed.

### 3.2 Upload initial firmware to ESP32-C3 for basic communication and sensor testing
**Upload basic firmware to the Flight Controller for initial testing.**
1. Open your preferred IDE (e.g., Arduino IDE, PlatformIO) and select the 'ESP32-C3 Dev Module' board.
2. Select the COM port identified in the previous step for the Flight Controller.
3. Upload a simple sketch, such as an I2C scanner or a basic 'blink' program if I2C devices are not yet initialized, to verify communication.
4. Confirm that the firmware upload completes successfully and the Flight Controller reboots as expected.
  > Tip: Ensure you have the ESP32 boards manager installed in your Arduino IDE or the correct platform installed in PlatformIO to recognize the ESP32-C3 board.

### 3.3 Verify MPU6050 IMU communication and data output via serial monitor
**Verify Gyro/Accelerometer communication and data output via serial monitor.**
1. Ensure the Flight Controller (ESP32-C3 Super Mini) is connected to your computer via USB.
2. Upload an I2C scanner sketch or a basic MPU6050 example sketch (e.g., from an MPU6050 library) to the Flight Controller.
3. Open the Serial Monitor in your IDE (e.g., Arduino IDE) and set the baud rate to 115200.
4. Observe the serial output: confirm that the I2C address for the Gyro/Accelerometer (MPU6050) is detected (typically 0x68 or 0x69).
5. If using an MPU6050 example, verify that gyroscope and accelerometer data values are streaming and respond to physical movement of the sensor.

### 3.4 Test individual motor functionality and PWM control using simple code sketches
**Test individual motor functionality and PWM control with simple code.**
1. **ENSURE ALL PROPELLERS ARE REMOVED** for safety before proceeding.
2. Write a simple Arduino sketch for the Flight Controller (ESP32-C3 Super Mini) that applies a low PWM signal (e.g., analogWrite(GPIO0, 50)) to GPIO0, leaving other motor GPIOs off.
3. Upload this sketch to the Flight Controller.
4. Carefully connect the Main LiPo Battery to power the system.
5. Observe the Front Left Motor: it should spin slowly. Vary the PWM value in the code (e.g., from 0 to 255) and re-upload to verify speed control for the Front Left Motor.
6. Repeat steps 2-5 for the Front Right Motor (GPIO1), Rear Left Motor (GPIO2), and Rear Right Motor (GPIO3) one by one, ensuring each motor responds correctly to PWM signals.
  > Tip: Always start with low PWM values and increase gradually to prevent sudden motor surges. Disconnect the LiPo battery before making any changes or re-uploading firmware.

### 3.5 Calibrate IMU sensor for accurate orientation data
**Calibrate Gyro/Accelerometer for accurate orientation data.**
1. Upload an MPU6050 calibration sketch (available in common libraries like 'MPU6050_light' or 'i2cdevlib') to the Flight Controller (ESP32-C3 Super Mini).
2. Place the Gyro/Accelerometer (MPU6050) module on a perfectly flat and stable surface, ensuring no movement, for initial accelerometer bias calibration.
3. Follow the instructions provided by the calibration sketch, which typically involves holding the drone completely still for a period, then slowly rotating it through all axes to calibrate the gyroscope.
4. Record the generated accelerometer and gyroscope offset values from the serial monitor.
5. Integrate these calibration offsets into your main flight control firmware to correct raw sensor readings.

## 4. Assembly
### 4.1 Mount the ESP32-C3 flight controller to the main drone frame using M2x6mm screws
*(not yet generated)*

### 4.2 Secure the MPU6050 IMU to the drone frame, ensuring correct orientation, using M2x6mm screws
*(not yet generated)*

### 4.3 Mount the 7x16mm coreless motors into their designated slots on the drone frame
*(not yet generated)*

### 4.4 Attach the CW and CCW propellers to their respective motors, ensuring correct rotation direction
*(not yet generated)*

### 4.5 Secure the 1S LiPo battery to the drone frame using the Velcro strap
*(not yet generated)*

### 4.6 Perform final checks of all connections, cable routing, and propeller security
*(not yet generated)*
