/**
 * @file boards/core8/board_configuration.cpp
 *
 * @brief Configuration defaults for the core8 board
 *
 * @author Ben Brazdziunas,  2022
 */

#include "pch.h"

static void setInjectorPins() {
	engineConfiguration->injectionPinMode = OM_DEFAULT;

	engineConfiguration->injectionPins[0] = Gpio::F13;
	engineConfiguration->injectionPins[1] = Gpio::F14;
	engineConfiguration->injectionPins[2] = Gpio::D8;
	engineConfiguration->injectionPins[3] = Gpio::D9;
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

static void setEtbConfig() {
	// TLE9201 driver
	// This chip has three control pins:
	// DIR - sets direction of the motor
	// PWM - pwm control (enable high, coast low)
	// DIS - disables motor (enable low)

	// Throttle #1
	// PWM pin
	engineConfiguration->etbIo[0].controlPin = Gpio::B8;
	// DIR pin
	engineConfiguration->etbIo[0].directionPin1 = Gpio::B9;
	// Disable pin
	engineConfiguration->etbIo[0].disablePin = Gpio::B7;
	// Unused
	engineConfiguration->etbIo[0].directionPin2 = Gpio::Unassigned;

	// Throttle #2
	// PWM pin
	engineConfiguration->etbIo[1].controlPin = Gpio::Unassigned;
	// DIR pin
	engineConfiguration->etbIo[1].directionPin1 = Gpio::Unassigned;
	// Disable pin
	engineConfiguration->etbIo[1].disablePin = Gpio::Unassigned;
	// Unused
	engineConfiguration->etbIo[1].directionPin2 = Gpio::Unassigned;

	// we only have pwm/dir, no dira/dirb
	engineConfiguration->etb_use_two_wires = false;
}

static void setupVbatt() {
	// 5.6k high side/10k low side = 1.56 ratio divider
	engineConfiguration->analogInputDividerCoefficient = 1.56f;
	
	// 6.34k high side/ 1k low side
	engineConfiguration->vbattDividerCoeff = (6.34 + 1) / 1; 

	// Battery sense on PA7
	engineConfiguration->vbattAdcChannel = EFI_ADC_0;

	engineConfiguration->adcVcc = 3.3f;
}

static void setStepperConfig() {
	engineConfiguration->idle.stepperDirectionPin = Gpio::F7;
	engineConfiguration->idle.stepperStepPin = Gpio::F8;
	engineConfiguration->stepperEnablePin = Gpio::F9;
}

void setBoardConfigOverrides() {
	setupVbatt();
	setEtbConfig();
	setStepperConfig();

	// PE3 is error LED, configured in board.mk
	engineConfiguration->communicationLedPin = Gpio::G13;
	engineConfiguration->runningLedPin = Gpio::G10;
	engineConfiguration->warningLedPin = Gpio::G11;

	engineConfiguration->clt.config.bias_resistor = 2490;
	engineConfiguration->iat.config.bias_resistor = 2490;

	//CAN 1 bus overwrites
	engineConfiguration->canRxPin = Gpio::D0;
	engineConfiguration->canTxPin = Gpio::D1;

	//CAN 2 bus overwrites
	engineConfiguration->can2RxPin = Gpio::B5;
	engineConfiguration->can2TxPin = Gpio::B6;
}

static void setupDefaultSensorInputs() {

	engineConfiguration->afr.hwChannel = EFI_ADC_11;
	setEgoSensor(ES_14Point7_Free);
	
	engineConfiguration->map.sensor.hwChannel = EFI_ADC_5;
	engineConfiguration->map.sensor.type = MT_MPX4250A;
	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;

	engineConfiguration->lps25BaroSensorScl = Gpio::B10;
	engineConfiguration->lps25BaroSensorSda = Gpio::B11;

	engineConfiguration->clt.adcChannel = EFI_ADC_7;
	engineConfiguration->iat.adcChannel = EFI_ADC_6;
	engineConfiguration->tps1_1AdcChannel = EFI_ADC_14;

	
	engineConfiguration->oilPressure.hwChannel = EFI_ADC_1;
	engineConfiguration->lowPressureFuel.hwChannel = EFI_ADC_2;

	

}

void setBoardDefaultConfiguration(void) {
	setInjectorPins();
	setIgnitionPins();
	setupDefaultSensorInputs();

	
	setAlgorithm(LM_SPEED_DENSITY);

	engineConfiguration->specs.cylindersCount = 4;
	engineConfiguration->specs.firingOrder = FO_1_3_4_2;
	engineConfiguration->trigger.type = TT_MITSUBISHI;
	engineConfiguration->globalTriggerAngleOffset = 671;
	
	engineConfiguration->triggerInputPins[0] = Gpio::E3;
	engineConfiguration->triggerInputPins[1] = Gpio::E2;
	engineConfiguration->camInputs[0] = Gpio::Unassigned;
	
	engineConfiguration->cranking.rpm = 400;
	engineConfiguration->crankingTimingAngle = -715;

	engineConfiguration->specs.displacement = 1.998;
	strcpy(engineConfiguration->engineMake, "Mitsubishi");
	strcpy(engineConfiguration->engineCode, "4G63");	
	engineConfiguration->vehicleWeight = 1280;

	engineConfiguration->isForcedInduction = true;
	engineConfiguration->compressionRatio = 8.5;
	engineConfiguration->cylinderBore = 85;
	engineConfiguration->rpmHardLimit = 7200;	
	engineConfiguration->boostCutPressure = 200;
	engineConfiguration->tachPulsePerRev = 2;

	engineConfiguration->ignitionMode = IM_INDIVIDUAL_COILS;
	engineConfiguration->crankingInjectionMode = IM_SIMULTANEOUS;
	engineConfiguration->injectionMode = IM_SIMULTANEOUS;

	engineConfiguration->injector.flow = 630;
	
    engineConfiguration->boostControlPin = Gpio::G4;
	engineConfiguration->boostType = CLOSED_LOOP;
	
	engineConfiguration->acSwitch = Gpio::Unassigned;
	engineConfiguration->fuelPumpPin = Gpio::D11;
	engineConfiguration->fanPin = Gpio::D10;
	engineConfiguration->mainRelayPin = Gpio::E8;
    engineConfiguration->tachOutputPin = Gpio::D4;
	engineConfiguration->malfunctionIndicatorPin = Gpio::E9;

	
	engineConfiguration->clutchDownPin = Gpio::F4;
	engineConfiguration->clutchDownPinMode = PI_PULLDOWN;
	engineConfiguration->launchActivationMode = CLUTCH_INPUT_LAUNCH;


	
	engineConfiguration->isSdCardEnabled = true;

	engineConfiguration->canWriteEnabled = true;
	engineConfiguration->canReadEnabled = true;
	engineConfiguration->canSleepPeriodMs = 50;

	engineConfiguration->canBaudRate = B500KBPS;
	engineConfiguration->can2BaudRate = B500KBPS;
	engineConfiguration->canNbcType = CAN_AIM_DASH;
}
