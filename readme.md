

# royalEFI SPARK

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

## FOME (RUSEFI fork) Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download FOME Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/fome/fome_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download FOME TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/fome/fome_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20Console-purple?style=for-the-badge&logo=download&logoColor=white "Download FOME Console")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/royalEFI_spark/fome/fome_console.zip)
<!-- END LATEST DOWNLOAD BUTTON -->

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

### Black Connector

<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/royalEFI_spark.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/cb34225e-63c1-4ae5-84aa-97a96f62b942" alt="black" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | Alternative Function #2 |
| ------ | ------ | ------ | ------ | ------ | ------ |
| A1 | PG3  | Low Side 12 (G3)	    | FUEL PUMP	            |                         |               |
| A2 | O1   | Additional Output O1	| Low Side 13 (G4)	    | O1 Option               |               |
| A3 | O2   | Additional Output O2	| Low Side 14 (G5)	    | O2 Option               |               |
| A4 | O3   | Additional Output O3	| Low Side 15 (G6)	    | O3 Option               |               |
| A5 |      | 	                    | LSU HEATER-		        | LSU 4.9 CONNECTOR PIN 3	| WHITE WIRE    |
| A6 |      | 	                    | LSU IA			          | LSU 4.9 CONNECTOR PIN 5	| GREEN WIRE    |
| A7 |      | 	                    | LSU VGND			        | LSU 4.9 CONNECTOR PIN 2	| YELLOW WIRE   |
| A8 |      | 	                    | LSU HEATER+		        | LSU 4.9 CONNECTOR PIN 4	| GREY WIRE     |
| B1 |      | Switch SW5		        | DBW+		              | Low Side 11 (G2)	      |               |
| B2 |      | Switch SW4		        | CAN LOW		            | Digital Input 1 (D5)	  | USB D+        |
| B3 |      | Switch SW3		        | CAN HIGH		          | Digital Input 2 (D4)	  | USB D-        |
| B4 |      | Switch SW2	 	        | Digital Input 4 (D2)  | Analogue Input 8 (A4)	  | Knock 1 (C0)  |
| B5 |      | Switch SW1		        | Digital Input 3 (D3)	| Analogue Input 9 (A1)	  | Knock 2 (C1)  |
| B6 |      | 	                    | LSU NERMEST	          | LSU 4.9 CONNECTOR PIN 6	| BLACK WIRE    |
| B7 |      | 	                    | LSU IP	              | LSU 4.9 CONNECTOR PIN 1	| RED WIRE      |
| B8 |      | +12V from Battery	    | +12V Battery	        |                         |               |
| C1 |      | Switch SW6		        | DBW-		              | Low Side 10 (D15)	      |               |
| C2 | PE2  | VR1+		              | VR1+		              | HALL 1 (PG1)	          |               |
| C3 |      | VR1-		              | VR1-		              | HALL 2 (PE7)	          |               |
| C4 |      | VR2-		              | VR2-		              | HALL 4 (PE8)	          |               |
| C5 | PE3  | VR2+		              | VR2+		              | HALL 3 (PE9)	          |               |
| C6 | PG7  | Additional Output O4  | Low Side 16 (G7)      | O3 Option               |               |
| C7 |      | Sensor +5v Supply	    | Sensor +5v Supply		  |                         |               |
| C8 |      | Ground	              | Ground	              |                         |               |

