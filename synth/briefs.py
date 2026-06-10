"""Diverse project-concept briefs for new-project generation.

~200 concepts spread across hardware domains so that scaled generation yields
genuinely distinct projects rather than minor rewordings of a few themes.

Grouped by domain for readability; `ALL_BRIEFS` is the flat list the generator
consumes. Keep entries short, concrete, and noun-phrase-shaped — they steer
ideation without dictating the design.
"""
from __future__ import annotations

AUDIO = [
    "a Bluetooth audio amplifier in a wooden enclosure",
    "a guitar effects pedal with digital reverb",
    "a portable Bluetooth speaker with passive radiators",
    "a tube headphone amplifier with VU meters",
    "a MIDI controller with rotary encoders and pads",
    "a eurorack synthesizer oscillator module",
    "a contact-microphone field recorder",
    "a digital audio sampler with pad triggers",
    "a vinyl turntable preamp with RIAA equalization",
    "a multi-zone home audio distribution controller",
    "a metronome with tap-tempo and click output",
    "a white-noise sleep machine with timer",
]

RF_COMMS = [
    "a ham radio antenna tuner with SWR display",
    "a LoRa long-range telemetry base station",
    "a software-defined radio receiver front-end",
    "a 433MHz remote relay controller",
    "an RF signal-strength field meter",
    "a packet-radio APRS tracker",
    "a Wi-Fi range-extender with directional antenna",
    "a GPS-disciplined frequency reference",
    "an NFC access-control reader",
    "a Bluetooth beacon for indoor positioning",
]

ROBOTICS = [
    "a robotic line-following delivery cart",
    "a self-balancing two-wheel robot",
    "a 4-DOF desktop robotic arm",
    "a hexapod walking robot",
    "a quadruped dog-style robot",
    "a cable-suspended camera robot",
    "a delta-configuration pick-and-place robot",
    "a SCARA arm for light assembly",
    "an omni-wheel holonomic rover",
    "a tracked search-and-rescue crawler",
    "a robotic gripper with force feedback",
    "a swarm of small differential-drive bots",
]

DRONES_AERIAL = [
    "a 3-inch cinewhoop FPV drone",
    "a fixed-wing mapping UAV",
    "a tethered surveillance quadcopter",
    "a payload-dropping delivery drone",
    "a brushed micro indoor drone",
    "a VTOL tailsitter aircraft",
    "a high-altitude weather balloon payload",
    "a crop-spraying agricultural drone",
]

SENSORS_INSTRUMENTS = [
    "a desktop weather station with e-ink display",
    "a desktop air quality monitor with CO2 sensing",
    "a Geiger counter with logging",
    "a portable spectrometer for material analysis",
    "a digital pH and TDS water tester",
    "a vibration analyzer for machinery",
    "a thermal-imaging add-on for a phone",
    "a lightning detector with strike mapping",
    "a seismometer for earthquake logging",
    "an ultrasonic anemometer wind gauge",
    "a soil-nutrient monitoring probe array",
    "a particulate-matter pollution logger",
    "a UV index and lux meter",
    "a gas-leak detector with audible alarm",
    "a laser rangefinder with display",
    "a digital caliper data-logger",
]

LAB_TOOLS = [
    "a digital bench power supply with display",
    "a brushless motor dynamometer test rig",
    "a UV exposure box for PCB fabrication",
    "a reflow soldering hotplate with PID control",
    "a programmable DC electronic load",
    "a benchtop function generator",
    "a component LCR meter",
    "a curve tracer for transistors",
    "a fume extractor with activated carbon",
    "a precision temperature-controlled water bath",
    "a magnetic stirrer with hotplate",
    "a vacuum chamber controller for degassing",
]

HOME_IOT = [
    "a wall-mounted smart home control panel",
    "a smart mailbox with delivery notification",
    "a smart thermostat with occupancy sensing",
    "a window-blind motorization kit",
    "a doorbell camera with local recording",
    "a water-leak detector network",
    "a smart energy meter for the breaker panel",
    "a voice-controlled lamp dimmer",
    "an RFID-based front-door lock",
    "a refrigerator inventory tracker",
    "a smart plant pot with self-watering",
    "a closet humidity and mold monitor",
]

GARDEN_AGRI = [
    "a solar-powered garden irrigation controller",
    "an automated plant-watering windowsill garden",
    "a hydroponic nutrient-dosing system",
    "an aquaponics monitoring controller",
    "a greenhouse climate automation hub",
    "a beehive weight and temperature monitor",
    "a chicken-coop automatic door",
    "a compost-pile temperature logger",
    "a drip-irrigation soil-moisture controller",
    "a grow-light spectrum scheduler",
]

WEARABLES = [
    "a wearable haptic navigation wristband",
    "a fitness heart-rate chest strap",
    "a sleep-tracking smart ring prototype",
    "a posture-correction back sensor",
    "a UV-exposure wristband for sun safety",
    "a gesture-control glove",
    "an EMG muscle-activity armband",
    "a fall-detection pendant for elderly care",
]

