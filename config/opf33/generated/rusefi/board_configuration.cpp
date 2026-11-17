/**
 * @file boards/core8/board_configuration.cpp
 *
 * GENERATED from config/opf33/board.yaml. Do not edit by hand.
 * Hand-written fallback: config/opf33/board_configuration.cpp
 *
 * @brief Configuration defaults for the OPF33 V1.1 board
 * @author Ben Brazdziunas
 */

#include "pch.h"
#include "settings.h"
#include "board_overrides.h"

static void setInjectorPins() {
	engineConfiguration->injectionPinMode = OM_DEFAULT;

	engineConfiguration->injectionPins[0] = Gpio::D13;
	engineConfiguration->injectionPins[1] = Gpio::D12;
	engineConfiguration->injectionPins[2] = Gpio::D11;
	engineConfiguration->injectionPins[3] = Gpio::D10;
	engineConfiguration->injectionPins[4] = Gpio::Unassigned;
	engineConfiguration->injectionPins[5] = Gpio::Unassigned;
	engineConfiguration->injectionPins[6] = Gpio::Unassigned;
	engineConfiguration->injectionPins[7] = Gpio::Unassigned;
}

static void setIgnitionPins() {
	engineConfiguration->ignitionPinMode = OM_DEFAULT;

	engineConfiguration->ignitionPins[0] = Gpio::E15;
	engineConfiguration->ignitionPins[1] = Gpio::E14;
	engineConfiguration->ignitionPins[2] = Gpio::E13;
	engineConfiguration->ignitionPins[3] = Gpio::E12;
	engineConfiguration->ignitionPins[4] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[5] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[6] = Gpio::Unassigned;
	engineConfiguration->ignitionPins[7] = Gpio::Unassigned;
}

void setSdCardConfigurationOverrides(void) {
}

static void setEtbConfig() {
	// OPF33 V1.1: DBW / ETB disabled in board.yaml
	engineConfiguration->etbIo[0].controlPin = Gpio::Unassigned;
	engineConfiguration->etbIo[0].directionPin1 = Gpio::Unassigned;
	engineConfiguration->etbIo[0].directionPin2 = Gpio::Unassigned;
	engineConfiguration->etbIo[0].disablePin = Gpio::Unassigned;
	engineConfiguration->etbIo[1].controlPin = Gpio::Unassigned;
	engineConfiguration->etbIo[1].directionPin1 = Gpio::Unassigned;
	engineConfiguration->etbIo[1].directionPin2 = Gpio::Unassigned;
	engineConfiguration->etbIo[1].disablePin = Gpio::Unassigned;
	engineConfiguration->etbFunctions[0] = DC_None;
	engineConfiguration->etbFunctions[1] = DC_None;
	engineConfiguration->etb_use_two_wires = false;
}

static void setupVbatt() {
	engineConfiguration->analogInputDividerCoefficient = 1.56f;
	engineConfiguration->vbattDividerCoeff = 7.34f;
	engineConfiguration->vbattAdcChannel = EFI_ADC_9;
	engineConfiguration->adcVcc = 3.3f;
}

static void setStepperConfig() {
	engineConfiguration->idle.stepperDirectionPin = Gpio::Unassigned;
	engineConfiguration->idle.stepperStepPin = Gpio::Unassigned;
	engineConfiguration->stepperEnablePin = Gpio::Unassigned;
	engineConfiguration->useStepperIdle = false;
}

static void setupSdCard() {
	engineConfiguration->sdCardSpiDevice = SPI_DEVICE_3;
	engineConfiguration->is_enabled_spi_3 = true;
	engineConfiguration->spi3sckPin = Gpio::C10;
	engineConfiguration->spi3misoPin = Gpio::C11;
	engineConfiguration->spi3mosiPin = Gpio::C12;
}

