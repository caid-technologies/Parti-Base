## Tools
- 3D printer (PETG and Carbon Fiber PETG capable)
- Soldering iron with fine tip
- Wire strippers and flush cutters
- Multimeter
- M2 and M3 hex key set
- Small Phillips and flathead screwdrivers
- Needle-nose pliers
- Heat gun (for heat shrink tubing)
- Adhesive or hot glue gun (for securing wires)

## Assumptions
- Basic knowledge of 3D printing and post-processing techniques.
- Familiarity with Raspberry Pi OS installation and basic configuration.
- Basic electronics knowledge including GPIO, SPI, I2C, and UART protocols.
- Competency in basic soldering techniques for PCBs and wire connections.

## 1. Fabrication
### 1.1 Print core chassis components (base and lid)
**3D print the robust cyberdeck chassis base and lid.**
1. Prepare your 3D printer with a clean, leveled bed and load Carbon Fiber PETG filament (matte black or olive drab).
2. Print the Custom Modular Chassis Base (220x150x50mm) using Carbon Fiber PETG, ensuring high infill (>60%) and settings optimized for waterproof layer lines.
3. Print the Custom Modular Chassis Lid (220x150x25mm) with the same Carbon Fiber PETG material and high infill/waterproof settings.
4. After cooling, carefully remove both chassis components and thoroughly inspect for dimensional accuracy, layer adhesion, and any defects that could compromise weather resistance or structural integrity.
  > Tip: To ensure maximum weather resistance and strength, consider drying your Carbon Fiber PETG filament before printing to prevent moisture-related print defects and choose a print orientation that minimizes visible layer lines on critical sealing surfaces.

### 1.2 Print modular chassis inserts (radio bay, port panel, control panel)
**Print all modular chassis inserts for controls and peripherals.**
1. Load PETG filament (matte olive drab recommended) into your 3D printer.
2. Print the Baofeng Radio Bay Insert (105x55x35mm) with medium infill and strong walls (e.g., 3-4 perimeters).
3. Print the External Port Panel Insert (100x50x20mm) using the same PETG settings.
4. Print the Control Deck Panel (120x60x10mm) with high infill (>60%) for extra sturdiness.
5. Inspect all printed inserts for fit, finish, and ensure all mounting points and cutouts are clear and accurate.
  > Tip: For a truly tactical look, ensure your PETG filament is a matte finish and consider matching the color to the Carbon Fiber PETG chassis, or using a contrasting dark color.

### 1.3 Print internal mounts and trays (RPI, battery, power boards)
**Print internal mounts and trays for the RPi, battery, and power modules.**
1. Load black PETG filament into your 3D printer.
2. Print the Raspberry Pi Mount (90x60x10mm) and Power Module Mount Plate (60x40x5mm) using standard PETG settings.
3. Print the LiPo Battery Tray (185x85x65mm) with medium infill (e.g., 40%) and strong walls (e.g., 3-4 perimeters) for robust battery retention.
4. Carefully remove all printed parts and verify their dimensions and fit against the corresponding electrical components.
  > Tip: For the battery tray, consider reinforcing critical stress points in your slicer software to ensure it can withstand the weight and potential vibrations of the large LiPo pack during rugged use.

### 1.4 Print display bezels and mounts
**Print bezels and mounts for all three displays.**
1. Load PETG filament (matte black or olive drab recommended) into your 3D printer.
2. Print the 7-inch LCD Bezel/Frame (170x110x5mm) with standard PETG settings.
3. Print the E-Ink Display Bezel/Frame (108x83x3mm) with standard PETG settings.
4. Print the Round HUD Display Mount (45x45x8mm) with standard PETG settings.
5. Inspect all printed bezels and mounts to ensure clean edges and accurate dimensions for optimal display fit and aesthetic integration.
  > Tip: Ensure that the visible surfaces of the bezels are printed with a high-quality finish, as they will be prominent components of the cyberdeck's aesthetic.

### 1.5 Print sensor and LED housings/shrouds
**Print all remaining sensor, LED, and status indicator housings.**
1. Load PETG filament (matte black or olive drab recommended) into your 3D printer.
2. Print the GPS Antenna Dome Shroud (30x30x20mm) with waterproof and UV-resistant settings to withstand outdoor exposure.
3. Print the LED Array Housing (45x25x20mm) with high infill and heat-resistant settings to support the multi-spectrum LED array and heatsink.
4. Print the RTL-SDR Antenna Mount (20x20x15mm) and Charge Status LED Panel Frame (50x25x3mm) using standard PETG settings.
5. Switch to Clear PETG filament and print the Sensor Window Frame (20x15x5mm) with standard settings.
6. Carefully inspect all printed parts for smooth finishes and accurate dimensions, especially the clear frame and heat-resistant housing.
  > Tip: For optimal UV resistance and waterproofing on the GPS dome, consider applying a clear UV-resistant sealant or paint after printing.

