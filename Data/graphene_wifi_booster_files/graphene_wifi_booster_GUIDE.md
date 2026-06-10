## Tools
- 3D printer (PETG capable)
- Soldering iron with fine tip
- Solder (fine gauge)
- Wire strippers
- Flush cutters
- Small Phillips screwdriver (for M2 screws)
- Tweezers
- Multimeter
- USB-C power supply (for testing)

## Assumptions
- Familiarity with 3D printing and post-processing prints
- Basic soldering skills
- Understanding of fundamental electronics and circuit diagrams
- Ability to flash firmware to microcontrollers (e.g., via Arduino IDE or ESP-IDF)
- Access to a computer for firmware flashing and testing

## 1. Fabrication
### 1.1 3D print all mechanical components
**3D print all custom mechanical components as specified.**
1. Print the Enclosure Bottom Half and Enclosure Top Half using PETG filament, 25% infill, and a 0.2mm layer height.
2. Print the PCB Standoff for Main MCU, 2.4GHz Antenna Mount, 5GHz Antenna Mount, USB-C Jack Retainer, and Mode Button Actuator using PETG filament, 100% infill, and a 0.15mm layer height.
3. Print the RF Module Mount using PETG filament, 50% infill, and a 0.2mm layer height.
4. Print the Power Status LED Mount, WiFi 2.4GHz Status LED Mount, and WiFi 5GHz Status LED Mount using PETG filament, 30% infill, a 0.2mm layer height, and 4 perimeters.
  > Tip: Orient parts on the print bed to minimize support material and optimize surface finish for visible or mating surfaces.

### 1.2 Clean and deburr all 3D printed parts
**Clean and deburr all 3D-printed parts for proper fit and finish.**
1. Remove all support material from the Enclosure Bottom Half, Enclosure Top Half, PCB Standoff for Main MCU, RF Module Mount, 2.4GHz Antenna Mount, 5GHz Antenna Mount, USB-C Jack Retainer, Mode Button Actuator, Power Status LED Mount, WiFi 2.4GHz Status LED Mount, and WiFi 5GHz Status LED Mount.
2. Carefully trim or sand away any stringing, rough edges, or plastic imperfections from all surfaces using a hobby knife or fine-grit sandpaper.
3. Clear any debris from screw holes and openings, ensuring they are free from obstructions and correctly sized for component fit.
4. Wipe down all cleaned parts with a lint-free cloth to remove any dust or plastic particles.
  > Tip: Pay close attention to mating surfaces and critical dimensions during deburring to ensure components fit together smoothly during assembly.

### 1.3 Test fit the enclosure halves and mounts for proper alignment
**Test fit all 3D-printed mechanical components for alignment.**
1. Insert the RF Module Mount, 2.4GHz Antenna Mount, 5GHz Antenna Mount, and USB-C Jack Retainer into their designated slots or mounting points within the Enclosure Bottom Half.
2. Verify that the Mode Button Actuator and the Power Status LED Mount, WiFi 2.4GHz Status LED Mount, and WiFi 5GHz Status LED Mount snap into their respective openings on the Enclosure Top Half.
3. Carefully align and attempt to mate the Enclosure Top Half with the Enclosure Bottom Half, ensuring any screw holes or interlocking features align correctly.
4. Check for any tight spots, excessive gaps, or interferences that might prevent a smooth and complete closure of the enclosure. Adjust print settings or minor sanding may be needed if tolerances are too tight.
  > Tip: If components fit too loosely, consider adjusting print settings for dimensional accuracy or adding a thin layer of adhesive in final assembly. If too tight, use fine-grit sandpaper or a small file.

## 2. Wiring
### 2.1 Solder USB-C Power Jack to 5V Voltage Regulator VIN/GND
**Solder USB-C power input to 5V Voltage Regulator.**
1. Tin the VBUS and GND pads on the USB-C Power Input.
2. Tin the VIN (USB-C) and GND pads on the 5V Voltage Regulator.
3. Carefully solder a wire from the VBUS pin of the USB-C Power Input to the VIN (USB-C) pin of the 5V Voltage Regulator.
4. Solder a separate wire from the GND pin of the USB-C Power Input to the GND pin of the 5V Voltage Regulator.
5. Visually inspect all solder joints for good adhesion and no shorts.
  > Tip: Use appropriately gauged wires (e.g., 24 AWG) for power connections to handle potential current draws effectively.

