/**
 * @file boards/opf33/board_configuration.cpp
 *
 * @brief Configuration defaults for the OPF33 V1.1 board (FOME)
 *
 * @author Ben Brazdziunas,  2022
 */

#include "pch.h"

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

static void setAuxOutputPins() {
	engineConfiguration->fuelPumpPin = Gpio::D9;      // OUT_L4, conn 27
	engineConfiguration->fanPin = Gpio::D8;           // OUT_L3, conn 28
	engineConfiguration->idle.solenoidPin = Gpio::D7; // OUT_L2, conn 29
	engineConfiguration->boostControlPin = Gpio::D6;  // OUT_L1, conn 30
	engineConfiguration->tachOutputPin = Gpio::D14;   // OUT_L9, conn 31
}

static void setTriggerPins() {
	engineConfiguration->triggerInputPins[0] = Gpio::G1;
	engineConfiguration->triggerInputPins[1] = Gpio::Unassigned;
	engineConfiguration->trigger.type = trigger_type_e::TT_TOOTHED_WHEEL_60_2;
}

static void setEtbConfig() {
	// OPF33 V1.1: DBW driver (IFX9201) and throttle-body connector removed
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
	// 5.6k high side/10k low side = 1.56 ratio divider
	engineConfiguration->analogInputDividerCoefficient = 1.56f;

	// 6.34k high side/ 1k low side
	engineConfiguration->vbattDividerCoeff = (6.34 + 1) / 1;

	// Battery sense on PB1 (BRV_CPU)
	engineConfiguration->vbattAdcChannel = EFI_ADC_9;

	engineConfiguration->adcVcc = 3.3f;
}

static void setStepperConfig() {
	// OPF33: no idle stepper hardware; idle is a solenoid on OUT_L2 (PD7)
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
	// OPF33 V1.1: MAX31855 EGT interface removed
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

void setBoardConfigOverrides() {
	setupSdCard();
	setEtbConfig();
	setStepperConfig();
	setupEGT();

	engineConfiguration->clt.config.bias_resistor = 2490;
	engineConfiguration->iat.config.bias_resistor = 2490;

	// CAN 1 bus overwrites
	engineConfiguration->canRxPin = Gpio::D0;
	engineConfiguration->canTxPin = Gpio::D1;

	// OPF33: CAN2 transceiver not fitted
	engineConfiguration->can2RxPin = Gpio::Unassigned;
	engineConfiguration->can2TxPin = Gpio::Unassigned;
}

static void setupDefaultSensorInputs() {
	// on-board 14point7 LSU linear output -> buffer -> PA4
	engineConfiguration->afr.hwChannel = EFI_ADC_4; // PA4
	engineConfiguration->afr.hwChannel2 = EFI_ADC_NONE;
	setEgoSensor(ES_14Point7_Free);

	// on-board MAP_CONV -> buffer -> PA3
	engineConfiguration->map.sensor.hwChannel = EFI_ADC_3; // PA3
	engineConfiguration->map.sensor.type = MT_MPXH6400;

	// CLT/IAT on IN_A1/IN_A2 (pins 12/13) have 2.49k pull-ups to +5V
	engineConfiguration->clt.adcChannel = EFI_ADC_15; // PC5, IN_A1, conn 12
	engineConfiguration->iat.adcChannel = EFI_ADC_8;  // PB0, IN_A2, conn 13
	// TPS on IN_A3 (pin 14) — no 2.49k pull-up, suitable for a 0-5V pot
	engineConfiguration->tps1_1AdcChannel = EFI_ADC_7; // PA7, IN_A3, conn 14

	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;

	engineConfiguration->lps25BaroSensorScl = Gpio::B10;
	engineConfiguration->lps25BaroSensorSda = Gpio::B11;
}

void setBoardDefaultConfiguration() {
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

	strncpy(config->luaScript, R"(

function onTick()

end

    )", efi::size(config->luaScript));
}
