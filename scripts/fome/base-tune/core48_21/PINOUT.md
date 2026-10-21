# core48_21 (OPF48 v2.1) pinout -> FOME base tune

Source: Benas' connector table (2026-10-21). Applied by `tune_overrides.txt` in this folder on top of the
FOME board defaults (`build_fome.sh` -> `core48_21_base_tune.msq`). "FOME ini label" is what TunerStudio shows.

## Grey connector

| Pin | MCU | Function | FOME field | FOME ini label |
|-|-|-|-|-|
| A1-A8 | PD6-PD13 | Injector 1-8 | injectionPins1-8 | Low Side 1 (D6) ... Low Side 8 (D13) |
| B1 | PG15 | Coil 1 | ignitionPins1 | High Side 8 (G15) |
| B2 | PG8 | Coil 2 | ignitionPins2 | High Side 7 (G8) |
| B3 | PE10 | Coil 3 | ignitionPins3 | High Side 6 (E10) |
| B4 | PE11 | Coil 4 | ignitionPins4 | High Side 5 (E11) |
| B5 | PE12 | Coil 5 | ignitionPins5 | High Side 4 (E12) |
| B6 | PE13 | Coil 6 | ignitionPins6 | High Side 3 (E13) |
| B7 | PE14 | Coil 7 | ignitionPins7 | High Side 2 (E14) |
| B8 | PE15 | Coil 8 | ignitionPins8 | High Side 1 (E15) |
| C1 | PC5 | TPS | tps1_1AdcChannel | Analog Inputs 1 (C5) |
| C2 | PB0 | CLT (SW10 B0 ON = 2.49k pull-up) | clt_adcChannel, clt_bias_resistor 2490 | Analog Inputs 2 (B0) |
| C3 | PA7 | IAT (SW10 A7 ON = 2.49k pull-up) | iat_adcChannel, iat_bias_resistor 2490 | Analog Inputs 3 (A7) |
| C4 | PC4 | Oil pressure | oilPressure_hwChannel | Analog Inputs 4 (C4) |
| C5 | PA5 | Fuel pressure | lowPressureFuel_hwChannel | Analog Inputs 5 (A5) |
| C6 | PA6 | Spare analog | - | Analog Inputs 6 (A6) |
| C7 | PA3 | Spare analog | - | Analog Inputs 7 (A3) |
| C8 | PD14 | Tacho | tachOutputPin | Low Side 9 (D14 TACHO) |

The FOME ini numbers the high side drivers in reverse (G15 = "High Side 8"); the pins above are what count.

## Black connector

| Pin | MCU | Function | FOME field | FOME ini label |
|-|-|-|-|-|
| A1 | PG3 | Fuel pump | fuelPumpPin | Low Side 12 (G3) |
| A2 | PG4 | Fan relay | fanPin | Low Side 13 (G4) |
| A3 | PG5 | Boost | boostControlPin | Low Side 14 (G5) |
| A4 | PG6 | Idle (single solenoid, open loop) | idle_solenoidPin | Low Side 15 (G6) |
| C6 | PG7 | VVT | vvtPins1 | Low Side 16 (G7) |
| C2/C3 | PE2 | VR1 = crank (alt Hall1 PG1 / Hall2 PE7) | triggerInputPins1 | VR1 (E2) |
| C5/C4 | PE3 | VR2 = cam (alt Hall3 PE9 / Hall4 PE8) | camInputs1, vvtMode1 Single Tooth | VR2 (E3) |
| B1 / C1 | - | DBW+/DBW- (SW5/SW6) or Low Side 11 (G2) / Low Side 10 (D15) | FOME defaults (ETB B8/B9/B7) | |
| B2 / B3 | - | CAN L/H (SW4/SW3) or DI1 (D5) / DI2 (D4) | FOME defaults | |
| B4 / B5 | - | DI4 (D2) / AN8 (A4) / Knock1 (C0); DI3 (D3) / AN9 (A1) / Knock2 (C1) | FOME defaults | |
| A5-A8, B6, B7 | - | LSU 4.9 wideband | FOME defaults (on-board O2 C3/A0) | |

## Trigger and engine

- Trigger: 60/2 on the crankshaft (`trigger_type = 60/2`), VR1. The bench emulator also does 36-1 (`36/1`).
- Cam on VR2 is optional: injection Batch + Wasted Spark run without it (switch to Sequential/Individual
  coils once the cam signal is confirmed).
- Engine: 4 cyl, 1-3-4-2, 2.0 L. Cylinder count from the Speeduino tune read from this board; Speeduino
  does not store firing order or displacement, so those are FOME defaults - set them for the real engine.
- Unchanged board defaults: MAP = on-board (A2), battery = on-board sense (B1), stepper idle pins A8/C6/C7
  (stepper idle disabled), SD/SPI/CAN/EGT pins from `board-overlay/core48_21/board_configuration.cpp`.

## Differences vs the compiled-in board defaults (board-overlay/core48_21/board_configuration.cpp)

Firmware code is not changed; the tune overrides fill these in:
- No trigger inputs, cam input, aux outputs (fuel pump, fan, boost, idle, VVT, tacho) or TPS/CLT/IAT/oil/fuel
  pressure channels are set in the firmware defaults (all NONE); injectors, coils and the 2490 ohm CLT/IAT bias match.
- Firmware defaults ignitionMode Single Coil / injectionMode Sequential; the base tune uses Wasted Spark / Batch.
- Stale comments in board_configuration.cpp: MAP `EFI_ADC_2` is PA2 (on-board MAP), not PB0; vbatt `EFI_ADC_9` is
  PB1, not PA7; "PE3 is error LED" is outdated (error LED is PG12, PE3 is VR2).
