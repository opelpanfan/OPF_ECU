

# royalEFI SPARK
![20240904_202134](https://github.com/user-attachments/assets/981e789f-b6b3-49ff-b69c-5a7080fcec3e)

## Features

- 2 Injectors
- 2 Coils
- 4 Low Side Switch
- 1 VR / 2 Hall Triggers
- 2 Digital Inputs
- 4 Analogue 0-5v inputs
- Wideband (14point7)
- 1 Canbus
- 4bar map
- Onboard Barometer
- Onboard Removable SD Card
- Bluetooth

## Firmware

## RUSEFI Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download RusEFI Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/rusefi/rusefi_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download RusEFI TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/rusefi/rusefi_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20Console-purple?style=for-the-badge&logo=download&logoColor=white "Download RusEFI Console")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/rusefi/rusefi_console.zip)
<!-- END LATEST DOWNLOAD BUTTON -->

## Interactive Pinout Manual 

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Pinout%20Manual-black?style=for-the-badge&logo=download&logoColor=white "Pinout Manual")](https://opelpanfan.github.io/OPF_ECU/royalEFI_spark.html)
<!-- END LATEST DOWNLOAD BUTTON -->

<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/royalEFI_spark.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/cdb32b64-67ca-4be2-bafb-5091004ee178" alt="black" width="100%" />
</a>
</div>

<table class="pinout-table"><thead><tr><th>Pin Number</th><th>STM32 Pin Number</th><th>TS Name</th><th>Typical Function</th><th>Alternative Function #1</th><th style="display: none;">Alternative Function #2</th></tr></thead><tbody><tr class="data"><td class="print-column" data-field="pin" data-type="lsu_heater-">A8</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">LSU Heater -</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="lsu_vgnd">A7</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">LSU VGND</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="lsu_ia">A6</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">LSU IA</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="switch">A5</td><td data-field="pin_name">E9</td><td data-field="ts_name">Hall3 (E9)</td><td class="print-column" data-field="function">SWITCH CAN_H/HALL3</td><td data-field="alternative1">CAN_H</td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="switch">A4</td><td data-field="pin_name">E2/E7</td><td data-field="ts_name">VR1 (E2)</td><td class="print-column" data-field="function">SWITCH VR-/HALL2</td><td data-field="alternative1">Hall2 (E7)</td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_high">A3</td><td data-field="pin_name">E15</td><td data-field="ts_name">COIL 1 (E15)</td><td class="print-column" data-field="function">COIL 1</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_low">A2</td><td data-field="pin_name">D10</td><td data-field="ts_name">BOOST (D10)</td><td class="print-column" data-field="function">BOOST</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_low">A1</td><td data-field="pin_name">D6</td><td data-field="ts_name">IDLE (D6)</td><td class="print-column" data-field="function">IDLE</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="12v">B8</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">+12V</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="lsu_ip">B7</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">LSU IP</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="lsu_nermest">B6</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">LSU NM</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="switch">B5</td><td data-field="pin_name">A5</td><td data-field="ts_name">Analog Inputs 1 (A5)</td><td class="print-column" data-field="function">SWITCH CAN_L/SPARE1</td><td data-field="alternative1">CAN_L</td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="switch">B4</td><td data-field="pin_name">E2/G1</td><td data-field="ts_name">VR1 (E2)</td><td class="print-column" data-field="function">SWITCH VR+/HALL1</td><td data-field="alternative1">Hall1 (G1)</td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_high">B3</td><td data-field="pin_name">E14</td><td data-field="ts_name">COIL 2 (E14)</td><td class="print-column" data-field="function">COIL 2</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_low">B2</td><td data-field="pin_name">D9</td><td data-field="ts_name">FAN (D9)</td><td class="print-column" data-field="function">FAN</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_inj">B1</td><td data-field="pin_name">D7</td><td data-field="ts_name">INJECTOR 2 (D7)</td><td class="print-column" data-field="function">INJECTOR 2</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="gnd">C8</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">Power Ground</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="5v">C7</td><td data-field="pin_name"></td><td data-field="ts_name"></td><td class="print-column" data-field="function">+5V</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="in_adc">C6</td><td data-field="pin_name">B0</td><td data-field="ts_name">IAT (B0)</td><td class="print-column" data-field="function">IAT</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="in_adc">C5</td><td data-field="pin_name">A7</td><td data-field="ts_name">CLT (A7)</td><td class="print-column" data-field="function">CLT</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="in_adc">C4</td><td data-field="pin_name">C5</td><td data-field="ts_name">TPS (C5)</td><td class="print-column" data-field="function">TPS</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_low">C3</td><td data-field="pin_name">D12</td><td data-field="ts_name">PUMP (D12)</td><td class="print-column" data-field="function">FUEL PUMP</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_low">C2</td><td data-field="pin_name">D11</td><td data-field="ts_name">TACHO (D11)</td><td class="print-column" data-field="function">TACHO</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr><tr class="data"><td class="print-column" data-field="pin" data-type="out_inj">C1</td><td data-field="pin_name">D8</td><td data-field="ts_name">INJECTOR 1 (D8)</td><td class="print-column" data-field="function">INJECTOR 1</td><td data-field="alternative1"></td><td data-field="alternative2" style="display: none;"></td></tr></tbody></table>