### 2.2 Solder 5V Voltage Regulator VOUT to 3.3V Voltage Regulator VIN and Main MCU 5V/GND
**Connect 5V regulator output to 3.3V regulator and Main MCU.**
1. Solder a wire from the VOUT (5V) pin of the 5V Voltage Regulator to the VIN (5V) pin of the 3.3V Voltage Regulator.
2. Solder a wire from the GND pin of the 5V Voltage Regulator to the GND pin of the 3.3V Voltage Regulator.
3. Solder a wire from the VOUT (5V) pin of the 5V Voltage Regulator to the 5V power input of the Main WiFi Controller.
4. Solder a wire from the GND pin of the 5V Voltage Regulator to the GND pin of the Main WiFi Controller.
5. Visually inspect all soldered connections for clean joints and to ensure no short circuits are present.
  > Tip: Ensure adequate wire length for clean routing and strain relief, especially for the Main WiFi Controller which will be mounted later.

### 2.3 Solder 3.3V Voltage Regulator VOUT to RF Front-End Module VCC/GND and Power Status LED Anode/GND
**Solder 3.3V power to RF Module and Power Status LED.**
1. Solder a wire from the VOUT (3.3V) pin of the 3.3V Voltage Regulator to the VCC pin of the RF Front-End Module.
2. Solder a wire from the GND pin of the 3.3V Voltage Regulator to the GND pin of the RF Front-End Module.
3. Solder a current-limiting resistor (e.g., 220 Ohm for a standard LED) in series with the Anode pin of the Power Status LED.
4. Solder a wire from the free end of the resistor connected to the Power Status LED's Anode to the VOUT (3.3V) pin of the 3.3V Voltage Regulator.
5. Solder a wire from the Cathode pin of the Power Status LED to the GND pin of the 3.3V Voltage Regulator.
  > Tip: Ensure correct polarity when connecting the Power Status LED (Anode to positive, Cathode to ground via resistor) to prevent damage.

### 2.4 Solder Main MCU GPIOs to RF Front-End Module CTL1/CTL2/RF_OUT and Graphene Antennas
**Solder Main WiFi Controller GPIOs to RF Module and Graphene Antennas.**
1. Solder a wire from the Main WiFi Controller's GPIO_RF_CTL1 pin to the RF Front-End Module's CTL1 pin.
2. Solder a wire from the Main WiFi Controller's GPIO_RF_CTL2 pin to the RF Front-End Module's CTL2 pin.
3. Solder a wire from the RF Front-End Module's RF_OUT (To ESP32) pin to the Main WiFi Controller's RF_Module_In pin.
4. Solder a short RF coaxial cable or appropriate trace from the Main WiFi Controller's RF_2_4GHz_OUT pin to the Graphene Antenna 2.4GHz's Antenna_Feed (2.4GHz) pin.
5. Solder a short RF coaxial cable or appropriate trace from the Main WiFi Controller's RF_5GHz_OUT pin to the Graphene Antenna 5GHz's Antenna_Feed (5GHz) pin.
6. Solder a short RF coaxial cable or appropriate trace from the RF Front-End Module's RF_IN (To Antenna) pin to the Graphene Antenna 2.4GHz's Antenna_Feed (2.4GHz) and Graphene Antenna 5GHz's Antenna_Feed (5GHz) if a diplexer is integrated or separate paths are used.
  > Tip: For RF connections, use very short, impedance-matched coaxial cables or carefully designed PCB traces to minimize signal loss and maximize booster performance.

### 2.5 Solder RF Front-End Module RF_IN to Graphene Antennas
*(not yet generated)*

