# Project: Wall-E Robot

## Overview
This project details the construction of a compact, low-cost "Wall-E" inspired robot. It features real-time motor and sensor control via an ESP32, enhanced with an expandable AI brain (LicheeRV-Nano) for complex tasks like vision and audio processing, all housed within a 3D-printed chassis for indoor environments and expressive movement.

## Assumptions
*  **Power Source:** 7.4-12.6V LiPo Battery.
*  **Environment:** Indoor, dry, level surfaces.
*  **Skill Level:** Intermediate hardware assembly and basic embedded programming knowledge.
*  **Tools:** 3D printer, soldering iron, basic hand tools (screwdrivers, wire strippers).

## Action Items
- [ ] Print all 3D mechanical components (chassis, mounts, head, arms, tracks).
- [ ] Mount motors (left_track_motor, right_track_motor) and attach tracks (left_track, right_track).
- [ ] Install power management (lipo_battery, bms_module, buck_converter_5v).
- [ ] Mount main controllers (licheerv_nano_main, esp32_controller) and motor driver (motor_driver_tracks) to combined_controller_mount.
- [ ] Connect track motors to motor_driver_tracks and motor driver to esp32_controller.
- [ ] Mount and wire head assembly servos (head_pan_servo, head_tilt_servo) and arm servos (left_arm_servo, right_arm_servo) to esp32_controller.
- [ ] Integrate all sensors (ultrasonic_front, ultrasonic_rear, ir_sensor_front, ir_sensor_rear, mic_module_usb, camera_mipi_csi_ov5647) with their respective MCUs.
- [ ] Connect display (display_st7789) and speaker (speaker_module_amp) to licheerv_nano_main.
- [ ] Establish inter-MCU communication (licheerv_nano_main ↔ esp32_controller via UART).
- [ ] Implement watchdog timer (watchdog_timer) for system reliability.
- [ ] Finalize wiring, ensuring all power and data connections are secure.
- [ ] Load initial firmware onto both MCUs.

## Assembly Key Points

| Component A           | Component B             | Key Considerations                                                                                                 |
| :-------------------- | :---------------------- | :----------------------------------------------------------------------------------------------------------------- |
| lipo_battery          | bms_module              | Connect BAT+ and BAT- for power.                                                                                   |
| bms_module            | buck_converter_5v       | Power input P+ and P- of BMS to VIN+ and VIN- of buck converter.                                                   |
| bms_module            | motor_driver_tracks     | Power P+ and P- of BMS to VM and GND of motor driver.                                                              |
| buck_converter_5v     | licheerv_nano_main      | VOUT+ to 5V, VOUT- to GND.                                                                                         |
| buck_converter_5v     | esp32_controller        | VOUT+ to VIN, VOUT- to GND.                                                                                        |
| licheerv_nano_main    | esp32_controller        | UART_TX (LicheeRV) to UART_RX (ESP32), UART_RX (LicheeRV) to UART_TX (ESP32).                                      |
| esp32_controller      | motor_driver_tracks     | GPIO16 (Motor1_PWM) to PWMA, GPIO17 (Motor1_DIR) to AIN1/AIN2; GPIO18 (Motor2_PWM) to PWMB, GPIO19 (Motor2_DIR) to BIN1/BIN2. |
| motor_driver_tracks   | left_track_motor/right_track_motor | AO1/AO2 for left, BO1/BO2 for right.                                                                               |
| esp32_controller      | ultrasonic_front/rear   | Front: GPIO5 (US_Trig_Front) to TRIG, ECHO to GPIO4 (US_Echo_Front). Rear: GPIO2 (US_Trig_Rear) to TRIG, ECHO to GPIO0 (US_Echo_Rear). |
| esp32_controller      | ir_sensor_front/rear    | GPIO34 (IR_Front) to OUT, GPIO35 (IR_Rear) to OUT.                                                                 |
| licheerv_nano_main    | mic_module_usb          | USB_HOST for data and 5V for power.                                                                                |
| licheerv_nano_main    | speaker_module_amp      | I2S_OUT for data, 5V for power.                                                                                    |
| licheerv_nano_main    | display_st7789          | SPI for data, 3.3V to VIN for power.                                                                               |
| watchdog_timer        | licheerv_nano_main      | DRV to RESET; GPIO_A (LicheeRV) to DONE.                                                                           |
| watchdog_timer        | esp32_controller        | DRV_ALT to EN; GPIO_B (ESP32) to DONE_ALT.                                                                         |
| bms_module            | esp32_controller        | LOW_BATT_OUT to GPIO_C for battery monitoring.                                                                     |
| esp32_controller      | head_pan_servo/tilt_servo/left_arm_servo/right_arm_servo | PWM pins GPIO12-GPIO15 to Signal. Power from buck_converter_5v.                                                    |
| licheerv_nano_main    | camera_mipi_csi_ov5647  | MIPI_CSI for data. Power from buck_converter_5v.                                                                   |
| chassis               | track_motor_mount       | M3x12mm bolts for secure mounting.                                                                                 |
| track_motor_mount     | left_track_motor/right_track_motor | M2x8mm bolts for secure mounting.                                                                                  |
| left/right_track_motor | drive_sprocket          | Ensure tight shaft coupling for reliable track movement.                                                           |
| head_assembly         | head_pan_servo/head_tilt_servo | Servo horns attach to mounts for smooth articulation.                                                              |
| chassis               | combined_controller_mount | Mount with M3 bolts; ensure proper orientation for component access.                                               |
| combined_controller_mount | licheerv_nano_main/esp32_controller/motor_driver_tracks | Use M2 bolts for secure attachment. Ensure clearance for wiring.                                                   |
| head_assembly         | camera_mipi_mount       | M3x6mm bolts, ensuring camera lens is clear.                                                                       |
| display_mount         | display_st7789          | M2x8mm bolts, careful not to overtighten and damage display.                                                       |