DISPLAY_LIGHTING = [
    "a programmable LED desk lamp with ambient sensing",
    "an addressable-LED matrix word clock",
    "a Nixie-tube retro clock",
    "a POV (persistence of vision) propeller display",
    "an infinity-mirror coffee table",
    "a sunrise-simulation alarm lamp",
    "a sound-reactive LED panel",
    "a flip-dot mechanical display",
    "an e-ink desktop calendar",
    "a fiber-optic star-ceiling controller",
]

CNC_FABRICATION = [
    "a CNC pen plotter for drawing",
    "a laser engraver for wood and acrylic",
    "a desktop foam-cutting hot-wire machine",
    "a 3-axis PCB milling machine",
    "a filament dry-box with humidity control",
    "a rotary axis attachment for a laser cutter",
    "a vinyl cutter for stickers",
    "an automatic wire-stripping machine",
]

POWER_ENERGY = [
    "a solar charge controller with MPPT",
    "an 18650 battery capacity tester",
    "a portable power station with inverter",
    "a wind-turbine charge regulator",
    "a supercapacitor energy buffer module",
    "a USB-C power-delivery trigger board",
    "a battery spot-welder for cell packs",
    "an uninterruptible power supply for a router",
]

AUTOMOTIVE_VEHICLE = [
    "an OBD-II car diagnostics display",
    "a motorcycle gear-position indicator",
    "a tire-pressure monitoring system",
    "a dashcam with G-sensor logging",
    "an electric skateboard motor controller",
    "a go-kart telemetry logger",
    "a trailer brake-light wireless repeater",
    "a car battery health monitor",
]

SECURITY_ACCESS = [
    "a fingerprint-locked storage box",
    "a PIN-code safe with motorized bolt",
    "a motion-activated security camera",
    "a perimeter laser tripwire alarm",
    "an RFID time-clock attendance system",
    "a GPS asset tracker with geofencing",
    "a tamper-evident shipping logger",
]

GAMES_TOYS = [
    "a handheld retro game console",
    "an arcade-button MAME cabinet controller",
    "a laser-tag blaster set",
    "an electronic dice tower with display",
    "a Simon-says memory game",
    "a marble-run gate sequencer",
    "a chess clock with two buttons",
    "a quiz-buzzer lockout system",
]

PHOTOGRAPHY = [
    "a motorized camera slider for time-lapse photography",
    "a focus-stacking macro rail",
    "a high-speed flash trigger for droplets",
    "a 360-degree product-photography turntable",
    "an intervalometer for star trails",
    "a panoramic gigapixel camera mount",
]

KITCHEN_APPLIANCE = [
    "a sous-vide immersion cooker controller",
    "a coffee-roaster temperature controller",
    "a kitchen scale with recipe scaling",
    "a fermentation chamber thermostat",
    "a smart kettle with temperature presets",
    "an automatic pet feeder with portion control",
]

NETWORK_COMPUTE = [
    "a network-attached storage enclosure with cooling",
    "a Raspberry Pi cluster carrier board",
    "a hardware password manager dongle",
    "a Pi-hole ad-blocker appliance",
    "a KVM switch for two computers",
    "a Wake-on-LAN remote power button",
    "a serial-console server for lab gear",
]

SCIENCE_EDU = [
    "a Tesla coil with music modulation",
    "a Van de Graaff generator controller",
    "a pendulum-wave demonstration rig",
    "a cloud chamber for particle visualization",
    "a magnetic levitation desk toy",
    "an electrochemistry electrolysis station",
    "a planetarium star projector",
    "a digital oscilloscope clock teaching aid",
]

MISC_GADGETS = [
    "a Bluetooth e-paper conference badge",
    "a desktop CO and smoke alarm hub",
    "a smart pill-dispenser with reminders",
    "a tide and moon-phase clock",
    "a binary wall clock",
    "a word-of-the-day e-ink display",
    "a dog-treat dispensing webcam",
    "a smart cat litter-box monitor",
    "a desktop zen-garden sand plotter",
    "a haptic Morse-code trainer",
]

# Flat list consumed by the generator.
ALL_BRIEFS: list[str] = [
    *AUDIO, *RF_COMMS, *ROBOTICS, *DRONES_AERIAL, *SENSORS_INSTRUMENTS,
    *LAB_TOOLS, *HOME_IOT, *GARDEN_AGRI, *WEARABLES, *DISPLAY_LIGHTING,
    *CNC_FABRICATION, *POWER_ENERGY, *AUTOMOTIVE_VEHICLE, *SECURITY_ACCESS,
    *GAMES_TOYS, *PHOTOGRAPHY, *KITCHEN_APPLIANCE, *NETWORK_COMPUTE,
    *SCIENCE_EDU, *MISC_GADGETS,
]
