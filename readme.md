

# core48 v2.2

## Features

- 8 Injectors
- 8 Coils
- 8 Low Side Switch
- 4 VR / 8 Hall Triggers
- 4 Digital Inputs
- 8 Analogue 0-5v inputs (all can be used as temperature inputs via 2.49k pull up resistor SW10 and SW11)
- DBW
- 2 Wideband (14point7)
- 2 Canbus
- 2 EGT
- 4bar map
- Onboard Barometer
- Onboard SD card/Removable SD Card
- Bluetooth

## Firmware

## FOME (RUSEFI fork) Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download FOME Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/fome/fome_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download FOME TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/fome/fome_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-FOME%20Console-purple?style=for-the-badge&logo=download&logoColor=white "Download FOME Console")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/fome/fome_console.zip)
<!-- END LATEST DOWNLOAD BUTTON -->

## RUSEFI Firmware
(Right click and 'Save link as...')

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20Firmware-blue?style=for-the-badge&logo=download&logoColor=white "Download RusEFI Firmware")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/rusefi/rusefi_firmware.bin)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20TunerStudio%20INI-green?style=for-the-badge&logo=download&logoColor=white "Download RusEFI TunerStudio INI")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/rusefi/rusefi_tunerstudio.ini)
<!-- END LATEST DOWNLOAD BUTTON -->

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-RusEFI%20Console-purple?style=for-the-badge&logo=download&logoColor=white "Download RusEFI Console")](https://raw.githubusercontent.com/opelpanfan/OPF_ECU/core48_22/rusefi/rusefi_console.zip)
<!-- END LATEST DOWNLOAD BUTTON -->

## Interactive Pinout Manual 

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Pinout%20Manual-black?style=for-the-badge&logo=download&logoColor=white "Pinout Manual")](https://opelpanfan.github.io/OPF_ECU/core48_22.html)
<!-- END LATEST DOWNLOAD BUTTON -->

### Black Connector

<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core48_21.html" target="_blank">
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

### Grey Connector


<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core48_21.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/ebb802ea-ebaf-4b2f-a6b5-6568010a384e" alt="grey" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | 
| ------ | ------ | ------ | ------ | ------ | 
| A1 | PD6  | Low Side 1 (D6)		     |INJECTOR 1	    	|                                           |
| A2 | PD7  | Low Side 2 (D7)		     |INJECTOR 2	    	|                                           |
| A3 | PD8  | Low Side 3 (D8)		     |INJECTOR 3	    	|                                           |
| A4 | PD9  | Low Side 4 (D9)		     |INJECTOR 4	    	|                                           |
| A5 | PD10 | Low Side 5 (D10)		   |INJECTOR 5	    	|                                           |
| A6 | PD11 | Low Side 6 (D11)		   |INJECTOR 6		    |                                           |
| A7 | PD12 | Low Side 7 (D12)		   |INJECTOR 7		    |                                           |
| A8 | PD13 | Low Side 8 (D13)		   |INJECTOR 8		    |                                           |
| B1 | PG15 | High Side 1 (G15)		   |COIL 1			      | +5v or +12v signal depends on selection	  |
| B2 | PG8  | High Side 2 (G8)		   |COIL 2			      | +5v or +12v signal depends on selection   |
| B3 | PE10 | High Side 3 (E10)		   |COIL 3		        | +5v or +12v signal depends on selection	  |
| B4 | PE11 | High Side 4 (E11)	 	   |COIL 4			      | +5v or +12v signal depends on selection	  |
| B5 | PE12 | High Side 5 (E12)		   |COIL 5			      | +5v or +12v signal depends on selection	  |
| B6 | PE13 | High Side 6 (E13)		   |COIL 6		        | +5v or +12v signal depends on selection	  |
| B7 | PE14 | High Side 7 (E14)		   |COIL 7		        | +5v or +12v signal depends on selection	  |
| B8 | PE15 | High Side 8 (E15)		   |COIL 8		        |                                           |
| C1 | PC5  | Analog Inputs 1 (C5)	 |TPS	              |                                           |
| C2 | PB0  | Analog Inputs 2 (B0)	 |CLT		            | turn SW10 B0 ON to enable 2.49k PULL UP	  |
| C3 | PA7  | Analog Inputs 3 (A7)	 |IAT			          | turn SW10 A7 ON to enable 2.49k PULL UP	  |
| C4 | PC4  | Analog Inputs 4 (C4)	 |OIL PRESSURE		  | HALL 4 (PE8)	                            |
| C5 | PA5  | Analog Inputs 5 (A5)	 |FUEL PRESSURE		  | HALL 3 (PE9)	                            |
| C6 | PA6  | Analog Inputs 6 (A6)	 |SPARE ANALOG INPUT|                                           |
| C7 | PA3  | Analog Inputs 7 (A3)	 |SPARE ANALOG INPUT|                                           |
| C8 | PD14 | Low Side 9 (D14 TACHO) |TACHO		          | PULLUP +5v or +12v depends on selection   |


## PCB Layout

## TOP
![front](https://github.com/opelpanfan/OPF_ECU/assets/12942077/39e08eaa-056f-47bf-bc9c-adae13f9d11d)


## BACK
![back](https://github.com/opelpanfan/OPF_ECU/assets/12942077/b780d395-3b82-46ec-8465-948469103bc0)


## Solder jumper configuration

| Switch ID | Link to Connector | Image  | RED | BLUE	 | GREEN |
| ------ | ------ | ------ | ------ | ------ |  ------ |
| SW1   | B_B5  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/a8f089bf-756e-499e-aeaf-23d290c80077)  | Knock 2 (C1)  | Analog Inputs 9 (A1) | Digital Input 3 (D3) |
| SW2   | B_B4  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/60eecaba-4185-443d-ba55-6d47e375f6af)  | Digital Input 4 (D2)   | Analog Inputs 8 (A4) | Knock 1 (C0) |
| SW3   | B_B3  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/7317de4f-f90f-421f-a8b6-e6b397e22e0e)  | CAN HIGH  | Digital Input 2 (D4) | USB D- |
| SW4   | B_B2  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/afe5f827-868f-4d1c-8b96-0ee988f302a9)  | USB D+  | Digital Input 1 (D5) | CAN LOW |
| SW5   | B_B1  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/3b56dfbf-93a3-4483-ab4d-dab7f33d0787)  | DBW+ | Low Side 11 (G2)   |  |
| SW6   | B_C1  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/4e700a4b-39fb-4627-a118-844ac0052b64)  | DBW- | Low Side 10 (D15)  |  |
| TACHO | G_C8  |  ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/84274391-8342-446c-9d9b-830f0544a226)  | TACHO PULL UP to +12v  | TACHO PULL UP to +5v |  |
| IGNITION OUTPUT | COIL Signal  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/120a9391-3466-4170-857a-9ee5fe4d4820)   | COIL Trigger +12v  | COIL Trigger +5v |  |

