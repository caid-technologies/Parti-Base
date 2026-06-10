## Tools
- Drill and drill bits (appropriate for enclosure materials and cable glands)
- M12 and M16 wrench/spanner (for cable glands)
- Wire strippers and cutters
- Screwdrivers (Phillips and flathead for terminal blocks and mounting)
- Multimeter
- Soldering iron (optional, if ESP32 headers are not pre-soldered)
- Heat shrink tubing and heat gun (if using for connections)
- Measuring tape or ruler
- Marker pen
- Safety glasses

## Assumptions
- Basic electrical wiring knowledge and safety practices, especially with AC power
- Familiarity with ESP32 board and flashing firmware
- Access to a computer with a suitable IDE (e.g., Arduino IDE, PlatformIO) for ESP32 programming
- Basic understanding of hydroponic system components and their function
- 12V DC power supply available for testing (e.g., the main_power_adapter)

## 1. Fabrication
### 1.1 Mark and drill holes for cable glands on the main IP65 Junction Box
**Mark and drill cable gland holes in the IP65 Junction Box.**
1. Using the Cable Gland M12 (Power) and Cable Gland M16 (Actuators/Sensors) as templates, mark the center points for each gland on the IP65 Junction Box enclosure.
2. Drill pilot holes using a small drill bit (e.g., 3mm) at each marked location.
3. Enlarge the power cable gland hole to 15.2mm for the M12 gland.
4. Enlarge the actuator and sensor cable gland holes to 18.5mm for the M16 glands.
5. Deburr all drilled holes thoroughly to ensure a smooth, clean edge for proper cable gland seating and IP65 seal integrity.

### 1.2 Mount the power DC Input Terminal Block and 12V to 5V DC-DC Converter inside the main junction box
**Mount power components inside the main IP65 junction box.**
1. Position the DC Input Terminal Block and the 12V to 5V DC-DC Converter inside the IP65 Junction Box, ensuring adequate space for wiring and cable glands.
2. Mark the mounting hole locations for both components on the internal mounting points of the enclosure.
3. Drill pilot holes for mounting screws at the marked locations, suitable for small self-tapping plastic screws (e.g., M2 or M2.5).
4. Secure the DC Input Terminal Block using appropriate screws, ensuring it is firmly attached.
5. Secure the 12V to 5V DC-DC Converter using appropriate screws, ensuring it is also firmly attached and stable.

### 1.3 Mount the ESP32 Main Controller, 8-Channel Relay Board, and ADS1115 ADC Module inside the main junction box
**Mount the main controller, relay board, and ADC module in the IP65 junction box.**
1. Determine optimal placement for the Main Controller (ESP32 NodeMCU), 8-Channel Optocoupled Relay Board, and 16-bit ADC Module within the IP65 Junction Box enclosure, considering wire routing and access to ports.
2. Mark the mounting hole locations for each component on the internal surface of the IP65 Junction Box.
3. Drill pilot holes, then 3mm clearance holes, at each marked mounting point for M3 standoffs.
4. Install M3 plastic standoffs at each drilled location to elevate the circuit boards.
5. Secure the Main Controller (ESP32 NodeMCU), 8-Channel Optocoupled Relay Board, and 16-bit ADC Module to their respective standoffs using M3 screws.

### 1.4 Mark and drill holes for cable glands on the small IP65 Junction Box (Valves)
**Mark and drill cable gland holes in the small IP65 Junction Box (Valves).**
1. Using the Cable Gland M16 (Valve Box) as a template, mark the center points for each gland on the IP65 Junction Box (Valves) enclosure.
2. Drill pilot holes using a small drill bit (e.g., 3mm) at each marked location.
3. Enlarge the cable gland holes to 18.5mm for the M16 glands.
4. Deburr all drilled holes thoroughly to ensure a smooth, clean edge for proper cable gland seating and IP65 seal integrity.