### 2.6 Solder Main MCU GPIOs to WiFi 2.4GHz and 5GHz Status LEDs Anodes, connect LED Cathodes to Main MCU GND
**Wire WiFi status LEDs to Main MCU GPIOs and GND.**
1. Identify the Anode (longer leg) and Cathode (shorter leg, flat edge) of both the WiFi 2.4GHz Status LED and WiFi 5GHz Status LED.
2. Solder a suitable current-limiting resistor (e.g., 220-470 Ohm) in series with the Anode of the WiFi 2.4GHz Status LED.
3. Connect the resistor-equipped Anode of the WiFi 2.4GHz Status LED to the Main WiFi Controller's GPIO_LED_2_4GHz pin, and its Cathode to the Main WiFi Controller's GND pin.
4. Repeat the process: solder a current-limiting resistor to the Anode of the WiFi 5GHz Status LED.
5. Connect the resistor-equipped Anode of the WiFi 5GHz Status LED to the Main WiFi Controller's GPIO_LED_5GHz pin, and its Cathode to the Main WiFi Controller's GND pin.
6. Perform a visual inspection to ensure correct polarity, secure solder joints, and no short circuits between pins.
  > Tip: Always use a current-limiting resistor with LEDs to prevent damage to the LED and the microcontroller's GPIO pin. The exact resistor value depends on the LED's forward voltage and the MCU's output voltage.

### 2.7 Solder Mode Selection Button to Main MCU GPIO and GND
**Solder Mode Selection Button to Main MCU GPIO and GND.**
1. Identify the two active pins (Switch_1, Switch_2) on the Mode Selection Button.
2. Solder a wire from one active pin (Switch_1) of the Mode Selection Button to the GPIO (Button) pin on the Main WiFi Controller.
3. Solder a wire from the other active pin (Switch_2) of the Mode Selection Button to a GND pin on the Main WiFi Controller.
4. Inspect all solder connections to ensure they are firm, clean, and free of shorts.
  > Tip: The Main WiFi Controller's firmware should configure the GPIO (Button) pin with an internal pull-up or pull-down resistor to ensure a defined state when the button is not pressed.

### 2.8 Perform continuity checks on all power and ground connections with a multimeter
**Verify continuity for all power and ground connections using a multimeter.**
1. Set your multimeter to continuity mode.
2. Confirm continuity between the USB-C Power Input's VBUS pin and the 5V Voltage Regulator's VIN pin.
3. Confirm continuity between the 5V Voltage Regulator's VOUT pin and the 3.3V Voltage Regulator's VIN pin, as well as the Main WiFi Controller's 5V input.
4. Confirm continuity between the 3.3V Voltage Regulator's VOUT pin and the RF Front-End Module's VCC pin, and the Power Status LED's Anode (through its current-limiting resistor, if present).
5. Check all ground connections by confirming continuity between the USB-C Power Input's GND pin and the GND pins of the 5V Voltage Regulator, 3.3V Voltage Regulator, Main WiFi Controller, RF Front-End Module, and the Cathodes of all Status LEDs and Mode Selection Button's Switch_2 pin.

## 3. Bring-up
### 3.1 Connect USB-C power and verify 5V and 3.3V rails with multimeter
**Verify 5V and 3.3V power rails using a multimeter.**
1. Connect a USB-C power source to the USB-C Power Input.
2. Set your multimeter to measure DC voltage.
3. Place the multimeter's positive probe on the VOUT (5V) pin of the 5V Voltage Regulator and the negative probe on its GND pin; verify the reading is approximately 5V.
4. Place the multimeter's positive probe on the VOUT (3.3V) pin of the 3.3V Voltage Regulator and the negative probe on its GND pin; verify the reading is approximately 3.3V.
5. If voltage readings are incorrect, immediately disconnect power and re-check all power wiring for shorts or open circuits.
  > Tip: Always verify power rails before connecting sensitive components like the Main WiFi Controller or RF Front-End Module to prevent damage from overvoltage or reverse polarity.

### 3.2 Connect Main MCU to computer and flash initial test firmware
**Flash initial test firmware to Main WiFi Controller.**
1. Connect the Main WiFi Controller to your computer using a USB-C cable.
2. Ensure you have the necessary development environment (e.g., Arduino IDE with ESP32-S3 board support) and drivers installed.
3. Open a basic test firmware (e.g., a simple blink sketch or a custom 'hello world' program that initializes Wi-Fi) in your chosen IDE.
4. Select the correct board type (ESP32-S3 Dev Module) and the associated serial port in the IDE's tools menu.
5. Initiate the firmware upload process and confirm that the firmware successfully uploads to the Main WiFi Controller.

