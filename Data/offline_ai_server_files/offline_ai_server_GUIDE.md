## Tools
- 3D printer (PETG capable)
- Soldering iron with fine tip
- Screwdriver set (Phillips head for M2/M3)
- Wire strippers/cutters
- Multimeter
- Tweezers or small pliers

## Assumptions
- Basic 3D printing knowledge
- Basic soldering skills for electronics
- Familiarity with ESP32-S3 development environment (e.g., ESP-IDF, PlatformIO)
- Access to a computer for flashing firmware and model deployment

## 1. Fabrication
### 1.1 3D print the server enclosure base
**3D print the Server Enclosure Base.**
1. Load PETG filament into your 3D printer.
2. Prepare the 3D model for the Server Enclosure Base, ensuring proper orientation for stability.
3. Set print parameters: 0.2mm layer height, 20% infill.
4. Initiate the 3D printing process for the Server Enclosure Base.
5. Once cooled, carefully remove the printed part from the build plate.
6. Clean any remaining support structures and deburr sharp edges.
  > Tip: Proper bed adhesion is crucial when printing PETG to prevent warping on the relatively large flat surface of the enclosure base.

### 1.2 3D print the server enclosure lid
**3D print the Server Enclosure Lid.**
1. Load PETG filament into your 3D printer.
2. Prepare the 3D model for the Server Enclosure Lid, ensuring optimal orientation for aesthetic finish.
3. Set print parameters: 0.2mm layer height, 20% infill.
4. Initiate the 3D printing process for the Server Enclosure Lid.
5. Once cooled, carefully remove the printed part from the build plate.
6. Clean any remaining support structures and deburr sharp edges.
  > Tip: Orienting the lid with the top surface facing the build plate (if possible and without requiring excessive supports) can yield a smoother exterior finish for the enclosure.

### 1.3 Install M3 heat set inserts into the enclosure base
**Install four M3 brass heat set inserts into the Server Enclosure Base.**
1. Heat your soldering iron to approximately 200-220°C (suitable for PETG and brass).
2. Place one M3 Heat Set Insert into a designated mounting hole on the Server Enclosure Base.
3. Carefully align the hot soldering iron tip with the insert and apply gentle, steady downward pressure.
4. Allow the insert to melt into the PETG plastic until it is flush or slightly recessed with the surface.
5. Remove the soldering iron and let the plastic cool and set around the insert for a few seconds.
6. Repeat for the remaining three M3 Heat Set Inserts.
  > Tip: Ensure each M3 Heat Set Insert is inserted straight and fully, as an uneven or partially inserted insert can cause difficulty when attaching the lid.

### 1.4 Test fit the ESP32-S3 and MicroSD module into the base to ensure clearances
**Test fit the Main AI Controller and MicroSD Card Module into the enclosure base.**
1. Carefully place the Main AI Controller (ESP32-S3-DevKitC-1) into its mounting location within the Server Enclosure Base.
2. Verify that the USB-C port of the Main AI Controller aligns correctly with the enclosure's cutout.
3. Slide the MicroSD Card Module into its dedicated slot within the Server Enclosure Base.
4. Ensure both components fit without significant force or obstruction, checking for proper clearances.

## 2. Wiring
### 2.1 Solder header pins to the MicroSD Card Module if not pre-assembled
**Solder header pins onto the MicroSD Card Module.**
1. Tin the six pads on the MicroSD Card Module (VCC, GND, MOSI, MISO, SCK, CS).
2. Place a 6-pin male header into the tinned holes, ensuring it sits straight.
3. Solder each pin securely to its corresponding pad on the MicroSD Card Module, using a soldering iron set to approximately 350°C.
4. Inspect all solder joints for good electrical connection and to ensure there are no short circuits or bridges between pins.
  > Tip: Use a breadboard or a helping hands tool to hold the header pins straight while soldering for cleaner, more reliable connections.

### 2.2 Mount the ESP32-S3 onto the enclosure base using M2 standoffs and screws
**Mount the Main AI Controller to the Server Enclosure Base.**
1. Screw four M2x6mm brass M2 PCB Standoffs into the designated mounting points on the Server Enclosure Base.
2. Carefully align the Main AI Controller (ESP32-S3-DevKitC-1) over the installed M2 PCB Standoffs.
3. Secure the Main AI Controller to the M2 PCB Standoffs using four M2x4mm M2 Screws for PCB.
4. Gently tighten each M2 screw until the board is held firmly, but avoid over-tightening to prevent damage.
  > Tip: Ensure the M2 standoffs are fully seated in the enclosure base before mounting the PCB to provide a stable and level platform for the Main AI Controller.