### 1.5 Mount Solenoid Valves 1-3 inside the small IP65 Junction Box (Valves)
**Mount solenoid valves inside the small IP65 Junction Box.**
1. Determine optimal placement for Solenoid Valve 1 (Freshwater Inlet), Solenoid Valve 2 (Wastewater Outlet), and Solenoid Valve 3 (Spare) inside the IP65 Junction Box (Valves) to accommodate plumbing and wiring.
2. Mark and drill mounting holes for each solenoid valve on the enclosure surface (e.g., use M3 or M4 screws for mounting).
3. Secure Solenoid Valve 1 (Freshwater Inlet) to the enclosure using appropriate screws.
4. Secure Solenoid Valve 2 (Wastewater Outlet) to the enclosure using appropriate screws.
5. Secure Solenoid Valve 3 (Spare) to the enclosure using appropriate screws.

### 1.6 Secure cable glands into all drilled holes on both IP65 junction boxes
**Secure all cable glands into the main and valve IP65 junction boxes.**
1. Insert the M12 Power Cable Gland into its hole on the main IP65 Junction Box Enclosure, ensuring the sealing washer is correctly placed on the outside, and tighten the securing nut from the inside.
2. Insert the M16 Actuator Cable Gland and M16 Sensor Cable Gland into their respective holes on the main IP65 Junction Box Enclosure, securing each with its nut and sealing washer.
3. Insert the M16 Valve Box Cable Gland into its hole on the IP65 Junction Box (Valves), securing it with its nut and sealing washer.
4. Carefully tighten all cable gland nuts using a wrench until they are snug and form a watertight seal, but do not overtighten.

## 2. Wiring
### 2.1 Wire the main 12V power distribution from the DC Input Terminal Block to the 12V to 5V DC-DC Converter and all 12V actuators (pumps, solenoid valves, DC-AC Inverter)
**Wire 12V power from the terminal block to the DC-DC converter and all 12V devices.**
1. Connect the 'Screw Terminal +' of the DC Input Terminal Block to the 'Input 12V+' of the 12V to 5V DC-DC Converter.
2. Connect the 'Screw Terminal -' of the DC Input Terminal Block to the 'Input GND-' of the 12V to 5V DC-DC Converter.
3. Connect the 'Screw Terminal +' of the DC Input Terminal Block to the positive leads (12V+) of Solenoid Valve 1, Solenoid Valve 2, Solenoid Valve 3, Mini Water Pump 1, and Mini Water Pump 2.
4. Connect the 'Screw Terminal +' of the DC Input Terminal Block to the '12V Input +' of the 12V DC to 220V AC Inverter.
5. Connect the 'Screw Terminal -' of the DC Input Terminal Block to the '12V Input -' of the 12V DC to 220V AC Inverter.

### 2.2 Wire the 5V power distribution from the DC-DC Converter to the ESP32, Relay Board, ADS1115, pH Sensor, TDS Sensor, Water Flow Sensor, and Peristaltic Micropump
**Wire 5V power and ground from the DC-DC Converter to specified modules.**
1. Connect the 'Output 5V+' pin of the 12V to 5V DC-DC Converter to the 'Vin' pin of the Main Controller (ESP32 NodeMCU), the 'VCC (5V)' pin of the 8-Channel Optocoupled Relay Board, the 'VDD (5V)' pin of the 16-bit ADC Module, the 'VCC (5V)' pin of the pH Sensor Module, the 'VCC (5V)' pin of the TDS Sensor Module, the 'VCC (5V)' pin of the Water Flow Sensor, and the '5V+' pin of the Peristaltic Micropump.
2. Connect the 'Output GND-' pin of the 12V to 5V DC-DC Converter to the 'GND' pin of the Main Controller (ESP32 NodeMCU), the 'GND' pin of the 8-Channel Optocoupled Relay Board, the 'GND' pin of the 16-bit ADC Module, the 'GND' pin of the pH Sensor Module, the 'GND' pin of the TDS Sensor Module, the 'GND' pin of the Water Flow Sensor, and the 'GND-' pin of the Peristaltic Micropump.

