/**
 ******************************************************************************
 * @file    LPS22HHSensor.cpp
 * @author  SRA
 * @version V1.0.0
 * @date    February 2019
 * @brief   Implementation of a LPS22HH pressure sensor.
 ******************************************************************************
 * @attention
 *
 * <h2><center>&copy; COPYRIGHT(c) 2019 STMicroelectronics</center></h2>
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *   1. Redistributions of source code must retain the above copyright notice,
 *      this list of conditions and the following disclaimer.
 *   2. Redistributions in binary form must reproduce the above copyright notice,
 *      this list of conditions and the following disclaimer in the documentation
 *      and/or other materials provided with the distribution.
 *   3. Neither the name of STMicroelectronics nor the names of its contributors
 *      may be used to endorse or promote products derived from this software
 *      without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 ******************************************************************************
 */


/* Includes ------------------------------------------------------------------*/

#include "LPS22HHSensor.h"


/* Class Implementation ------------------------------------------------------*/

/** Constructor
 * @param i2c object of an helper class which handles the I2C peripheral
 * @param address the address of the component's instance
 */
LPS22HHSensor::LPS22HHSensor(TwoWire *i2c, uint8_t address) : dev_i2c(i2c), address(address)
{
  dev_spi = NULL;
  reg_ctx.write_reg = LPS22HH_io_write;
  reg_ctx.read_reg = LPS22HH_io_read;
  reg_ctx.handle = (void *)this;
  enabled = 0;
}

/** Constructor
 * @param spi object of an helper class which handles the SPI peripheral
 * @param cs_pin the chip select pin
 * @param spi_speed the SPI speed
 */
LPS22HHSensor::LPS22HHSensor(SPIClass *spi, int cs_pin, uint32_t spi_speed) : dev_spi(spi), cs_pin(cs_pin), spi_speed(spi_speed)
{
  reg_ctx.write_reg = LPS22HH_io_write;
  reg_ctx.read_reg = LPS22HH_io_read;
  reg_ctx.handle = (void *)this;
  dev_i2c = NULL;
  address = 0;
  enabled = 0;
}