### 3.3 Test Power Status LED functionality via firmware
**Verify Power Status LED functionality using firmware.**
1. Connect the Main WiFi Controller to your computer via its USB-C port.
2. Upload a test firmware to the Main WiFi Controller that configures the GPIO pin connected to the Power Status LED as an output and cycles the LED on and off (e.g., a 1-second blink pattern).
3. Observe the Power Status LED. It should illuminate and blink according to the firmware pattern.
4. If the LED does not function as expected, verify the correct GPIO pin assignment in the firmware and check the physical wiring of the LED, including its current-limiting resistor, to the Main WiFi Controller.
  > Tip: Ensure the polarity of the Power Status LED is correct; the Anode (longer leg, usually connected to GPIO via resistor) should be connected differently from the Cathode (shorter leg, usually connected to GND).

### 3.4 Test WiFi 2.4GHz and 5GHz Status LEDs functionality via firmware
**Test WiFi status LEDs functionality using a test firmware sketch.**
1. Upload a basic firmware sketch to the Main WiFi Controller that successively illuminates the WiFi 2.4GHz Status LED and the WiFi 5GHz Status LED, using GPIO_LED_2_4GHz and GPIO_LED_5GHz respectively.
2. Observe if the blue WiFi 2.4GHz Status LED illuminates when its corresponding GPIO pin is set HIGH.
3. Observe if the yellow WiFi 5GHz Status LED illuminates when its corresponding GPIO pin is set HIGH.
4. Verify that both LEDs turn OFF when their respective GPIO pins are set LOW.
  > Tip: Ensure current-limiting resistors are properly connected to the LEDs to prevent damage to the Main WiFi Controller's GPIO pins or the LEDs themselves.

### 3.5 Test Mode Selection Button response via firmware serial output
**Test Mode Selection Button input with serial feedback.**
1. Connect the Main WiFi Controller to your computer via USB-C.
2. Upload a firmware sketch that initializes the GPIO (Button) pin on the Main WiFi Controller as an input (with an internal pull-up resistor if required by your button wiring) and prints 'Button Pressed' or 'Button Released' to the serial console upon state change.
3. Open the serial monitor in your IDE (e.g., Arduino Serial Monitor) and ensure the baud rate matches your firmware setting.
4. Press and release the Mode Selection Button multiple times.
5. Verify that the serial monitor displays messages indicating button presses and releases, confirming correct functionality.
  > Tip: Ensure the button is debounced in your firmware to prevent multiple readings from a single physical press, which can lead to unexpected behavior.

### 3.6 Verify basic communication with RF Front-End Module (e.g., register reads/writes)
*(not yet generated)*

## 4. Assembly
### 4.1 Mount Main MCU onto PCB Standoffs in the Enclosure Bottom Half using M2 screws
*(not yet generated)*

### 4.2 Mount RF Front-End Module into RF Module Mount, then secure mount to Enclosure Bottom Half
*(not yet generated)*

### 4.3 Mount Graphene 2.4GHz and 5GHz Antennas into their respective mounts, then secure mounts to Enclosure Bottom Half
*(not yet generated)*

### 4.4 Mount USB-C Power Input into USB-C Jack Retainer, then secure retainer to Enclosure Bottom Half
*(not yet generated)*

### 4.5 Insert Mode Selection Button into Enclosure Bottom Half and attach Button Actuator to Enclosure Top Half (snap-fit over button)
*(not yet generated)*

### 4.6 Install Power and WiFi Status LEDs into their respective mounts, then snap-fit mounts into Enclosure Top Half
**Install Status LEDs into mounts, then snap-fit into Enclosure Top Half.**
1. Carefully insert the green Power Status LED into the Power Status LED Mount.
2. Insert the blue WiFi 2.4GHz Status LED into the WiFi 2.4GHz Status LED Mount.
3. Insert the yellow WiFi 5GHz Status LED into the WiFi 5GHz Status LED Mount.
4. Snap-fit the Power Status LED Mount, WiFi 2.4GHz Status LED Mount, and WiFi 5GHz Status LED Mount into their corresponding openings on the Enclosure Top Half, ensuring they are flush.

### 4.7 Route and organize all internal wiring to prevent strain and interference
*(not yet generated)*

### 4.8 Close the Enclosure Top Half onto the Enclosure Bottom Half and secure with M2 screws
*(not yet generated)*

### 4.9 Perform final system power-on and functional test of all features
*(not yet generated)*