### 2.3 Connect ESP32 GPIOs to the Relay Board input pins (IN1-IN6) for controlling actuators
**Connect ESP32 GPIOs to the 8-Channel Relay Board input pins.**
1. Connect ESP32's GPIO 12 to the Relay Board's IN1 pin using a jumper wire.
2. Connect ESP32's GPIO 13 to the Relay Board's IN2 pin using a jumper wire.
3. Connect ESP32's GPIO 14 to the Relay Board's IN3 pin using a jumper wire.
4. Connect ESP32's GPIO 25 to the Relay Board's IN4 pin using a jumper wire.
5. Connect ESP32's GPIO 26 to the Relay Board's IN5 pin using a jumper wire.
6. Connect ESP32's GPIO 27 to the Relay Board's IN6 pin using a jumper wire.
  > Tip: Ensure correct pin orientation for jumper wires, connecting the ESP32 GPIO to the corresponding 'IN' pin on the relay module. Double-check to avoid accidental shorts or incorrect control signals.

### 2.4 Wire the I2C bus between ESP32 (SDA, SCL) and the ADS1115 ADC Module (SDA, SCL)
*(not yet generated)*

### 2.5 Connect analog sensor outputs (pH, TDS) to ADS1115 ADC input channels (A0, A1), and configure ADS1115 ADDR pin
**Wire pH and TDS sensor analog outputs to ADS1115 ADC, configure ADDR pin.**
1. Connect the 'Analog Output' pin of the pH Sensor Module to the 'A0' input of the 16-bit ADC Module.
2. Connect the 'Analog Output' pin of the TDS Sensor Module to the 'A1' input of the 16-bit ADC Module.
3. Connect the 'ADDR' pin of the 16-bit ADC Module to its 'GND' pin to set the I2C address to 0x48.

### 2.6 Wire the Signal and GND pins for the Water Flow Sensor and both Float Sensors to ESP32 GPIOs
**Wire sensors' Signal and GND pins to the ESP32 main controller.**
1. Connect the Signal Output pin of the Water Flow Sensor to GPIO 23 on the ESP32 Main Controller.
2. Connect the Signal pin of the Water Level Float Sensor (Growth Tube) to GPIO 17 on the ESP32 Main Controller.
3. Connect the Signal pin of the Water Level Float Sensor (Reservoir) to GPIO 16 on the ESP32 Main Controller.
4. Connect the GND pins of the Water Flow Sensor, Water Level Float Sensor (Growth Tube), and Water Level Float Sensor (Reservoir) to a common GND pin on the ESP32 Main Controller.

### 2.7 Install flyback diodes across the coils of all solenoid valves and mini water pumps, observing polarity
**Install flyback diodes across the coils of all solenoid valves and mini water pumps.**
1. For each Solenoid Valve (Freshwater Inlet, Wastewater Outlet, Spare), connect the Anode lead of its respective Flyback Diode to the GND- terminal of the valve.
2. For each Solenoid Valve, connect the Cathode lead of its respective Flyback Diode to the 12V+ terminal of the valve.
3. For each Mini Water Pump (Main Ebb & Flow Flood, Recirculation), connect the Anode lead of its respective Flyback Diode to the GND- terminal of the pump.
4. For each Mini Water Pump, connect the Cathode lead of its respective Flyback Diode to the 12V+ terminal of the pump.
5. Secure all diode connections, preferably by soldering and insulating with heat shrink tubing, or using appropriate crimp terminals.
  > Tip: Ensure correct diode polarity for each component. Reversing polarity can cause a short circuit or damage the diode and the driving circuit.

