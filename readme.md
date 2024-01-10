

# OPF 8 (Core8) v2.4c

## FOME (RUSEFI fork) Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download FOME Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/fome/fome_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download FOME TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/fome/fome_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

## RUSEFI Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download RusEFI Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/rusefi/rusefi_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download RusEFI TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/rusefi/rusefi_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->


## Speeduino Firmware

(Right click and 'Save link as...')
<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Speeduino%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download Speeduino Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/speeduino/speeduino_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Speeduino%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download Speeduino TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core8_24c/speeduino/speeduino_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

## Interactive Pinout Manual 

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Pinout%20Manual-black?style=for-the-badge&logo=download&logoColor=white "Pinout Manual")](https://opelpanfan.github.io/OPF_ECU/core8_24c.html)
<!-- END LATEST DOWNLOAD BUTTON -->

### Black Connector

<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core8_24c.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/cb34225e-63c1-4ae5-84aa-97a96f62b942" alt="black" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | Alternative Function #2 |
| ------ | ------ | ------ | ------ | ------ | ------ |
| A1 | PG3  | Low Side 12 (G3)	| FUEL PUMP	            |                           |               |
| A2 | PG4  | Low Side 13 (G4)	| FAN RELAY		        |                           |               |
| A3 |      | Switch SW2    	| DBW+	                | Low Side 10 (D15)	        |               |
| A4 |      | Switch SW3    	| DBW-	                | Low Side 16 (G7)          |               |
| A5 |      | 	                | LSU HEATER-		    | LSU 4.9 CONNECTOR PIN 3	| WHITE WIRE    |
| A6 |      | 	                | LSU IA			    | LSU 4.9 CONNECTOR PIN 5	| GREEN WIRE    |
| A7 |      | 	                | LSU VGND			    | LSU 4.9 CONNECTOR PIN 2	| YELLOW WIRE   |
| A8 |      | 	                | LSU HEATER+		    | LSU 4.9 CONNECTOR PIN 4	| GREY WIRE     |
| B1 | PG2  | Low Side 11 (G2)	|       	            |                           |               |
| B2 | PD5  | Digital In 1 (D5)	|           	        |                   	    |               |
| B3 |      | Switch SW4		| CAN LOW		        | Digital Input 2 (D4)	    |               |
| B4 |      | Switch SW5	 	| CAN HIGH              | Digital Input 3 (D3)	    |               |
| B5 |      | Switch SW7		| KNOCK 1             	| Analogue Input 9 (C5)	    |               |
| B6 |      | 	                | LSU NERMEST	        | LSU 4.9 CONNECTOR PIN 6	| BLACK WIRE    |
| B7 |      | 	                | LSU IP	            | LSU 4.9 CONNECTOR PIN 1	| RED WIRE      |
| B8 |      | +12V from Battery	| +12V Battery	        |                           |               |
| C1 | PD10 | Low Side 10 (D15)	| 		                | 	                        |               |
| C2 | PE2  | VR2+		        | VR1+		            |                           |               |
| C3 |      | VR2-		        | VR1-		            |                           |               |
| C4 |      | VR1-		        | VR2-		            |                           |               |
| C5 | PE3  | VR1+		        | VR2+		            |                           |               |
| C6 |      | Switch SW6    	| KNOCK 2               | Analogue Input 12 (C0)    |               |
| C7 |      | Sensor +5v Supply	| Sensor +5v Supply		|                           |               |
| C8 |      | Ground	        | Ground	            |                           |               |

### Grey Connector


<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core8_24c.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/ebb802ea-ebaf-4b2f-a6b5-6568010a384e" alt="grey" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | 
| ------ | ------ | ------ | ------ | ------ | 
| A1 | PF13  | Low Side 1 (F13)		 |INJECTOR 1		|                                           |
| A2 | PF14  | Low Side 2 (F14)		 |INJECTOR 2		|                                           |
| A3 | PD8  | Low Side 3 (D8)		 |INJECTOR 3		|                                           |
| A4 | PD9  | Low Side 4 (D9)		 |INJECTOR 4		|                                           |
| A5 | PD10 | Low Side 5 (D10)		 |INJECTOR 5		|                                           |
| A6 | PD11 | Low Side 6 (D11)		 |INJECTOR 6		|                                           |
| A7 | PD12 | Low Side 7 (D12)		 |INJECTOR 7		|                                           |
| A8 | PD13 | Low Side 8 (D13)		 |INJECTOR 8		|                                           |
| B1 | PG1 | High Side 1 (G1)		 |COIL 1			| +5v or +12v signal depends on selection	|
| B2 | PG0  | High Side 2 (G0)		 |COIL 2			| +5v or +12v signal depends on selection   |
| B3 | PF15 | High Side 3 (F10)		 |COIL 3		    | +5v or +12v signal depends on selection	|
| B4 | PE11 | High Side 4 (E11)	 	 |COIL 4			| +5v or +12v signal depends on selection	|
| B5 | PE12 | High Side 5 (E12)		 |COIL 5			| +5v or +12v signal depends on selection	|
| B6 | PE13 | High Side 6 (E13)		 |COIL 6		    | +5v or +12v signal depends on selection	|
| B7 | PE14 | High Side 7 (E14)		 |COIL 7		    | +5v or +12v signal depends on selection	|
| B8 | PE15 | High Side 8 (E15)		 |COIL 8		    |                                           |
| C1 | PA6  | Analog Inputs 1 (A6)	 |TPS	            |                                           |
| C2 | PA7  | Analog Inputs 2 (A7)	 |CLT		        | turn SW10 B0 ON to enable 2.49k PULL UP	|
| C3 | PC4  | Analog Inputs 3 (C4)	 |IAT			    | turn SW10 A7 ON to enable 2.49k PULL UP	|
| C4 | PA1  | Analog Inputs 4 (A1)	 |OIL PRESSURE		| 	                                        |
| C5 | PA2  | Analog Inputs 5 (A2)	 |FUEL PRESSURE		| 	                                        |
| C6 | PA3  | Analog Inputs 6 (A3)	 |SPARE ANALOG INPUT|                                           |
| C7 | PA4  | Analog Inputs 7 (A4)	 |SPARE ANALOG INPUT|                                           |
| C8 | PD14 | Low Side 9 (D14 TACHO) |TACHO		        | PULLUP +5v or +12v depends on selection   |





