/**
 * @file boards/core8/board_configuration.cpp
 *
 * @brief Configuration defaults for the royalEFI Spark board
 *
 * @author Ben Brazdziunas,  2022
 */

#include "pch.h"

static void setInjectorPins() {
	engineConfiguration->injectionPinMode = OM_DEFAULT;

	engineConfiguration->injectionPins[0] = Gpio::D6;
	engineConfiguration->injectionPins[1] = Gpio::D7;
	engineConfiguration->injectionPins[2] = Gpio::Unassigned;
	engineConfiguration->injectionPins[3] = Gpio::Unassigned;
	engineConfiguration->injectionPins[4] = Gpio::Unassigned;
	engineConfiguration->injectionPins[5] = Gpio::Unassigned;
	engineConfiguration->injectionPins[6] = Gpio::Unassigned;
	engineConfiguration->injectionPins[7] = Gpio::Unassigned;
}

static void setIgnitionPins() {
	engineConfiguration->ignitionPinMode = OM_DEFAULT;

	engineConfiguration->ignitionPins[0] = Gpio::E15;
	engineConfiguration->ignitionPins[1] = Gpio::E14;
	engineConfiguration->ignitionPins[2] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[3] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[4] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[5] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[6] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[7] = Gpio::Unassigned;
}


void setSdCardConfigurationOverrides(void) {
}

static void setupVbatt() {
	// 5.6k high side/10k low side = 1.56 ratio divider
	engineConfiguration->analogInputDividerCoefficient = 1.56f;
	
	// 6.34k high side/ 1k low side
	engineConfiguration->vbattDividerCoeff = (6.34 + 1) / 1; 

	// Battery sense on PA7
	engineConfiguration->vbattAdcChannel = EFI_ADC_9;

	engineConfiguration->adcVcc = 3.3f;
}

static void setupSdCard() {
	
	//SD CARD overwrites
	engineConfiguration->sdCardSpiDevice = SPI_DEVICE_3;	
	

	engineConfiguration->is_enabled_spi_3 = true;
	engineConfiguration->spi3sckPin = Gpio::C10;
	engineConfiguration->spi3misoPin = Gpio::C11;
	engineConfiguration->spi3mosiPin = Gpio::C12;
}


Gpio getRunningLedPin() {
	return Gpio::G10;
}

Gpio getWarningLedPin() {
	return Gpio::G11;
}
// PE3 is error LED, configured in board.mk
Gpio getCommsLedPin() {
	return Gpio::G13;
}


void setBoardConfigOverrides() {
	setupSdCard();

	engineConfiguration->clt.config.bias_resistor = 2490;
	engineConfiguration->iat.config.bias_resistor = 2490;

	//SERIAL 
	engineConfiguration->binarySerialTxPin = Gpio::A9;
	engineConfiguration->binarySerialRxPin = Gpio::A10;
	engineConfiguration->tunerStudioSerialSpeed = SERIAL_SPEED;
	engineConfiguration->uartConsoleSerialSpeed = SERIAL_SPEED;



	//CAN 1 bus overwrites
	engineConfiguration->canRxPin = Gpio::D0;
	engineConfiguration->canTxPin = Gpio::D1;

}

static void setupDefaultSensorInputs() {

	engineConfiguration->afr.hwChannel = EFI_ADC_13; //PC3
	setEgoSensor(ES_14Point7_Free);
	
	engineConfiguration->map.sensor.hwChannel = EFI_ADC_14; //PC4
	engineConfiguration->map.sensor.type = MT_MPXH6400;
	
	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;

	engineConfiguration->lps25BaroSensorScl = Gpio::B10;
	engineConfiguration->lps25BaroSensorSda = Gpio::B11;

}


void setBoardDefaultConfiguration(void) {
	setInjectorPins();
	setIgnitionPins();
	setupDefaultSensorInputs();
	setupVbatt();


	engineConfiguration->canWriteEnabled = true;
	engineConfiguration->canReadEnabled = true;
	engineConfiguration->canSleepPeriodMs = 50;

	engineConfiguration->canBaudRate = B500KBPS;

	engineConfiguration->sdCardCsPin = Gpio::B4;
		
	strncpy(config->luaScript, R"(

gearSensor = Sensor.new("DetectedGear")
gearCalibration = findCurveIndex("GearADC")

function onTick()
	if gearCalibration > 0 then
		selectorVoltage = getAuxAnalog(0)
		if selectorVoltage ~= nil and selectorVoltage > 0 and selectorVoltage < 5 then 
			yValue = curve(gearCalibration, selectorVoltage)
 			if yValue > -1 then
				gearSensor : set(yValue)
				print("selectorVoltage: " ..selectorVoltage)
			end
		end
	end
end


    )", efi::size(config->luaScript));
}