static void setupEGT() {
	engineConfiguration->spi2sckPin = Gpio::Unassigned;
	engineConfiguration->spi2misoPin = Gpio::Unassigned;
	engineConfiguration->spi2mosiPin = Gpio::Unassigned;
	engineConfiguration->is_enabled_spi_2 = false;
	engineConfiguration->max31855spiDevice = SPI_NONE;
	for (int i = 0; i < EGT_CHANNEL_COUNT; i++) {
		engineConfiguration->max31855_cs[i] = Gpio::Unassigned;
	}
}

Gpio getCommsLedPin() {
	return Gpio::G13;
}

Gpio getRunningLedPin() {
	return Gpio::G10;
}

Gpio getWarningLedPin() {
	return Gpio::G11;
}

static void opf33_boardConfigOverrides() {
	setupSdCard();
	setEtbConfig();
	setStepperConfig();
	setupEGT();

	engineConfiguration->clt.config.bias_resistor = 2490;
	engineConfiguration->iat.config.bias_resistor = 2490;

	engineConfiguration->binarySerialTxPin = Gpio::A9;
	engineConfiguration->binarySerialRxPin = Gpio::A10;
	engineConfiguration->tunerStudioSerialSpeed = SERIAL_SPEED;
	engineConfiguration->uartConsoleSerialSpeed = SERIAL_SPEED;

	engineConfiguration->canRxPin = Gpio::D0;
	engineConfiguration->canTxPin = Gpio::D1;
	engineConfiguration->can2RxPin = Gpio::Unassigned;
	engineConfiguration->can2TxPin = Gpio::Unassigned;
}

static void setAuxOutputPins() {
	engineConfiguration->fuelPumpPin = Gpio::D9;
	engineConfiguration->fanPin = Gpio::D8;
	engineConfiguration->idle.solenoidPin = Gpio::D7;
	engineConfiguration->boostControlPin = Gpio::D6;
	engineConfiguration->tachOutputPin = Gpio::D14;
}

static void setTriggerPins() {
	engineConfiguration->triggerInputPins[0] = Gpio::G1;
	engineConfiguration->triggerInputPins[1] = Gpio::Unassigned;
	engineConfiguration->trigger.type = trigger_type_e::TT_TOOTHED_WHEEL_60_2;
}

static void setupDefaultSensorInputs() {
	engineConfiguration->afr.hwChannel = EFI_ADC_4;
	engineConfiguration->afr.hwChannel2 = EFI_ADC_NONE;
	setEgoSensor(ES_14Point7_Free);

	engineConfiguration->map.sensor.hwChannel = EFI_ADC_3;
	engineConfiguration->map.sensor.type = MT_MPXH6400;

	engineConfiguration->clt.adcChannel = EFI_ADC_15;
	engineConfiguration->iat.adcChannel = EFI_ADC_8;
	engineConfiguration->tps1_1AdcChannel = EFI_ADC_7;

	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;
	engineConfiguration->lps25BaroSensorScl = Gpio::B10;
	engineConfiguration->lps25BaroSensorSda = Gpio::B11;
}

static void opf33_boardDefaultConfiguration() {
	setInjectorPins();
	setIgnitionPins();
	setAuxOutputPins();
	setTriggerPins();
	setupDefaultSensorInputs();
	engineConfiguration->enableSoftwareKnock = false;
	setupVbatt();

	engineConfiguration->canWriteEnabled = true;
	engineConfiguration->canReadEnabled = true;
	engineConfiguration->canSleepPeriodMs = 50;
	engineConfiguration->canBaudRate = B500KBPS;
	engineConfiguration->can2BaudRate = B500KBPS;
	engineConfiguration->sdCardCsPin = Gpio::B3;

	setLuaScript(R"(
function onTick()

end
    )");
}

void setup_custom_board_overrides() {
	custom_board_DefaultConfiguration = opf33_boardDefaultConfiguration;
	custom_board_ConfigOverrides = opf33_boardConfigOverrides;
}
