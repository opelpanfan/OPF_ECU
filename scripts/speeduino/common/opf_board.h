/*
 * OPF (opelpanfan) board support for Speeduino on STM32F407 based OPF ECUs (core48, core8, ...).
 * Copied into the Speeduino source tree by scripts/speeduino/build_speeduino.sh; compiled only when OPF_BOARD is defined
 * (set by the generated PlatformIO env from scripts/speeduino/board-overlay/<variant>/board.json).
 */
#ifndef OPF_BOARD_H
#define OPF_BOARD_H

#if defined(OPF_BOARD)
#include <Arduino.h>

void opfBoardInit(void);  // called at the start of initBoard() (after loadConfig(), before initialiseMAPBaro())
void opfBoardLoop(void);  // called once per main loop iteration, right after LOOP_TIMER is latched
bool opfReadBaro(void);   // called from readBaro()/initialiseMAPBaro(); true = currentStatus.baro was set from the onboard sensor

#if defined(OPF_CAN2) && defined(HAL_CAN_MODULE_ENABLED)
  #include "src/STM32_CAN/STM32_CAN.h"
  extern STM32_CAN Can1; // CAN2 peripheral (PB5 RX / PB6 TX); Can0 = CAN1 on PD0/PD1 is provided by upstream
#endif

#endif // OPF_BOARD
#endif // OPF_BOARD_H