### 1.6 Cut and fit the chassis sealing gasket
**Cut and fit the custom EPDM foam gasket for chassis sealing.**
1. Measure the perimeter of the Custom Modular Chassis Base's sealing channel.
2. Carefully cut the EPDM Foam Gasket (600x10x3mm) to the measured length, ensuring clean, straight cuts for optimal sealing.
3. Apply a thin, even bead of high-strength, waterproof adhesive along the sealing channel of the chassis base.
4. Press the custom-cut EPDM Foam Gasket firmly into the adhesive-lined channel, ensuring no gaps or overlaps at the corners.
5. Allow the adhesive to fully cure according to the manufacturer's instructions, ensuring a robust and weather-resistant seal.
  > Tip: Pre-fitting the gasket without adhesive can help identify any areas that require trimming or adjustment for a perfect seal. Use a contact adhesive or marine-grade sealant for best waterproof results.

### 1.7 Cut and fit the sensor protective window
**Cut and fit the acrylic protective window for the environmental sensors.**
1. Carefully measure the internal dimensions of the Sensor Window Frame (20x15x5mm) opening.
2. Using a sharp acrylic cutting tool or a fine-tooth saw, cut a piece of 2mm thick Acrylic Sheet to the measured dimensions (approximately 15x10mm).
3. Deburr and smooth all edges of the cut acrylic piece with fine-grit sandpaper to ensure a clean finish and prevent snags.
4. Test fit the cut acrylic window into the Sensor Window Frame to ensure a snug, flush fit. Trim as necessary for a perfect seal.
5. Apply a small bead of clear, waterproof adhesive (e.g., silicone or epoxy) around the inner perimeter of the frame and carefully press the acrylic window into place.
  > Tip: When working with acrylic, use masking tape along your cut lines to prevent chipping and ensure a cleaner break. For optimal clarity, clean the window with a microfiber cloth before final adhesive application.

## 2. Wiring
### 2.1 Wire the external power input, charge controller, and main battery pack
*(not yet generated)*

### 2.2 Wire main power toggle and 5V DC-DC converter from battery
*(not yet generated)*

### 2.3 Connect 5V power bus to Raspberry Pi and ruggedized USB hub
*(not yet generated)*

### 2.4 Wire Raspberry Pi GPIO to E-Ink display, round LCD, and rotary encoder
*(not yet generated)*

### 2.5 Connect Raspberry Pi to GPS, environmental, and IMU sensors via UART/I2C
*(not yet generated)*

### 2.6 Wire LED array power toggle and connect to multi-spectrum LED array
*(not yet generated)*

### 2.7 Connect USB hub to Raspberry Pi and prepare external USB connections
*(not yet generated)*

### 2.8 Prepare audio interface for Baofeng radio integration
*(not yet generated)*

## 3. Bring-up
### 3.1 Install Raspberry Pi OS and basic drivers
*(not yet generated)*

### 3.2 Test 7-inch IPS LCD display via HDMI
*(not yet generated)*

### 3.3 Verify E-Ink and round LCD functionality with SPI drivers
*(not yet generated)*

### 3.4 Test rotary encoder and switch input responsiveness
*(not yet generated)*

### 3.5 Confirm GPS, BME280, and BNO055 sensor data acquisition
*(not yet generated)*

### 3.6 Test high-power LED array illumination and control
*(not yet generated)*

### 3.7 Verify battery charge status panel and charging input
*(not yet generated)*

### 3.8 Test RTL-SDR dongle and Baofeng audio interface connectivity
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the Raspberry Pi and internal power boards
*(not yet generated)*

### 4.2 Install the main LiPo battery pack into its tray
*(not yet generated)*

### 4.3 Mount primary 7-inch LCD into lid chassis with bezel
*(not yet generated)*

### 4.4 Integrate E-Ink and round HUD displays into chassis base and lid
*(not yet generated)*

### 4.5 Install rotary encoder, knob, toggle switches, and safety covers onto control panel
*(not yet generated)*

### 4.6 Mount Baofeng radio into its bay insert
*(not yet generated)*

### 4.7 Install external port panel with power input, USB hub, and LED array
*(not yet generated)*

### 4.8 Mount GPS module, environmental/IMU sensors, and status LED panel
*(not yet generated)*

### 4.9 Route all internal wiring, secure with cable ties, and fasten chassis lid
*(not yet generated)*