## Solder jumper configuration for Additional Outputs
| Switch ID | Link to Connector | Image  | RED | BLUE	 | GREEN |
| ------ | ------ | ------ | ------ | ------ |  ------ |
| O1 OUTPUT | B_A2  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/7721ebb9-10fd-4e13-b313-ce84879af818) | Low Side 13 (G4)  | O1 SWITCH |  |
| O2 OUTPUT | B_A3  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/49f23855-923e-4ae0-8dd5-e888767934f4) | Low Side 14 (G5)  | O2 SWITCH |  |
| O3 OUTPUT | B_A4  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/258e7309-b414-49b8-9f6e-34849ad63a73) | Low Side 15 (G6)  | O3 SWITCH |  |
| O4 OUTPUT | B_C6  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/0dad5b56-ec19-4573-a50f-10c866ff9606) | Low Side 16 (G7)  | O4 SWITCH |  |
| O1 SWITCH | O1 OUTPUT  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/80021f76-063c-4e8c-9625-203b20545482) | CAN HIGH  | STEP2 B | EGT1 - |
| O2 SWITCH | O2 OUTPUT  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/212dd901-a98d-45c3-a89d-ebef2f109cac) | CAN LOW  | STEP2 A | EGT1 + |
| O3 SWITCH | O3 OUTPUT  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/81efa24f-96f3-4bf1-8e74-566e5a6bd659) | USB D+  | STEP1 A | EGT2 - |
| O4 SWITCH | O4 OUTPUT  | ![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/fce76c37-d508-4bb1-8566-49ba7cb04fe6) | USB D-  | STEP1 B | EGT2 + |

