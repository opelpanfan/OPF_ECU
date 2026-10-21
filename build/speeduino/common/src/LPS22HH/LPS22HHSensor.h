/**
 ******************************************************************************
 * @file    LPS22HHSensor.h
 * @author  SRA
 * @version V1.0.0
 * @date    February 2019
 * @brief   Abstract Class of a LPS22HH pressure sensor.
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


/* Prevent recursive inclusion -----------------------------------------------*/

#ifndef __LPS22HHSensor_H__
#define __LPS22HHSensor_H__


/* Includes ------------------------------------------------------------------*/

#include "Wire.h"
#include "SPI.h"
#include "lps22hh_reg.h"

/* Defines -------------------------------------------------------------------*/



/* Typedefs ------------------------------------------------------------------*/

typedef enum {
  LPS22HH_OK = 0,
  LPS22HH_ERROR = -1
} LPS22HHStatusTypeDef;


/* Class Declaration ---------------------------------------------------------*/

/**
 * Abstract class of a LPS22HH pressure sensor.
 */
class LPS22HHSensor {
  public:
    LPS22HHSensor(TwoWire *i2c, uint8_t address = LPS22HH_I2C_ADD_H);
    LPS22HHSensor(SPIClass *spi, int cs_pin, uint32_t spi_speed = 2000000);
    LPS22HHStatusTypeDef begin();
    LPS22HHStatusTypeDef end();
    LPS22HHStatusTypeDef ReadID(uint8_t *Id);
    LPS22HHStatusTypeDef Enable();
    LPS22HHStatusTypeDef Disable();
    LPS22HHStatusTypeDef GetOutputDataRate(float *Odr);
    LPS22HHStatusTypeDef SetOutputDataRate(float Odr);
    LPS22HHStatusTypeDef GetPressure(float *Value);
    LPS22HHStatusTypeDef Get_PRESS_DRDY_Status(uint8_t *Status);

    LPS22HHStatusTypeDef GetTemperature(float *Value);
    LPS22HHStatusTypeDef Get_TEMP_DRDY_Status(uint8_t *Status);

    LPS22HHStatusTypeDef Read_Reg(uint8_t reg, uint8_t *Data);
    LPS22HHStatusTypeDef Write_Reg(uint8_t reg, uint8_t Data);

    LPS22HHStatusTypeDef Get_FIFO_Data(float *Press, float *Temp);
    LPS22HHStatusTypeDef Get_FIFO_FTh_Status(uint8_t *Status);
    LPS22HHStatusTypeDef Get_FIFO_Full_Status(uint8_t *Status);
    LPS22HHStatusTypeDef Get_FIFO_Ovr_Status(uint8_t *Status);
    LPS22HHStatusTypeDef Get_FIFO_Level(uint8_t *Status);
    LPS22HHStatusTypeDef Reset_FIFO_Interrupt(uint8_t interrupt);
    LPS22HHStatusTypeDef Set_FIFO_Interrupt(uint8_t interrupt);
    LPS22HHStatusTypeDef Set_FIFO_Mode(uint8_t Mode);
    LPS22HHStatusTypeDef Set_FIFO_Watermark_Level(uint8_t Watermark);
    LPS22HHStatusTypeDef Stop_FIFO_On_Watermark(uint8_t Stop);

    LPS22HHStatusTypeDef Set_One_Shot();
    LPS22HHStatusTypeDef Get_One_Shot_Status(uint8_t *Status);


    /**
     * @brief Utility function to read data.
     * @param  pBuffer: pointer to data to be read.
     * @param  RegisterAddr: specifies internal address register to be read.
     * @param  NumByteToRead: number of bytes to be read.
     * @retval 0 if ok, an error code otherwise.
     */
    uint8_t IO_Read(uint8_t *pBuffer, uint8_t RegisterAddr, uint16_t NumByteToRead)
    {
      if (dev_spi) {
        dev_spi->beginTransaction(SPISettings(spi_speed, MSBFIRST, SPI_MODE3));

        digitalWrite(cs_pin, LOW);

        /* Write Reg Address */
        dev_spi->transfer(RegisterAddr | 0x80);
        /* Read the data */
        for (uint16_t i = 0; i < NumByteToRead; i++) {
          *(pBuffer + i) = dev_spi->transfer(0x00);
        }

        digitalWrite(cs_pin, HIGH);

        dev_spi->endTransaction();

        return 0;
      }

      if (dev_i2c) {
        dev_i2c->beginTransmission(((uint8_t)(((address) >> 1) & 0x7F)));
        dev_i2c->write(RegisterAddr);
        dev_i2c->endTransmission(false);

        dev_i2c->requestFrom(((uint8_t)(((address) >> 1) & 0x7F)), (uint8_t) NumByteToRead);

        int i = 0;
        while (dev_i2c->available()) {
          pBuffer[i] = dev_i2c->read();
          i++;
        }

        return 0;
      }

      return 1;
    }

    /**
     * @brief Utility function to write data.
     * @param  pBuffer: pointer to data to be written.
     * @param  RegisterAddr: specifies internal address register to be written.
     * @param  NumByteToWrite: number of bytes to write.
     * @retval 0 if ok, an error code otherwise.
     */
    uint8_t IO_Write(uint8_t *pBuffer, uint8_t RegisterAddr, uint16_t NumByteToWrite)
    {
      if (dev_spi) {
        dev_spi->beginTransaction(SPISettings(spi_speed, MSBFIRST, SPI_MODE3));

        digitalWrite(cs_pin, LOW);

        /* Write Reg Address */
        dev_spi->transfer(RegisterAddr);
        /* Write the data */
        for (uint16_t i = 0; i < NumByteToWrite; i++) {
          dev_spi->transfer(pBuffer[i]);
        }

        digitalWrite(cs_pin, HIGH);

        dev_spi->endTransaction();

        return 0;
      }

      if (dev_i2c) {
        dev_i2c->beginTransmission(((uint8_t)(((address) >> 1) & 0x7F)));

        dev_i2c->write(RegisterAddr);
        for (uint16_t i = 0 ; i < NumByteToWrite ; i++) {
          dev_i2c->write(pBuffer[i]);
        }

        dev_i2c->endTransmission(true);

        return 0;
      }

      return 1;
    }

  private:
    LPS22HHStatusTypeDef SetOutputDataRate_When_Enabled(float Odr);
    LPS22HHStatusTypeDef SetOutputDataRate_When_Disabled(float Odr);

    /* Helper classes. */
    TwoWire *dev_i2c;
    SPIClass *dev_spi;

    /* Configuration */
    uint8_t address;
    int cs_pin;
    uint32_t spi_speed;

    lps22hh_odr_t last_odr;
    uint8_t enabled;

    lps22hh_ctx_t reg_ctx;

};

#ifdef __cplusplus
extern "C" {
#endif
int32_t LPS22HH_io_write(void *handle, uint8_t WriteAddr, uint8_t *pBuffer, uint16_t nBytesToWrite);
int32_t LPS22HH_io_read(void *handle, uint8_t ReadAddr, uint8_t *pBuffer, uint16_t nBytesToRead);
#ifdef __cplusplus
}
#endif

#endif
