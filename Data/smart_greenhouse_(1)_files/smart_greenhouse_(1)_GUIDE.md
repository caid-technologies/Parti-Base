## Tools
- 3D printer (PETG and PLA capable)
- Soldering iron with fine tip
- Wire strippers
- Crimping tool (optional, for custom wire harnesses)
- Multimeter
- M3 hex key / screwdriver
- Heat gun (for heat-set inserts)
- Small pliers / tweezers
- Utility knife / snips (for tubing and zip ties)

## Assumptions
- Basic electronics knowledge and safety practices
- Familiarity with 3D printing software and operation
- Arduino IDE or ESP-IDF installed for firmware development
- Access to a 12V power supply for initial testing (optional, can use battery/solar)

## 1. Fabrication
### 1.1 3D print all custom mechanical components
*(not yet generated)*

### 1.2 Install M3 heat-set inserts into all designated mounting points on 3D printed parts
*(not yet generated)*

### 1.3 Cut water tubing to the required length for pump connections
*(not yet generated)*

### 1.4 Deburr and clean all 3D printed parts, then test-fit mechanical connections
*(not yet generated)*

## 2. Wiring
### 2.1 Connect Solar Panel to Solar Charge Controller input terminals
*(not yet generated)*

### 2.2 Connect 12V Battery to Solar Charge Controller battery terminals
*(not yet generated)*

### 2.3 Wire Solar Charge Controller load output to 5V buck converter input and relay module COM pins
*(not yet generated)*

### 2.4 Connect 5V buck converter output to ESP32, DHT22 sensor, soil moisture sensor, and both relay VCC pins
*(not yet generated)*

### 2.5 Wire ESP32 data pins to DHT22 sensor, soil moisture sensor, and relay IN pins
*(not yet generated)*

### 2.6 Wire fan relay NO output to Cooling Fan, and pump relay NO output to Water Pump
*(not yet generated)*

### 2.7 Connect shared system ground from solar charge controller LOAD- to water pump - terminal
*(not yet generated)*

### 2.8 Perform continuity checks on all power and data lines to ensure correct wiring
*(not yet generated)*

## 3. Bring-up
### 3.1 Connect ESP32 to computer and upload initial firmware
*(not yet generated)*

### 3.2 Verify ESP32 boots correctly and serial output is functional
*(not yet generated)*

### 3.3 Test DHT22 sensor readings for ambient temperature and humidity
*(not yet generated)*

### 3.4 Test soil moisture sensor readings and analog input functionality
*(not yet generated)*

### 3.5 Actuate pump and fan relays individually and verify fan and water pump operation
*(not yet generated)*

### 3.6 Confirm solar charge controller is charging the battery and providing power to loads
*(not yet generated)*

## 4. Assembly
### 4.1 Mount the Solar Panel Mount and Solar Panel to the exterior of the greenhouse frame
*(not yet generated)*

### 4.2 Mount the Battery Holder and 12V Battery to the interior base of the greenhouse frame
*(not yet generated)*

### 4.3 Mount the Electronics Enclosure to the greenhouse frame
*(not yet generated)*

### 4.4 Install ESP32, both relay modules, 5V buck converter, and charge controller into the Electronics Enclosure
*(not yet generated)*

### 4.5 Mount the Soil Sensor Mount and Soil Moisture Sensor in soil near plants, and the DHT22 Sensor Mount and DHT22 Sensor inside the greenhouse
*(not yet generated)*

### 4.6 Mount the Pump Bracket and Water Pump near the water source, and the Fan Mount and Cooling Fan to the frame opening
*(not yet generated)*

### 4.7 Attach the water hose to the water pump and route all cables, securing with zip ties for strain relief and organization
*(not yet generated)*