### VR Trigger Configuration

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/83f4c142-d014-474f-8db0-7748346d7d1c)

### HALL Trigger Configuration

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/3e8c9698-e620-4e2e-aa5c-6c7e95a41adc)

### SW10 and SW11: Analogue input PULLUP resistors (2.49k) to +5V for Temperature Sensor

>Analogue input pull up settings to use for temperature inputs:
>Most of Analogue inputs can be used as temperature inputs with 2.49Kohm pull up to +5v resistors.
>These resistors can be enabled by flipping toggle switch to ON position.

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/4b32ae2e-9675-4ed0-840b-b0a25cef0e7a)

### SW12 Digital Input PULLUP resistors (680k) to +5v

>Digital input 680kohm pull up resistors to +5v.
>If your digital input requires pull up resistor taht can be enabled by flipping toggle switch to ON possition.

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/35bf0126-d9e4-4bc6-bb26-321129c39fa8)

### SW9 CAN bus terminator Resistors and Knock Audio Filters

>1. toggle switch is to ON possition to enable 120ohm terminating resistor on CAN1
>2. toggle switch is to ON possition to enable 120ohm terminating resistor on CAN2
>3. toggle switch is to ON possition to enable 3.3nF filter capacitor on KNOCK 1 Input
>4. toggle switch is to ON possition to enable 3.3nF filter capacitor on KNOCK 2 Input

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/ff682a8b-d209-444a-9393-c2f8b3ee4286)

## Additional Connectors

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/97ef0acd-f3cf-4ad0-a3d1-6431f46757c7)


### CAN Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/d09fa081-5cd6-4d9a-be30-1ee47d5a534f)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | CAN 1 LOW |
| 2 |  | CAN 1 HIGH |
| 3 |  | CAN 2 LOW |
| 4 |  | CAN 2 HIGH |

### USB Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/28440f01-4af8-4c36-8c39-1c8cbae31018)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | USB +5V |
| 2 |  | USB D- |
| 3 |  | USB D+ |
| 4 |  | GND |

### Stepper Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/e34e9e4d-1b7a-4d78-b032-acf8d3970b42)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | STEP 1B |
| 2 |  | STEP 1A |
| 3 |  | STEP 2A |
| 4 |  | STEP 2B |

### VR3/VR4 Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/7487d04a-ca39-4ea0-89ba-61334c59820c)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 | PE4/PF13  | VR3+/HALL5 (F13) |
| 2 | PF14 | VR3-/HALL6 (F14) |
| 3 | PF15 | VR4-/HALL8 (F15) |
| 4 | PE5/PG0 | VR4+/HALL7 (G0) |

### EGT Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/a79caca7-1704-4548-ba6f-a7a69c43e911)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | EGT1 T- |
| 2 |  | EGT1 T+ |
| 3 |  | EGT2 T- |
| 4 |  | EGT2 T+ |

### Knock/Serial Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/a540029c-f379-491f-b8d2-05d715955fec)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | UART6 RX |
| 2 |  | UART6 TX |
| 3 |  | KNOCK 2 Audio |
| 4 |  | KNOCK 1 Audio |

### DBW Connector
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/7795b322-d11e-4130-8336-8c679de8507d)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | GND |
| 2 |  | +5V |
| 3 |  | ET- |
| 4 |  | ET+ |
| 5 |  | Analog Inputs 8 (A4) |
| 6 |  | Analog Inputs 9 (A1) |

### LSU Connector

![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/6e7645d5-8103-496a-bb16-77c106c47582)
![image](https://github.com/opelpanfan/OPF_ECU/assets/12942077/05f5cd9a-93ac-4810-8be9-47d00f090758)

| Pin   | STM32 PIN | Function  |
| ------ | ------ | ------ |
| 1 |  | LSU Connector 4 |
| 2 |  | LSU Connector 3 |
| 3 |  | LSU Connector 2 |
| 4 |  | LSU Connector 1 |
| 5 |  | LSU Connector 6 |
| 6 |  | LSU Connector 5 |




