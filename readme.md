

# Teensy 48

![PXL_20240110_124119080](https://github.com/opelpanfan/OPF_ECU/assets/12942077/a79a7790-c60c-4dd3-baf1-0e0608057663)

## Features

- 8 Injectors
- 8 Coils
- 8 Low Side Switch
- 2 VR / 2 Hall Triggers
- 4 Digital Inputs
- 8 Analogue 0-5v inputs
- 1 Wideband (14point7)
- 1 Canbus
- 4bar map
- Onboard Barometer

## Firmware

## Speeduino Teensy Flasher
<div>
<a href="https://github.com/opelpanfan/OPF_ECU/blob/teensy48_36/speeduino/Speeduino%20Teensy%20Flasher.msi" download>
  https://github.com/opelpanfan/OPF_ECU/blob/teensy48_36/speeduino/Speeduino%20Teensy%20Flasher.msi
</a>
</div>

## Speeduino Firmware

https://github.com/opelpanfan/OPF_ECU/tree/teensy48_36/speeduino

## Interactive Pinout Manual 

https://opelpanfan.github.io/OPF_ECU/teensy48_36.html

### Black Connector

<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core48_21.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/cb34225e-63c1-4ae5-84aa-97a96f62b942" alt="black" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | Alternative Function #2 |
| ------ | ------ | ------ | ------ | ------ | ------ |
| A1 | PG3  | Low Side 12 (G3)	| FUEL PUMP	            |                           |               |
| A2 | PG4  | Low Side 13 (G4)	| FAN RELAY		        |                           |               |
| A3 | PG5  | Low Side 14 (G5)	| BOOST	                |                           |               |
| A4 | PG6  | Low Side 15 (G6)	| IDLE	                |                           |               |
| A5 |      | 	                | LSU HEATER-		    | LSU 4.9 CONNECTOR PIN 3	| WHITE WIRE    |
| A6 |      | 	                | LSU IA			    | LSU 4.9 CONNECTOR PIN 5	| GREEN WIRE    |
| A7 |      | 	                | LSU VGND			    | LSU 4.9 CONNECTOR PIN 2	| YELLOW WIRE   |
| A8 |      | 	                | LSU HEATER+		    | LSU 4.9 CONNECTOR PIN 4	| GREY WIRE     |
| B1 |      | Switch SW5		| DBW+		            | Low Side 11 (G2)	        |               |
| B2 |      | Switch SW4		| CAN LOW		        | Digital Input 1 (D5)	    | USB D+        |
| B3 |      | Switch SW3		| CAN HIGH		        | Digital Input 2 (D4)	    | USB D-        |
| B4 |      | Switch SW2	 	| Digital Input 4 (D2)  | Analogue Input 8 (A4)	    | Knock 1 (C0)  |
| B5 |      | Switch SW1		| Digital Input 3 (D3)	| Analogue Input 9 (A1)	    | Knock 2 (C1)  |
| B6 |      | 	                | LSU NERMEST	        | LSU 4.9 CONNECTOR PIN 6	| BLACK WIRE    |
| B7 |      | 	                | LSU IP	            | LSU 4.9 CONNECTOR PIN 1	| RED WIRE      |
| B8 |      | +12V from Battery	| +12V Battery	        |                           |               |
| C1 |      | Switch SW6		| DBW-		            | Low Side 10 (D15)	        |               |
| C2 | PE2  | VR1+		        | VR1+		            | HALL 1 (PG1)	            |               |
| C3 |      | VR1-		        | VR1-		            | HALL 2 (PE7)	            |               |
| C4 |      | VR2-		        | VR2-		            | HALL 4 (PE8)	            |               |
| C5 | PE3  | VR2+		        | VR2+		            | HALL 3 (PE9)	            |               |
| C6 | PG7  | Low Side 16 (G7)	| VVTI	                |                           |               |
| C7 |      | Sensor +5v Supply	| Sensor +5v Supply		|                           |               |
| C8 |      | Ground	        | Ground	            |                           |               |

### Grey Connector


<div align="center">
<a href="https://opelpanfan.github.io/OPF_ECU/core48_21.html" target="_blank">
  <img src="https://github.com/opelpanfan/OPF_ECU/assets/12942077/ebb802ea-ebaf-4b2f-a6b5-6568010a384e" alt="grey" width="100%" />
</a>
</div>

| Pin Number | STM32 Pin Number | TS Name  | Typical Function | Alternative Function #1	 | 
| ------ | ------ | ------ | ------ | ------ | 
| A1 | PD6  | Low Side 1 (D6)		 |INJECTOR 1		|                                           |
| A2 | PD7  | Low Side 2 (D7)		 |INJECTOR 2		|                                           |
| A3 | PD8  | Low Side 3 (D8)		 |INJECTOR 3		|                                           |
| A4 | PD9  | Low Side 4 (D9)		 |INJECTOR 4		|                                           |
| A5 | PD10 | Low Side 5 (D10)		 |INJECTOR 5		|                                           |
| A6 | PD11 | Low Side 6 (D11)		 |INJECTOR 6		|                                           |
| A7 | PD12 | Low Side 7 (D12)		 |INJECTOR 7		|                                           |
| A8 | PD13 | Low Side 8 (D13)		 |INJECTOR 8		|                                           |
| B1 | PG15 | High Side 1 (G15)		 |COIL 1			| +5v or +12v signal depends on selection	|
| B2 | PG8  | High Side 2 (G8)		 |COIL 2			| +5v or +12v signal depends on selection   |
| B3 | PE10 | High Side 3 (E10)		 |COIL 3		    | +5v or +12v signal depends on selection	|
| B4 | PE11 | High Side 4 (E11)	 	 |COIL 4			| +5v or +12v signal depends on selection	|
| B5 | PE12 | High Side 5 (E12)		 |COIL 5			| +5v or +12v signal depends on selection	|
| B6 | PE13 | High Side 6 (E13)		 |COIL 6		    | +5v or +12v signal depends on selection	|
| B7 | PE14 | High Side 7 (E14)		 |COIL 7		    | +5v or +12v signal depends on selection	|
| B8 | PE15 | High Side 8 (E15)		 |COIL 8		    |                                           |
| C1 | PC5  | Analog Inputs 1 (C5)	 |TPS	            |                                           |
| C2 | PB0  | Analog Inputs 2 (B0)	 |CLT		        | turn SW10 B0 ON to enable 2.49k PULL UP	|
| C3 | PA7  | Analog Inputs 3 (A7)	 |IAT			    | turn SW10 A7 ON to enable 2.49k PULL UP	|
| C4 | PC4  | Analog Inputs 4 (C4)	 |OIL PRESSURE		| HALL 4 (PE8)	                            |
| C5 | PA5  | Analog Inputs 5 (A5)	 |FUEL PRESSURE		| HALL 3 (PE9)	                            |
| C6 | PA6  | Analog Inputs 6 (A6)	 |SPARE ANALOG INPUT|                                           |
| C7 | PA3  | Analog Inputs 7 (A3)	 |SPARE ANALOG INPUT|                                           |
| C8 | PD14 | Low Side 9 (D14 TACHO)		 |TACHO		        | PULLUP +5v or +12v depends on selection   |