/**
 * @brief  Configure the sensor in order to be used
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::begin()
{
  if (dev_spi) {
    // Configure CS pin
    pinMode(cs_pin, OUTPUT);
    digitalWrite(cs_pin, HIGH);
  }

  /* Disable MIPI I3C(SM) interface */
  if (lps22hh_i3c_interface_set(&reg_ctx, LPS22HH_I3C_DISABLE) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Power down the device, set Low Noise Enable (bit 5), clear One Shot (bit 4) */
  if (lps22hh_data_rate_set(&reg_ctx, (lps22hh_odr_t)(LPS22HH_POWER_DOWN | 0x10)) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Disable low-pass filter on LPS22HH pressure data */
  if (lps22hh_lp_bandwidth_set(&reg_ctx, LPS22HH_LPF_ODR_DIV_2) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Set block data update mode */
  if (lps22hh_block_data_update_set(&reg_ctx, PROPERTY_ENABLE) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Set autoincrement for multi-byte read/write */
  if (lps22hh_auto_increment_set(&reg_ctx, PROPERTY_ENABLE) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  last_odr = LPS22HH_25_Hz;
  enabled = 0;

  return LPS22HH_OK;
}

/**
 * @brief  Disable the sensor and relative resources
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::end()
{
  /* Disable pressure and temperature sensor */
  if (Disable() != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Reset CS configuration */
  if (dev_spi) {
    // Configure CS pin
    pinMode(cs_pin, INPUT);
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get WHO_AM_I value
 * @param  Id the WHO_AM_I value
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::ReadID(uint8_t *Id)
{
  if (lps22hh_device_id_get(&reg_ctx, Id) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Enable the LPS22HH pressure sensor
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Enable()
{
  /* Check if the component is already enabled */
  if (enabled == 1U) {
    return LPS22HH_OK;
  }

  /* Output data rate selection. */
  if (lps22hh_data_rate_set(&reg_ctx, last_odr) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  enabled = 1;

  return LPS22HH_OK;
}

/**
 * @brief  Disable the LPS22HH pressure sensor
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Disable()
{
  /* Check if the component is already disabled */
  if (enabled == 0U) {
    return LPS22HH_OK;
  }

  /* Get current output data rate. */
  if (lps22hh_data_rate_get(&reg_ctx, &last_odr) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }
  /* Output data rate selection - power down. */
  if (lps22hh_data_rate_set(&reg_ctx, LPS22HH_POWER_DOWN) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }


  enabled = 0;

  return LPS22HH_OK;
}


/**
 * @brief  Get output data rate
 * @param  Odr the output data rate value
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::GetOutputDataRate(float *Odr)
{
  LPS22HHStatusTypeDef ret = LPS22HH_OK;
  lps22hh_odr_t odr_low_level;

  if (lps22hh_data_rate_get(&reg_ctx, &odr_low_level) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  switch (odr_low_level) {
    case LPS22HH_POWER_DOWN:
      *Odr = 0.0f;
      break;

    case LPS22HH_1_Hz:
      *Odr = 1.0f;
      break;

    case LPS22HH_10_Hz:
      *Odr = 10.0f;
      break;

    case LPS22HH_25_Hz:
      *Odr = 25.0f;
      break;

    case LPS22HH_50_Hz:
      *Odr = 50.0f;
      break;

    case LPS22HH_75_Hz:
      *Odr = 75.0f;
      break;

    case LPS22HH_100_Hz:
      *Odr = 100.0f;
      break;

    case LPS22HH_200_Hz:
      *Odr = 200.0f;
      break;

    default:
      ret = LPS22HH_ERROR;
      break;
  }

  return ret;
}

/**
 * @brief  Set the LPS22HH pressure sensor output data rate
 * @param  Odr the output data rate value to be set
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::SetOutputDataRate(float Odr)
{
  /* Check if the component is enabled */
  if (enabled == 1U) {
    return SetOutputDataRate_When_Enabled(Odr);
  } else {
    return SetOutputDataRate_When_Disabled(Odr);
  }
}


/**
 * @brief  Set output data rate
 * @param  Odr the output data rate value to be set
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::SetOutputDataRate_When_Enabled(float Odr)
{
  lps22hh_odr_t new_odr;

  new_odr = (Odr <=   1.0f) ? LPS22HH_1_Hz
            : (Odr <=  10.0f) ? LPS22HH_10_Hz
            : (Odr <=  25.0f) ? LPS22HH_25_Hz
            : (Odr <=  50.0f) ? LPS22HH_50_Hz
            : (Odr <=  75.0f) ? LPS22HH_75_Hz
            : (Odr <= 100.0f) ? LPS22HH_100_Hz
            :                   LPS22HH_200_Hz;

  if (lps22hh_data_rate_set(&reg_ctx, new_odr) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  if (lps22hh_data_rate_get(&reg_ctx, &last_odr) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set output data rate when disabled
 * @param  Odr the output data rate value to be set
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::SetOutputDataRate_When_Disabled(float Odr)
{
  last_odr = (Odr <=   1.0f) ? LPS22HH_1_Hz
             : (Odr <=  10.0f) ? LPS22HH_10_Hz
             : (Odr <=  25.0f) ? LPS22HH_25_Hz
             : (Odr <=  50.0f) ? LPS22HH_50_Hz
             : (Odr <=  75.0f) ? LPS22HH_75_Hz
             : (Odr <= 100.0f) ? LPS22HH_100_Hz
             :                   LPS22HH_200_Hz;

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH pressure value
 * @param  Value pointer where the pressure value is written
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::GetPressure(float *Value)
{
  axis1bit32_t data_raw_pressure;

  (void)memset(data_raw_pressure.u8bit, 0x00, sizeof(int32_t));
  if (lps22hh_pressure_raw_get(&reg_ctx, data_raw_pressure.u8bit) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  *Value = LPS22HH_FROM_LSB_TO_hPa((float)(data_raw_pressure.i32bit));

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH pressure data ready bit value
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_PRESS_DRDY_Status(uint8_t *Status)
{
  if (lps22hh_press_flag_data_ready_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH temperature value
 * @param  Value pointer where the temperature value is written
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::GetTemperature(float *Value)
{
  axis1bit16_t data_raw_temperature;

  (void)memset(data_raw_temperature.u8bit, 0x00, sizeof(int16_t));
  if (lps22hh_temperature_raw_get(&reg_ctx, data_raw_temperature.u8bit) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  *Value = LPS22HH_FROM_LSB_TO_degC((float)(data_raw_temperature.i16bit));

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH temperature data ready bit value
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_TEMP_DRDY_Status(uint8_t *Status)
{
  if (lps22hh_temp_flag_data_ready_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH register value
 * @param  Reg address to be written
 * @param  Data value to be written
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Read_Reg(uint8_t Reg, uint8_t *Data)
{
  if (lps22hh_read_reg(&reg_ctx, Reg, Data, 1) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the LPS22HH register value
 * @param  pObj the device pObj
 * @param  Reg address to be written
 * @param  Data value to be written
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Write_Reg(uint8_t Reg, uint8_t Data)
{
  if (lps22hh_write_reg(&reg_ctx, Reg, &Data, 1) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH FIFO data level
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_FIFO_Data(float *Press, float *Temp)
{
  axis1bit32_t data_raw_pressure;
  axis1bit16_t data_raw_temperature;

  (void)memset(data_raw_pressure.u8bit, 0x00, sizeof(int32_t));
  if (lps22hh_fifo_pressure_raw_get(&reg_ctx, data_raw_pressure.u8bit) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  *Press = LPS22HH_FROM_LSB_TO_hPa((float)(data_raw_pressure.i32bit));

  (void)memset(data_raw_temperature.u8bit, 0x00, sizeof(int16_t));
  if (lps22hh_fifo_temperature_raw_get(&reg_ctx, data_raw_temperature.u8bit) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  *Temp = LPS22HH_FROM_LSB_TO_degC((float)(data_raw_temperature.i16bit));

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH FIFO threshold
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_FIFO_FTh_Status(uint8_t *Status)
{
  if (lps22hh_fifo_wtm_flag_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH FIFO full status
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_FIFO_Full_Status(uint8_t *Status)
{
  if (lps22hh_fifo_full_flag_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH FIFO OVR status
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_FIFO_Ovr_Status(uint8_t *Status)
{
  if (lps22hh_fifo_ovr_flag_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH FIFO data level
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_FIFO_Level(uint8_t *Status)
{
  if (lps22hh_fifo_data_level_get(&reg_ctx, Status) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Reset the FIFO interrupt
 * @param  interrupt The FIFO interrupt to be reset; values: 0 = FTH; 1 = FULL; 2 = OVR
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Reset_FIFO_Interrupt(uint8_t interrupt)
{
  switch (interrupt) {
    case 0:
      if (lps22hh_fifo_threshold_on_int_set(&reg_ctx, PROPERTY_DISABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    case 1:
      if (lps22hh_fifo_full_on_int_set(&reg_ctx, PROPERTY_DISABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    case 2:
      if (lps22hh_fifo_ovr_on_int_set(&reg_ctx, PROPERTY_DISABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    default:
      return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the FIFO interrupt
 * @param  interrupt The FIFO interrupt to be reset; values: 0 = FTH; 1 = FULL; 2 = OVR
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Set_FIFO_Interrupt(uint8_t interrupt)
{
  switch (interrupt) {
    case 0:
      if (lps22hh_fifo_threshold_on_int_set(&reg_ctx, PROPERTY_ENABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    case 1:
      if (lps22hh_fifo_full_on_int_set(&reg_ctx, PROPERTY_ENABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    case 2:
      if (lps22hh_fifo_ovr_on_int_set(&reg_ctx, PROPERTY_ENABLE) != LPS22HH_OK) {
        return LPS22HH_ERROR;
      }
      break;
    default:
      return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the FIFO mode
 * @param  Mode the FIFO mode to be set
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Set_FIFO_Mode(uint8_t Mode)
{
  /* Verify that the passed parameter contains one of the valid values */
  switch ((lps22hh_f_mode_t)Mode) {
    case LPS22HH_BYPASS_MODE:
    case LPS22HH_FIFO_MODE:
    case LPS22HH_STREAM_MODE:
    case LPS22HH_STREAM_TO_FIFO_MODE:
    case LPS22HH_BYPASS_TO_STREAM_MODE:
    case LPS22HH_BYPASS_TO_FIFO_MODE:
      break;
    default:
      return LPS22HH_ERROR;
  }

  if (lps22hh_fifo_mode_set(&reg_ctx, (lps22hh_f_mode_t)Mode) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the LPS22HH FIFO data level
 * @param  Status the status of data ready bit
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Set_FIFO_Watermark_Level(uint8_t Watermark)
{
  if (lps22hh_fifo_watermark_set(&reg_ctx, Watermark) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the LPS22HH stop on watermark function
 * @param  Stop the state of stop on watermark function
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Stop_FIFO_On_Watermark(uint8_t Stop)
{
  if (lps22hh_fifo_stop_on_wtm_set(&reg_ctx, Stop) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Set the LPS22HH One Shot Mode
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Set_One_Shot()
{
  /* Start One Shot Measurement */
  if (lps22hh_data_rate_set(&reg_ctx, LPS22HH_ONE_SHOOT) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  return LPS22HH_OK;
}

/**
 * @brief  Get the LPS22HH One Shot Status
 * @param  Status pointer to the one shot status (1 means measurements available, 0 means measurements not available yet)
 * @retval 0 in case of success, an error code otherwise
 */
LPS22HHStatusTypeDef LPS22HHSensor::Get_One_Shot_Status(uint8_t *Status)
{
  uint8_t p_da;
  uint8_t t_da;

  /* Get DataReady for pressure */
  if (lps22hh_press_flag_data_ready_get(&reg_ctx, &p_da) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  /* Get DataReady for temperature */
  if (lps22hh_temp_flag_data_ready_get(&reg_ctx, &t_da) != LPS22HH_OK) {
    return LPS22HH_ERROR;
  }

  if (p_da && t_da) {
    *Status = 1;
  } else {
    *Status = 0;
  }

  return LPS22HH_OK;
}

int32_t LPS22HH_io_write(void *handle, uint8_t WriteAddr, uint8_t *pBuffer, uint16_t nBytesToWrite)
{
  return ((LPS22HHSensor *)handle)->IO_Write(pBuffer, WriteAddr, nBytesToWrite);
}

int32_t LPS22HH_io_read(void *handle, uint8_t ReadAddr, uint8_t *pBuffer, uint16_t nBytesToRead)
{
  return ((LPS22HHSensor *)handle)->IO_Read(pBuffer, ReadAddr, nBytesToRead);
}
