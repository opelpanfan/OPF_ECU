/*
 * OPF (opelpanfan) board support for Speeduino - see opf_board.h.
 * Behaviour ported from the legacy OPF opf_core.ino (ECU_Build 63e9f3c): status LEDs, onboard I2C barometer
 * (LPS22HH or LPS25HB) and the second CAN interface. SPI flash EEPROM and the pin map are handled by the
 * generated edits in board_stm32_official.* and init.cpp.
 */
#include "globals.h"

#if defined(OPF_BOARD)
#include "opf_board.h"

#if defined(OPF_I2C_BARO)
  #include <Wire.h>
  static TwoWire opfBaroWire(OPF_BARO_SDA, OPF_BARO_SCL);
  #if defined(OPF_BARO_LPS25HB)
    #include "src/LPS25HB/LPS25HBSensor.h"
    static LPS25HBSensor opfBaro(&opfBaroWire, LPS25HB_ADDRESS_LOW);
  #else
    #include "src/LPS22HH/LPS22HHSensor.h"
    static LPS22HHSensor opfBaro(&opfBaroWire, LPS22HH_I2C_ADD_L);
  #endif
  static bool opfBaroOk = false;
#endif

#if defined(OPF_CAN2) && defined(HAL_CAN_MODULE_ENABLED)
  STM32_CAN Can1(CAN2, ALT, RX_SIZE_256, TX_SIZE_16);
#endif

static inline void opfLedInit(uint8_t pin, uint8_t state) { pinMode(pin, OUTPUT); digitalWrite(pin, state); }

void opfBoardInit(void)
{
#if defined(OPF_LED_RUNNING)
  opfLedInit(OPF_LED_RUNNING, LOW);
#endif
#if defined(OPF_LED_WARNING)
  opfLedInit(OPF_LED_WARNING, LOW);
#endif
#if defined(OPF_LED_ALERT)
  opfLedInit(OPF_LED_ALERT, HIGH); // on during init, follows engine protection afterwards
#endif
#if defined(OPF_LED_COMS)
  opfLedInit(OPF_LED_COMS, LOW);
#endif

#if defined(OPF_I2C_BARO)
  opfBaroWire.begin();
  opfBaroOk = (opfBaro.begin() == 0);
  #if defined(OPF_BARO_LPS25HB)
    if (opfBaroOk) { opfBaroOk = (opfBaro.SetODR(7.0f) == 0); }
  #endif
  if (opfBaroOk) { opfBaroOk = (opfBaro.Enable() == 0); }
#endif

#if defined(OPF_CAN2) && defined(HAL_CAN_MODULE_ENABLED)
  Can1.begin();
  Can1.setBaudRate(500000);
  Can1.enableFIFO();
#endif

#if defined(OPF_LED_ALERT)
  digitalWrite(OPF_LED_ALERT, LOW);
#endif
}

bool opfReadBaro(void)
{
#if defined(OPF_I2C_BARO)
  if (!opfBaroOk) { return false; }
  float pressure = 0.0f; // hPa
  if (opfBaro.GetPressure(&pressure) != 0) { return false; }
  float kpa = pressure / 10.0f;
  if ((kpa < 10.0f) || (kpa > 255.0f)) { return false; } // implausible -> fall back to the upstream MAP/ext. baro logic
  currentStatus.baro = (uint8_t)(kpa + 0.5f);
  return true;
#else
  return false;
#endif
}

void opfBoardLoop(void)
{
#if defined(OPF_LED_COMS)
  if (Serial.available() > 0) { digitalToggle(OPF_LED_COMS); }
  else { digitalWrite(OPF_LED_COMS, LOW); }
#endif
#if defined(OPF_LED_ALERT)
  if (BIT_CHECK(LOOP_TIMER, BIT_TIMER_4HZ)) { digitalWrite(OPF_LED_ALERT, (currentStatus.engineProtectStatus != 0U) ? HIGH : LOW); }
#endif
#if defined(OPF_LED_RUNNING)
  if (BIT_CHECK(LOOP_TIMER, BIT_TIMER_10HZ)) { digitalToggle(OPF_LED_RUNNING); }
#endif
}

#endif // OPF_BOARD