### 2.8 Wire the 220V AC Return Pump to the 12V DC to 220V AC Inverter output
**Wire the 220V AC Return Pump to the AC Inverter output.**
1. Identify the 220V AC Live and Neutral wires extending from the Return Pump (220V AC).
2. Connect the Return Pump's 220V AC Live wire to one of the 220V AC Output terminals on the 12V DC to 220V AC Inverter.
3. Connect the Return Pump's 220V AC Neutral wire to the remaining 220V AC Output terminal on the 12V DC to 220V AC Inverter.
4. Ensure all 220V AC connections are securely terminated, using heat shrink tubing or appropriate connectors for insulation.

## 3. Bring-up
### 3.1 Perform continuity checks on all power and ground lines to prevent shorts
**Perform multimeter continuity checks on all power and ground lines.**
1. Set a multimeter to continuity mode.
2. Verify there is no continuity (short circuit) between the 'Screw Terminal +' and 'Screw Terminal -' on the DC Input Terminal Block.
3. Verify there is no continuity (short circuit) between the 'Input 12V+' and 'Input GND-' pins of the 12V to 5V DC-DC Converter.
4. Verify there is no continuity (short circuit) between the 'Output 5V+' and 'Output GND-' pins of the 12V to 5V DC-DC Converter.
5. Check for continuity between the 'Output 5V+' from the 12V to 5V DC-DC Converter and the 'Vin' pin on the Main Controller (ESP32 NodeMCU), and 'VCC (5V)' on the 8-Channel Optocoupled Relay Board, and 'VDD (5V)' on the 16-bit ADC Module, ensuring proper 5V distribution.
6. Check for continuity between the 'Output GND-' from the 12V to 5V DC-DC Converter and the 'GND' pins of the Main Controller (ESP32 NodeMCU), 8-Channel Optocoupled Relay Board, and 16-bit ADC Module, confirming ground connections.

### 3.2 Apply 12V power and verify 5V output from the DC-DC converter using a multimeter
**Verify 5V output from DC-DC converter after applying 12V power.**
1. Connect the Main AC/DC Power Adapter's male jack to the DC Input Terminal Block's female jack.
2. Plug the Main AC/DC Power Adapter into a wall outlet to apply 12V power.
3. Set a multimeter to DC voltage measurement mode.
4. Carefully probe the 'Input 12V+' and 'Input GND-' terminals of the 12V to 5V DC-DC Converter to confirm approximately 12V input.
5. Probe the 'Output 5V+' and 'Output GND-' terminals of the 12V to 5V DC-DC Converter to verify a stable 5V output.

### 3.3 Connect ESP32 to computer, verify driver installation, and upload basic 'blink' sketch to confirm functionality
**Connect ESP32 to computer, verify drivers, and upload 'blink' sketch.**
1. Connect the ESP32 Main Controller to your computer using a USB cable.
2. Verify that the necessary USB-to-serial drivers (e.g., CP210x or CH340) are correctly installed and that the ESP32 is recognized as a COM port in your system's device manager.
3. Open your Arduino IDE (or preferred ESP32 development environment), select 'ESP32 Dev Module' as the board, and choose the correct COM port.
4. Upload a basic 'blink' example sketch to the ESP32 Main Controller to confirm successful firmware flashing and operation.
5. Observe the onboard LED on the ESP32 Main Controller; it should begin blinking, indicating successful program execution.

### 3.4 Upload I2C scanner sketch to ESP32 and verify detection of the ADS1115 module
**Upload an I2C scanner sketch to ESP32 and verify ADS1115 detection.**
1. Connect the Main Controller (ESP32 NodeMCU) to your computer via USB cable.
2. Open the Arduino IDE, select the correct board (ESP32 Dev Module) and COM port.
3. Upload a standard I2C scanner sketch (available in examples or online) to the ESP32.
4. Open the Serial Monitor and observe the output to confirm that the 16-bit ADC Module (ADS1115) is detected at I2C address 0x48.

