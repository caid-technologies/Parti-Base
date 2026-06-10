# Smart AR Glasses Project Guide

## Overview
This project outlines the development of "Smart AR Glasses" designed for navigation and AI capabilities, featuring a first-person camera. Key subsystems include head tracking, GPS navigation, AR display, voice input/output, and power management, all controlled by a central MCU.

## Assumptions
* Power Source: Single LiPo Battery 3.7V.
* Environment: Indoor/outdoor operation, moderate temperatures.
* Skill Level: Intermediate electrical and mechanical assembly, basic 3D printing knowledge.
* Software: Firmware development for mcu_main (ESP32-based) handling all peripheral communication.

## Action Items
- [ ] 3D print all mechanical housings and structural components.
- [ ] Assemble power management circuit (power_lipo_battery, power_charging_circuit, power_buck_converter).
- [ ] Mount mcu_main into mcu_mount.
- [ ] Integrate imu_head_tracking into imu_housing and connect to mcu_main (I2C: SDA, SCL).
- [ ] Integrate gps_navigation into gps_module_mount and connect to mcu_main (UART: TXD0, RXD0).
- [ ] Install display_ar_micro into oled_display_bezel and connect to mcu_main (I2C: SDA, SCL).
- [ ] Mount camera_fpv into camera_module_housing and connect to mcu_main (Parallel DVP, SCCB/I2C).
- [ ] Connect mic_voice_input (GPIO32) and speaker_audio_out (GPIO18) to mcu_main.
- [ ] Secure input_button_left (GPIO13) and input_button_right (GPIO14) with button_caps to mcu_main.
- [ ] Finalize assembly of all components into spectacle_frame, ensuring proper cable management.
- [ ] Test all electrical connections and component functionality.
- [ ] Load and verify initial firmware for AR functionality, navigation, and AI processing.

## Assembly Key Points

* `spectacle_frame` * `left_hinge`, `right_hinge`
    Mounts via `m1_7_x_5mm_screws`
* `spectacle_frame` * `nose_pad_set`
    Mounts into frame recess
* `mcu_mount` * `mcu_main`
    `mcu_mount` holds `mcu_main` with `m2_x_8mm_screws`
* `imu_housing` * `imu_head_tracking`
    `imu_housing` encloses and secures `imu_head_tracking`
* `gps_module_mount` * `gps_navigation`
    `gps_module_mount` holds `gps_navigation` with `m2_x_8mm_screws`
* `oled_display_bezel` * `display_ar_micro`
    `oled_display_bezel` secures `display_ar_micro` into bezel
* `camera_module_housing` * `camera_fpv`
    `camera_module_housing` encloses and positions `camera_fpv`
* `microphone_grille` * `mic_voice_input`
    `microphone_grille` integrates over opening, protects `mic_voice_input`
* `speaker_grille` * `speaker_audio_out`
    `speaker_grille` integrates over opening, protects `speaker_audio_out`
* `battery_bay_cover` * `spectacle_frame`
    `battery_bay_cover` latches onto battery bay
* `button_caps` * `input_button_left`, `input_button_right`
    `button_caps` attach to button recess with adhesive, actuate button
* `power_lipo_battery` * `power_charging_circuit`
    Connect BAT+ to BAT+ and BAT- to BAT-
* `power_charging_circuit` * `power_buck_converter`
    Connect OUT+ to VIN, OUT- to GND_IN (3.7V nominal)
* `power_buck_converter` * `mcu_main`, `display_ar_micro`, `camera_fpv`, `mic_voice_input`, `gps_navigation`
    VOUT (5V) and GND_OUT to respective VCC/V+ and GND pins
* `mcu_main` * `imu_head_tracking`
    `SDA` to `SDA`, `SCL` to `SCL` (I2C)
* `mcu_main` * `gps_navigation`
    `TXD0` to `RX`, `RXD0` to `TX` (UART)
* `mcu_main` * `display_ar_micro`
    `SDA` to `SDA`, `SCL` to `SCL` (I2C)
* `mcu_main` * `camera_fpv`
    Ensure correct DVP pin mapping (`GPIO2-PCLK`, `GPIO4-VSYNC`, `GPIO16-HREF`, `GPIO17-XCLK`, `GPIO21-D0`, `GPIO22-D1`, `GPIO23-D2`, `GPIO25-D3`, `GPIO26-D4`, `GPIO34-D5`, `GPIO35-D6`, `GPIO36-D7`). SCCB `SDA` to `SIOD`, `SCL` to `SIOC`.
* `mcu_main` * `mic_voice_input`
    `GPIO32` to `OUT` (Analog)
* `mcu_main` * `speaker_audio_out`
    `GPIO18` to `SPK+` (PWM/DAC)
* `mcu_main` * `input_button_left`, `input_button_right`
    `GPIO13` to `SIG` (left), `GPIO14` to `SIG` (right)