### 2.3 Wire the MicroSD Card Module to the ESP32-S3 for power (3.3V, GND)
**Wire the MicroSD Card Module to the Main AI Controller for power.**
1. Connect a jumper wire from the "3V3" pin on the Main AI Controller (ESP32-S3-DevKitC-1) to the "VCC" pin on the MicroSD Card Module.
2. Connect a jumper wire from the "GND" pin on the Main AI Controller (ESP32-S3-DevKitC-1) to the "GND" pin on the MicroSD Card Module.
3. Verify that both power connections are secure and correctly polarized.
  > Tip: Double-check that you are connecting to the 3.3V power rail on the Main AI Controller, not the 5V, as the MicroSD Card Module typically operates at 3.3V.

### 2.4 Wire the MicroSD Card Module to the ESP32-S3 for SPI data (MOSI, MISO, SCK, CS)
**Wire MicroSD Card Module to Main AI Controller via SPI.**
1. Connect a jumper wire from GPIO11 (MOSI) on the Main AI Controller to the MOSI pin on the MicroSD Card Module.
2. Connect a jumper wire from GPIO13 (MISO) on the Main AI Controller to the MISO pin on the MicroSD Card Module.
3. Connect a jumper wire from GPIO12 (SCK) on the Main AI Controller to the SCK pin on the MicroSD Card Module.
4. Connect a jumper wire from GPIO10 (CS) on the Main AI Controller to the CS pin on the MicroSD Card Module.
5. Verify all four SPI data connections are secure and correctly matched.
  > Tip: For reliable high-speed data transfer, keep SPI data lines as short as possible and bundled together to minimize interference.

### 2.5 Perform continuity checks on all wired connections to prevent shorts
**Perform continuity and short circuit checks on all electrical connections.**
1. Set your multimeter to continuity mode.
2. Verify continuity between the 3V3 pin on the Main AI Controller and the VCC pin on the MicroSD Card Module.
3. Verify continuity between the GND pin on the Main AI Controller and the GND pin on the MicroSD Card Module.
4. Check for shorts between 3V3 and GND on both the Main AI Controller and MicroSD Card Module.
5. Verify continuity for each SPI data line: GPIO11 (MOSI) to MOSI, GPIO13 (MISO) to MISO, GPIO12 (SCK) to SCK, and GPIO10 (CS) to CS.
6. Check for shorts between adjacent data lines and between data lines and power/ground on both modules.
  > Tip: Always perform continuity checks *before* applying power to prevent potential damage from miswires or shorts.

## 3. Bring-up
### 3.1 Connect the USB-C Wall Adapter to the ESP32-S3
**Connect the USB-C Wall Adapter to the Main AI Controller.**
1. Plug the USB-C Wall Adapter into a standard wall outlet.
2. Insert the USB-C cable from the USB-C Wall Adapter into the USB-C port on the Main AI Controller (ESP32-S3-DevKitC-1).
3. Observe the power indicator LED(s) on the Main AI Controller to confirm it is receiving power.
  > Tip: Ensure the USB-C Wall Adapter provides 5V DC output, which is standard for USB-C powered development boards like the ESP32-S3.

### 3.2 Verify ESP32-S3 powers on and is recognized by your computer
**Verify Main AI Controller powers on and is recognized by computer.**
1. Ensure the Main AI Controller (ESP32-S3-DevKitC-1) is connected to your computer via its USB-C port.
2. Observe if the power indicator LED on the Main AI Controller illuminates, confirming it is powered.
3. Open your computer's device manager (Windows) or use terminal commands like `ls /dev/tty*` (Linux/macOS).
4. Verify that a new USB-to-serial device (e.g., CP210x or CH340, depending on the specific ESP32-S3 variant) appears.
  > Tip: If the device is not recognized, you may need to install the appropriate USB-to-serial drivers for your ESP32-S3 board model.

### 3.3 Flash the operating system (e.g., RTOS) and necessary firmware onto the ESP32-S3
**Flash the operating system and firmware onto the Main AI Controller.**
1. Open your preferred development environment (e.g., ESP-IDF, Arduino IDE) on your computer.
2. Load the operating system (RTOS) and AI firmware project for the ESP32-S3-DevKitC-1.
3. Select the correct board model and the identified serial port for the Main AI Controller.
4. Compile the firmware project.
5. Initiate the flashing process, ensuring the Main AI Controller is in bootloader mode if required (typically by holding the BOOT button while briefly pressing and releasing the RESET button).
6. Monitor the console output for successful flashing and verification.
  > Tip: Ensure you have the necessary ESP32-S3 toolchain and drivers installed on your computer before attempting to flash firmware.