### 3.5 Develop and upload initial firmware for controlling relays, testing each actuator individually
**Develop firmware to control and test each relay-actuated component.**
1. Connect the Main Controller (ESP32 NodeMCU) to your computer via USB for programming.
2. Using your preferred IDE (e.g., Arduino IDE with ESP32 board support), write firmware to sequentially activate and deactivate each relay channel (IN1 through IN6) for a short duration.
3. Upload the developed firmware to the Main Controller (ESP32 NodeMCU).
4. Observe and verify that Solenoid Valve 1 (Freshwater Inlet), Solenoid Valve 2 (Wastewater Outlet), Solenoid Valve 3 (Spare), Mini Water Pump 1 (Main Ebb & Flow Flood), Mini Water Pump 2 (Recirculation), and the Peristaltic Micropump (Fertilizer Dosing) activate and deactivate correctly when their corresponding relay channels are triggered. Also test the 12V DC to 220V AC Inverter (and subsequently the Return Pump) if connected to a relay channel (e.g. IN7).
  > Tip: Start with simple 'blink' style code for each relay to confirm basic functionality before integrating complex logic. Isolate testing to one actuator at a time to simplify debugging.

### 3.6 Test analog sensor readings (pH, TDS) through the ADS1115 and verify digital sensor inputs (water flow, float sensors) on the ESP32
**Verify analog and digital sensor inputs to ESP32 via ADS1115 and direct GPIO.**
1. Upload a basic test firmware to the ESP32 Main Controller that initializes I2C for the 16-bit ADC Module (ADS1115) and reads from its A0 and A1 channels.
2. Submerge the pH Sensor Module's electrode and TDS Sensor Module's probe into known reference solutions (e.g., distilled water, calibration fluids), and verify the reported analog values on the serial monitor of the ESP32.
3. Verify that the 16-bit ADC Module (ADS1115) is recognized on the I2C bus (address 0x48).
4. Manually trigger the Water Level Float Sensor (Growth Tube) and Water Level Float Sensor (Reservoir) by changing their orientation or submerging them, verifying the corresponding digital state changes on ESP32's GPIO 17 and GPIO 16 via the serial monitor.
5. Induce a small amount of water flow through the Water Flow Sensor and monitor for pulse readings or frequency changes on ESP32's GPIO 23, verifying its functionality.

## 4. Assembly
### 4.1 Route all external sensor and actuator cables through the appropriate cable glands into the main IP65 junction box
**Route all external sensor and actuator cables through main IP65 junction box cable glands.**
1. Feed the cables from the pH Sensor Module, TDS Sensor Module, Water Flow Sensor, Water Level Float Sensor (Growth Tube), and Water Level Float Sensor (Reservoir) through the Cable Gland M16 (Sensors) into the main IP65 Junction Box Enclosure.
2. Feed the cables from Mini Water Pump 1 (Main Ebb & Flow Flood), Mini Water Pump 2 (Recirculation), and Peristaltic Micropump (Fertilizer Dosing) through the Cable Gland M16 (Actuators) into the main IP65 Junction Box Enclosure.
3. Do not tighten the cable glands yet, leave enough slack for internal connections.

### 4.2 Route cables for the solenoid valves from the small IP65 Valve Box to the main IP65 Junction Box
**Route solenoid valve cables from the valve box to the main junction box.**
1. Gather the power and control cables for Solenoid Valve 1, Solenoid Valve 2, and Solenoid Valve 3.
2. Feed these grouped cables through the Cable Gland M16 (Valve Box) installed on the IP65 Junction Box (Valves).
3. Feed the same grouped cables through the Cable Gland M16 (Actuators) installed on the main IP65 Junction Box Enclosure.
4. Pull sufficient cable slack through both glands to allow for internal wiring, then gently tighten the compression nuts on both the Cable Gland M16 (Valve Box) and Cable Gland M16 (Actuators) to provide strain relief.