### 3.4 Insert a formatted MicroSD card and load the offline AI model files onto it
**Insert and load offline AI model files onto a formatted MicroSD card.**
1. Insert a blank MicroSD card into your computer's card reader.
2. Format the MicroSD card to FAT32 or exFAT filesystem.
3. Copy your pre-trained offline AI model files to the root directory of the formatted MicroSD card.
4. Safely eject the MicroSD card from your computer.
5. Insert the prepared MicroSD card into the slot on the MicroSD Card Module, ensuring it clicks into place.
  > Tip: For optimal performance and compatibility with embedded systems, ensure your MicroSD card is formatted with a standard filesystem like FAT32 and not NTFS.

### 3.5 Test MicroSD card detection and verify AI model files are accessible by the ESP32-S3
**Test MicroSD card detection and AI model file accessibility.**
1. Ensure the Main AI Controller is connected to your computer via USB-C and the MicroSD card is inserted into its module.
2. Open a serial monitor (e.g., in Arduino IDE or PlatformIO) connected to the Main AI Controller at the correct baud rate.
3. Reset the Main AI Controller to initiate the firmware's SD card detection routine.
4. Observe the serial monitor for messages indicating successful MicroSD card initialization.
5. Look for messages confirming the Main AI Controller can list and access the AI model files stored on the MicroSD card.
  > Tip: If the MicroSD card is not detected, double-check your SPI wiring (MOSI, MISO, SCK, CS, VCC, GND) and ensure the card is properly formatted and seated.

### 3.6 Run preliminary tests to confirm basic AI model inference functionality
**Test basic AI model inference functionality on the ESP32-S3.**
1. Ensure the Main AI Controller is powered and connected to your computer's serial monitor.
2. Reset the Main AI Controller to start the firmware, which should initiate AI model loading and a test inference.
3. Observe the serial monitor for output confirming the AI model is loaded from the MicroSD Card Module.
4. Look for messages indicating successful inference, such as confidence scores or classification results for a predefined test input.
5. Verify that the output reflects expected behavior for a basic AI model test run.
  > Tip: If inference fails, check the console for error messages related to model loading, memory allocation, or processing, which can indicate issues with the model file or firmware configuration.

## 4. Assembly
### 4.1 Gently place the MicroSD Card Module into its designated slot in the enclosure base
**Place the MicroSD Card Module into its designated slot.**
1. Locate the integrated slot designed for the MicroSD Card Module within the Server Enclosure Base.
2. Carefully align the MicroSD Card Module with the slot, ensuring the header pins face the Main AI Controller.
3. Gently slide the MicroSD Card Module into the slot until it is fully seated and stable.
4. Confirm that the module fits snugly without excessive force and that its orientation is correct.
  > Tip: Ensure all wired connections to the MicroSD Card Module are routed neatly before placing it, to prevent pinching or strain.

### 4.2 Ensure all internal wiring is neatly routed and secured, avoiding pinch points
**Neatly route and secure all internal wiring, avoiding pinch points.**
1. Visually inspect all jumper wires connecting the Main AI Controller and the MicroSD Card Module.
2. Gently route wires to avoid interfering with component placement or enclosure closure.
3. Ensure wires are not stretched or pulled taut, providing adequate slack.
4. Confirm no wires are in the path of where the Server Enclosure Lid will seat, preventing pinching.
5. Use small cable ties or adhesive mounts if necessary to secure loose wires, improving airflow and preventing snags.
  > Tip: Proper cable management prevents electrical shorts, improves airflow for cooling, and makes future maintenance easier within the tiny server enclosure.

### 4.3 Align the enclosure lid with the base and secure it using M3 screws
**Align the enclosure lid with the base and secure it with M3 screws.**
1. Carefully align the Server Enclosure Lid with the Server Enclosure Base, ensuring all edges are flush.
2. Verify that the screw holes in the lid line up precisely with the M3 Heat Set Inserts embedded in the base.
3. Insert four M3x8mm M3 Screws for Enclosure through the lid's holes and into the M3 Heat Set Inserts.
4. Using a screwdriver, gently tighten each M3 screw in an opposing pattern (e.g., diagonally) until the lid is securely fastened.
5. Ensure the lid is tightly closed, but avoid over-tightening the screws to prevent stripping the heat set inserts.
  > Tip: Tightening screws diagonally helps distribute pressure evenly, preventing warping of the 3D-printed lid or base.

### 4.4 Perform a final power-on test with the fully assembled enclosure
**Perform final power-on and functional test of the assembled server.**
1. Plug the USB-C Wall Adapter into a wall outlet and connect it to the USB-C port of the fully assembled Offline AI Server.
2. Observe the power indicator LED on the Main AI Controller through any enclosure cutouts, ensuring it illuminates.
3. Allow a few moments for the Main AI Controller to boot up and load the AI model from the MicroSD Card Module.
4. Verify any external indicators (e.g., LED patterns configured in firmware) or listen for internal signs of the offline AI processing initiating normally.
  > Tip: If no power is detected or the system doesn't appear to boot, double-check that the USB-C power connection is solid and consider reopening the enclosure to re-verify internal connections.