### 4.3 Organize and secure all internal wiring using cable ties or clips for strain relief and neatness
**Organize and secure all internal wiring within both IP65 junction boxes.**
1. Within the main IP65 Junction Box Enclosure, bundle similar wires (e.g., power, data, sensor leads) using cable ties or adhesive clips.
2. Route bundled wires along the interior walls or designated channels, securing them to prevent interference and provide strain relief at connection points.
3. Ensure adequate slack in wires connected to moving parts or components that may need future access, such as the ESP32 and relay board terminals.
4. Repeat the bundling and securing process for all wiring within the IP65 Junction Box (Valves), paying special attention to wires leading to the solenoid valves.
5. Verify that no wires are pinched, taut, or interfere with the proper closure of either enclosure lid.

### 4.4 Submerge the pH and TDS sensors and Mini Water Pump 1 into the Water Reservoir Tank
**Submerge pH and TDS sensors and Mini Water Pump 1 into the Water Reservoir Tank.**
1. Place the pH Sensor Module with Electrode into the Water Reservoir Tank, ensuring the electrode and module are fully submerged in the water as per design.
2. Place the TDS Sensor Module with Probe into the Water Reservoir Tank, ensuring the probe and module are fully submerged in the water.
3. Position the Mini Water Pump 1 (Main Ebb & Flow Flood) at the bottom of the Water Reservoir Tank, ensuring it is fully submerged and stable for operation.
4. Route the cables for the pH Sensor, TDS Sensor, and Mini Water Pump 1 through the Cable Gland M16 (Reservoir Sensors) installed on the reservoir box, tightening the gland to create a watertight seal around the cables.

### 4.5 Connect the main AC/DC Power Adapter to the DC Input Terminal Block, ensuring proper strain relief at the cable gland
**Connect power adapter to terminal block with strain relief.**
1. Plug the DC 5.5x2.1mm male jack of the Main AC/DC Power Adapter into the DC 5.5x2.1mm female jack of the DC Input Terminal Block.
2. Feed the cable from the Main AC/DC Power Adapter through the Cable Gland M12 (Power).
3. Tighten the compression nut of the Cable Gland M12 (Power) until the cable is securely gripped, providing strain relief and maintaining the IP65 seal.

### 4.6 Perform final system power-up and verify all components respond correctly to control signals
**Perform final system power-up and verify all components function correctly.**
1. Connect the Main AC/DC Power Adapter's male jack to the DC Input Terminal Block's female jack.
2. Power on the system and observe the Main Controller (ESP32 NodeMCU) and 8-Channel Optocoupled Relay Board for proper power indication (e.g., power LEDs illuminated).
3. Using a test firmware, sequentially activate each relay connected to Solenoid Valve 1, Solenoid Valve 2, Solenoid Valve 3, Mini Water Pump 1, Mini Water Pump 2, Peristaltic Micropump, and the 12V DC to 220V AC Inverter (which will power the Return Pump), verifying audible and/or visual confirmation of activation.
4. Monitor the serial output or a display for stable readings from the pH Sensor Module, TDS Sensor Module, Water Flow Sensor, Water Level Float Sensor (Growth Tube), and Water Level Float Sensor (Reservoir).
5. Inspect all wiring for secure connections and proper routing, ensuring no wires are pinched or under strain, and ensure all IP65 enclosures are properly closed and sealed.

### 4.7 Secure all enclosure lids, ensuring IP65 rating is maintained with proper gaskets and screws
**Secure all enclosure lids, ensuring IP65 rating is maintained.**
1. Ensure that the rubber gaskets are correctly seated and undamaged on the main IP65 Junction Box Enclosure and the IP65 Junction Box (Valves).
2. Carefully align the lid of the main IP65 Junction Box Enclosure with its base and begin inserting the lid screws.
3. Tighten the screws on the main IP65 Junction Box Enclosure lid in a diagonal or cross pattern to ensure even pressure and a watertight seal.
4. Align the lid of the IP65 Junction Box (Valves) with its base and insert the lid screws.
5. Tighten the screws on the IP65 Junction Box (Valves) lid in a diagonal or cross pattern to ensure an even and secure seal.
