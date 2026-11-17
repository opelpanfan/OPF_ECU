#!/usr/bin/env python3
"""Generate rusEFI and FOME board overlays and a board manual from board.yaml.

Usage:
    python3 tools/boardgen/generate_board.py config/opf33/board.yaml

Writes:
    config/<id>/generated/rusefi/   board_configuration.cpp, board.mk, prepend.txt, board.env
    config/<id>/generated/fome/     board_configuration.cpp, board.mk, prepend.txt, compile_<id>.sh
    config/<id>/generated/README.md
    config/<id>/readme.md           (same manual; official docs / release notes)

Does not overwrite hand-written board.h or board_configuration.cpp in
config/<id>/ or config/<id>_fome/. Those remain the CI fallback until
the generated files are adopted.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")


def gpio(pin: str | None) -> str:
    if not pin or str(pin).lower() in {"null", "none", "unassigned"}:
        return "Gpio::Unassigned"
    p = str(pin).strip().upper()
    if p.startswith("P") and len(p) >= 3 and p[1].isalpha():
        return f"Gpio::{p[1]}{p[2:]}"
    return f"Gpio::{p}"


def pad8(pins: list) -> list:
    out = list(pins)
    while len(out) < 8:
        out.append("Unassigned")
    return out


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    if not data or "board" not in data:
        sys.exit(f"{path}: missing board: key")
    return data


def _pin_assigns(field: str, pins: list) -> str:
    lines = []
    for i, p in enumerate(pad8(pins)):
        val = "Gpio::Unassigned" if p == "Unassigned" else gpio(p)
        lines.append(f"\tengineConfiguration->{field}[{i}] = {val};")
    return "\n".join(lines)


def render_rusefi_cpp(d: dict) -> str:
    b = d["board"]
    o = d["outputs"]
    s = d["sensors"]
    t = d["trigger"]
    c = d["can"]
    sd = d["sd_card"]
    ser = d["serial"]
    baro = d["baro"]
    leds = d["leds"]
    analog = d["analog"]
    ident = b["id"].replace("-", "_")
    lua = (d.get("lua") or "function onTick()\n\nend\n").rstrip() + "\n"
    inj_lines = _pin_assigns("injectionPins", o["injectors"])
    ign_lines = _pin_assigns("ignitionPins", o["ignition"])
    overlay = d["firmware"]["rusefi"]["overlay_as"]

    return f"""/**
 * @file boards/{overlay}/board_configuration.cpp
 *
 * GENERATED from config/{b["id"]}/board.yaml. Do not edit by hand.
 * Hand-written fallback: config/{b["id"]}/board_configuration.cpp
 *
 * @brief Configuration defaults for the {b["name"]} {b.get("hardware_revision", "")} board
 * @author {b.get("author", "")}
 */

#include "pch.h"
#include "settings.h"
#include "board_overrides.h"

static void setInjectorPins() {{
	engineConfiguration->injectionPinMode = OM_DEFAULT;

{inj_lines}
}}

static void setIgnitionPins() {{
	engineConfiguration->ignitionPinMode = OM_DEFAULT;

{ign_lines}
}}

void setSdCardConfigurationOverrides(void) {{
}}

static void setEtbConfig() {{
	// {b["name"]} {b.get("hardware_revision", "")}: DBW / ETB disabled in board.yaml
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
}}

static void setupVbatt() {{
	engineConfiguration->analogInputDividerCoefficient = {analog["input_divider"]}f;
	engineConfiguration->vbattDividerCoeff = {analog["vbatt_divider"]}f;
	engineConfiguration->vbattAdcChannel = {s["vbatt"]["adc"]};
	engineConfiguration->adcVcc = {analog["adc_vcc"]}f;
}}

static void setStepperConfig() {{
	engineConfiguration->idle.stepperDirectionPin = Gpio::Unassigned;
	engineConfiguration->idle.stepperStepPin = Gpio::Unassigned;
	engineConfiguration->stepperEnablePin = Gpio::Unassigned;
	engineConfiguration->useStepperIdle = false;
}}

static void setupSdCard() {{
	engineConfiguration->sdCardSpiDevice = SPI_DEVICE_{sd["spi"]};
	engineConfiguration->is_enabled_spi_3 = true;
	engineConfiguration->spi3sckPin = {gpio(sd["sck"])};
	engineConfiguration->spi3misoPin = {gpio(sd["miso"])};
	engineConfiguration->spi3mosiPin = {gpio(sd["mosi"])};
}}

static void setupEGT() {{
	engineConfiguration->spi2sckPin = Gpio::Unassigned;
	engineConfiguration->spi2misoPin = Gpio::Unassigned;
	engineConfiguration->spi2mosiPin = Gpio::Unassigned;
	engineConfiguration->is_enabled_spi_2 = false;
	engineConfiguration->max31855spiDevice = SPI_NONE;
	for (int i = 0; i < EGT_CHANNEL_COUNT; i++) {{
		engineConfiguration->max31855_cs[i] = Gpio::Unassigned;
	}}
}}

Gpio getCommsLedPin() {{
	return {gpio(leds["comms"])};
}}

Gpio getRunningLedPin() {{
	return {gpio(leds["running"])};
}}

Gpio getWarningLedPin() {{
	return {gpio(leds["warning"])};
}}

static void {ident}_boardConfigOverrides() {{
	setupSdCard();
	setEtbConfig();
	setStepperConfig();
	setupEGT();

	engineConfiguration->clt.config.bias_resistor = {s["clt"]["bias_ohms"]};
	engineConfiguration->iat.config.bias_resistor = {s["iat"]["bias_ohms"]};

	engineConfiguration->binarySerialTxPin = {gpio(ser["tx"])};
	engineConfiguration->binarySerialRxPin = {gpio(ser["rx"])};
	engineConfiguration->tunerStudioSerialSpeed = SERIAL_SPEED;
	engineConfiguration->uartConsoleSerialSpeed = SERIAL_SPEED;

	engineConfiguration->canRxPin = {gpio(c["can1"]["rx"])};
	engineConfiguration->canTxPin = {gpio(c["can1"]["tx"])};
	engineConfiguration->can2RxPin = Gpio::Unassigned;
	engineConfiguration->can2TxPin = Gpio::Unassigned;
}}

static void setAuxOutputPins() {{
	engineConfiguration->fuelPumpPin = {gpio(o["fuel_pump"])};
	engineConfiguration->fanPin = {gpio(o["fan"])};
	engineConfiguration->idle.solenoidPin = {gpio(o["idle_solenoid"])};
	engineConfiguration->boostControlPin = {gpio(o["boost"])};
	engineConfiguration->tachOutputPin = {gpio(o["tacho"])};
}}

static void setTriggerPins() {{
	engineConfiguration->triggerInputPins[0] = {gpio(t["primary"]["pin"])};
	engineConfiguration->triggerInputPins[1] = Gpio::Unassigned;
	engineConfiguration->trigger.type = trigger_type_e::{t["type"]};
}}

static void setupDefaultSensorInputs() {{
	engineConfiguration->afr.hwChannel = {s["afr"]["adc"]};
	engineConfiguration->afr.hwChannel2 = EFI_ADC_NONE;
	setEgoSensor({s["afr"]["ego"]});

	engineConfiguration->map.sensor.hwChannel = {s["map"]["adc"]};
	engineConfiguration->map.sensor.type = {s["map"]["type"]};

	engineConfiguration->clt.adcChannel = {s["clt"]["adc"]};
	engineConfiguration->iat.adcChannel = {s["iat"]["adc"]};
	engineConfiguration->tps1_1AdcChannel = {s["tps"]["adc"]};

	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;
	engineConfiguration->lps25BaroSensorScl = {gpio(baro["scl"])};
	engineConfiguration->lps25BaroSensorSda = {gpio(baro["sda"])};
}}

static void {ident}_boardDefaultConfiguration() {{
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
	engineConfiguration->sdCardCsPin = {gpio(sd["cs"])};

	setLuaScript(R"(
{lua}    )");
}}

void setup_custom_board_overrides() {{
	custom_board_DefaultConfiguration = {ident}_boardDefaultConfiguration;
	custom_board_ConfigOverrides = {ident}_boardConfigOverrides;
}}
"""


def render_fome_cpp(d: dict) -> str:
    b = d["board"]
    o = d["outputs"]
    s = d["sensors"]
    t = d["trigger"]
    c = d["can"]
    sd = d["sd_card"]
    baro = d["baro"]
    leds = d["leds"]
    analog = d["analog"]
    lua = (d.get("lua") or "function onTick()\n\nend\n").rstrip() + "\n"
    inj_lines = _pin_assigns("injectionPins", o["injectors"])
    ign_lines = _pin_assigns("ignitionPins", o["ignition"])
    overlay = d["firmware"]["fome"]["overlay_as"]

    return f"""/**
 * @file boards/{overlay}/board_configuration.cpp
 *
 * GENERATED from config/{b["id"]}/board.yaml. Do not edit by hand.
 * Hand-written fallback: config/{b["id"]}_fome/board_configuration.cpp
 *
 * FOME at the pinned revision still uses setBoardDefaultConfiguration /
 * setBoardConfigOverrides and strncpy(config->luaScript, ...).
 *
 * @brief FOME configuration defaults for the {b["name"]} {b.get("hardware_revision", "")} board
 * @author {b.get("author", "")}
 */

#include "pch.h"

static void setInjectorPins() {{
	engineConfiguration->injectionPinMode = OM_DEFAULT;

{inj_lines}
}}

static void setIgnitionPins() {{
	engineConfiguration->ignitionPinMode = OM_DEFAULT;

{ign_lines}
}}

static void setAuxOutputPins() {{
	engineConfiguration->fuelPumpPin = {gpio(o["fuel_pump"])};
	engineConfiguration->fanPin = {gpio(o["fan"])};
	engineConfiguration->idle.solenoidPin = {gpio(o["idle_solenoid"])};
	engineConfiguration->boostControlPin = {gpio(o["boost"])};
	engineConfiguration->tachOutputPin = {gpio(o["tacho"])};
}}

static void setTriggerPins() {{
	engineConfiguration->triggerInputPins[0] = {gpio(t["primary"]["pin"])};
	engineConfiguration->triggerInputPins[1] = Gpio::Unassigned;
	engineConfiguration->trigger.type = trigger_type_e::{t["type"]};
}}

void setSdCardConfigurationOverrides(void) {{
}}

static void setEtbConfig() {{
	engineConfiguration->etbIo[0].controlPin = Gpio::Unassigned;
	engineConfiguration->etbIo[0].directionPin1 = Gpio::Unassigned;
	engineConfiguration->etbIo[0].directionPin2 = Gpio::Unassigned;
	engineConfiguration->etbIo[0].disablePin = Gpio::Unassigned;
	engineConfiguration->etbIo[1].controlPin = Gpio::Unassigned;
	engineConfiguration->etbIo[1].directionPin1 = Gpio::Unassigned;
	engineConfiguration->etbIo[1].directionPin2 = Gpio::Unassigned;
	engineConfiguration->etbIo[1].disablePin = Gpio::Unassigned;
	engineConfiguration->etb_use_two_wires = false;
}}

static void setupVbatt() {{
	engineConfiguration->analogInputDividerCoefficient = {analog["input_divider"]}f;
	engineConfiguration->vbattDividerCoeff = {analog["vbatt_divider"]}f;
	engineConfiguration->vbattAdcChannel = {s["vbatt"]["adc"]};
	engineConfiguration->adcVcc = {analog["adc_vcc"]}f;
}}

static void setStepperConfig() {{
	engineConfiguration->idle.stepperDirectionPin = Gpio::Unassigned;
	engineConfiguration->idle.stepperStepPin = Gpio::Unassigned;
	engineConfiguration->stepperEnablePin = Gpio::Unassigned;
	engineConfiguration->useStepperIdle = false;
}}

static void setupSdCard() {{
	engineConfiguration->sdCardSpiDevice = SPI_DEVICE_{sd["spi"]};
	engineConfiguration->is_enabled_spi_3 = true;
	engineConfiguration->spi3sckPin = {gpio(sd["sck"])};
	engineConfiguration->spi3misoPin = {gpio(sd["miso"])};
	engineConfiguration->spi3mosiPin = {gpio(sd["mosi"])};
}}

static void setupEGT() {{
	engineConfiguration->spi2sckPin = Gpio::Unassigned;
	engineConfiguration->spi2misoPin = Gpio::Unassigned;
	engineConfiguration->spi2mosiPin = Gpio::Unassigned;
	engineConfiguration->is_enabled_spi_2 = false;
	engineConfiguration->max31855spiDevice = SPI_NONE;
	for (int i = 0; i < EGT_CHANNEL_COUNT; i++) {{
		engineConfiguration->max31855_cs[i] = Gpio::Unassigned;
	}}
}}

Gpio getCommsLedPin() {{
	return {gpio(leds["comms"])};
}}

Gpio getRunningLedPin() {{
	return {gpio(leds["running"])};
}}

Gpio getWarningLedPin() {{
	return {gpio(leds["warning"])};
}}

void setBoardConfigOverrides() {{
	setupSdCard();
	setEtbConfig();
	setStepperConfig();
	setupEGT();

	engineConfiguration->clt.config.bias_resistor = {s["clt"]["bias_ohms"]};
	engineConfiguration->iat.config.bias_resistor = {s["iat"]["bias_ohms"]};

	engineConfiguration->canRxPin = {gpio(c["can1"]["rx"])};
	engineConfiguration->canTxPin = {gpio(c["can1"]["tx"])};
	engineConfiguration->can2RxPin = Gpio::Unassigned;
	engineConfiguration->can2TxPin = Gpio::Unassigned;
}}

static void setupDefaultSensorInputs() {{
	engineConfiguration->afr.hwChannel = {s["afr"]["adc"]};
	engineConfiguration->afr.hwChannel2 = EFI_ADC_NONE;
	setEgoSensor({s["afr"]["ego"]});

	engineConfiguration->map.sensor.hwChannel = {s["map"]["adc"]};
	engineConfiguration->map.sensor.type = {s["map"]["type"]};

	engineConfiguration->clt.adcChannel = {s["clt"]["adc"]};
	engineConfiguration->iat.adcChannel = {s["iat"]["adc"]};
	engineConfiguration->tps1_1AdcChannel = {s["tps"]["adc"]};

	engineConfiguration->baroSensor.hwChannel = EFI_ADC_NONE;
	engineConfiguration->lps25BaroSensorScl = {gpio(baro["scl"])};
	engineConfiguration->lps25BaroSensorSda = {gpio(baro["sda"])};
}}

void setBoardDefaultConfiguration() {{
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
	engineConfiguration->sdCardCsPin = {gpio(sd["cs"])};

	strncpy(config->luaScript, R"(
{lua}    )", efi::size(config->luaScript));
}}
"""


def render_rusefi_mk(d: dict) -> str:
    fw = d["firmware"]["rusefi"]
    ram = d["firmware"].get("ram_unused_size")
    ram_line = f"DDEFS += -DRAM_UNUSED_SIZE={ram}\n" if ram else ""
    return (
        f"# GENERATED from config/{d['board']['id']}/board.yaml\n"
        f"BOARDCPPSRC = $(PROJECT_DIR)/config/boards/{fw['overlay_as']}/board_configuration.cpp\n"
        f"BOARDINC = $(PROJECT_DIR)/config/boards/{fw['overlay_as']}\n"
        f"SHORT_BOARD_NAME={fw['short_board_name']}\n"
        f'DDEFS += -DFIRMWARE_ID=\\"{fw["firmware_id"]}\\"\n'
        f"DDEFS += -DDEFAULT_ENGINE_TYPE=engine_type_e::{d['firmware']['default_engine_type']}\n"
        "DDEFS += -DEFI_SOFTWARE_KNOCK=FALSE -DSTM32_ADC_USE_ADC3=TRUE\n"
        f"{ram_line}"
    )


def render_fome_mk(d: dict) -> str:
    fw = d["firmware"]["fome"]
    return (
        f"# GENERATED from config/{d['board']['id']}/board.yaml\n"
        "BOARDCPPSRC = $(BOARD_DIR)/board_configuration.cpp\n"
        f"SHORT_BOARD_NAME = {fw['short_board_name']}\n"
        f'DDEFS += -DFIRMWARE_ID=\\"{fw["firmware_id"]}\\"\n'
        f"DDEFS += -DDEFAULT_ENGINE_TYPE={d['firmware']['default_engine_type']}\n"
        "DDEFS += -DEFI_SOFTWARE_KNOCK=FALSE -DSTM32_ADC_USE_ADC3=TRUE\n"
    )


def render_prepend(d: dict) -> str:
    return """#define ts_show_hip9011 false
#define ts_show_cj125 false
#define ts_show_lcd false
#define ts_show_joystick false
#define ts_show_gps false
#define ts_show_software_knock false
#define show_test_presets true
#define show_microRusEFI_presets false
#define show_Frankenso_presets false
#define show_Hellen_presets false
#define show_Proteus_presets false
"""


def render_env(d: dict) -> str:
    fw = d["firmware"]["rusefi"]
    return f"SHORT_BOARD_NAME={fw['short_board_name']}\nPROJECT_CPU={d['board']['cpu']}\n"


def render_compile_sh(d: dict) -> str:
    fw = d["firmware"]["fome"]
    openblt = "yes" if fw.get("use_openblt") else "no"
    return (
        "#!/bin/bash\n"
        f"export USE_OPENBLT={openblt}\n"
        f"bash ../common_make.sh {fw['overlay_as']} {d['board']['cpu']}\n"
    )


def download_button(label: str, color: str, url: str) -> str:
    slug = label.replace(" ", "%20")
    return (
        "<!-- BEGIN LATEST DOWNLOAD BUTTON -->\n"
        f"[![Download {label}](https://custom-icon-badges.demolab.com/badge/-{slug}-{color}"
        f"?style=for-the-badge&logo=download&logoColor=white \"Download {label}\")]({url})\n"
        "<!-- END LATEST DOWNLOAD BUTTON -->\n"
    )


def _dash(value) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def render_pin_table(d: dict) -> str:
    rows = []
    for p in d["connector"]["pins"]:
        silk = _dash(p.get("silk"))
        mcu = p.get("mcu") or p.get("via") or "-"
        if p.get("alt_mcu"):
            alt_fn = p.get("alt_function") or "alt"
            mcu = f"{mcu} / {p['alt_mcu']} ({alt_fn})"
        elif p.get("via") and p.get("mcu"):
            mcu = f"{mcu} ({p['via']})"
        note = p.get("note") or ""
        if p.get("alt_function") and not p.get("alt_mcu") and p["alt_function"] not in note:
            note = (note + " " if note else "") + p["alt_function"]
        if p.get("via") and not p.get("mcu"):
            via = f"via {p['via']}"
            if via not in note:
                note = (note + " " if note else "") + via
        pull = p.get("pullup_ohms")
        if pull and str(pull) not in note and "pull-up" not in note.lower() and "pull up" not in note.lower():
            note = (note + " " if note else "") + f"{pull} ohm pull-up to +5 V."
        rows.append(
            f"| {p['pin']} | {silk} | {_dash(p.get('net'))} | {mcu} | {_dash(p.get('function'))} | {note or '-'} |"
        )
    header = (
        "| Pin | Back silk | Net | MCU | Function | Notes |\n"
        "| ---: | --- | --- | --- | --- | --- |\n"
    )
    return header + "\n".join(rows)


def render_readme(d: dict) -> str:
    """Board manual in the same section layout as the older config/*/readme.md files."""
    b = d["board"]
    feat = d["features"]
    docs = d.get("docs") or {}
    links = docs.get("release_links") or {}
    images = docs.get("images") or {}
    notes = docs.get("notes") or []
    host_repo = docs.get("host_repo") or "opelpanfan/OPF_ECU"
    host_branch = docs.get("host_branch") or b["id"]
    pages_base = docs.get("pages_base") or f"https://{host_repo.split('/')[0]}.github.io/{host_repo.split('/')[1]}"
    rusefi_tag = links.get("rusefi_tag", f"{b['id']}-rusefi-latest")
    fome_tag = links.get("fome_tag", f"{b['id']}-fome-latest")
    raw = f"https://raw.githubusercontent.com/{host_repo}/{host_branch}"
    rel_base = f"https://github.com/{host_repo}/releases/download"
    style = links.get("style") or "board_branch"

    def asset_url(kind: str, name: str, fallback_tag: str, fallback_asset: str) -> str:
        if style == "board_branch":
            directory = links.get(f"{kind}_branch_dir", kind)
            assets = links.get(f"{kind}_branch_assets") or {}
            filename = assets.get(name, fallback_asset)
            return f"{raw}/{directory}/{filename}"
        return f"{rel_base}/{fallback_tag}/{fallback_asset}"

    feature_lines = [
        f"- {feat['injectors']} Injectors",
        f"- {feat['coils']} Coils",
        f"- {feat['low_side']} Low-side outputs (fuel pump, fan, idle, boost, tacho)",
        f"- {feat['vr_channels']} VR / {feat['hall_inputs']} Hall trigger inputs (shared via jumpers)",
        f"- {feat['analog_5v']} analogue 0-5 V inputs on the connector (IN_A1-IN_A5)",
        f"- {feat['can']} CANbus",
        f"- On-board wideband ({feat['wideband']})",
        f"- On-board MAP ({feat['map']})",
    ]
    if feat.get("barometer"):
        feature_lines.append(f"- On-board barometer ({feat['barometer']})")
    if feat.get("sd_card"):
        feature_lines.append("- On-board SD card")
    if feat.get("bluetooth"):
        feature_lines.append("- Bluetooth")
    if feat.get("usb"):
        feature_lines.append("- USB")
    features = "\n".join(feature_lines)

    fome_btns = "\n".join(
        download_button(label, color, asset_url("fome", key, fome_tag, asset))
        for label, color, key, asset in [
            ("FOME Firmware", "blue", "bin", "fome.bin"),
            ("FOME Update SREC", "blue", "srec", "fome_update.srec"),
            ("FOME TunerStudio INI", "green", "ini", "fome_tunerstudio.ini"),
        ]
    )
    rusefi_btns = "\n".join(
        download_button(label, color, asset_url("rusefi", key, rusefi_tag, asset))
        for label, color, key, asset in [
            ("RusEFI Firmware", "blue", "bin", "rusefi.bin"),
            ("RusEFI HEX", "blue", "hex", "rusefi.hex"),
            ("RusEFI SREC", "blue", "srec", "rusefi.srec"),
            ("RusEFI TunerStudio INI", "green", "ini", "rusefi_tunerstudio.ini"),
        ]
    )

    pin_table = render_pin_table(d)

    notes_md = "\n".join(f"- {n}" for n in notes)

    top = images.get("pcb_top")
    back = images.get("pcb_back")
    hall = images.get("hall_setup")
    vr = images.get("vr_setup")
    pcb = ""
    if top or back:
        pcb += "## PCB Layout\n\n"
        if top:
            pcb += f"## TOP\n![front]({top})\n\n"
        if back:
            pcb += f"## BACK\n![back]({back})\n\n"

    trigger = d["trigger"]
    prim = trigger["primary"]
    trigger_md = (
        "## Trigger configuration\n\n"
        f"Primary trigger default is **{prim.get('mode', 'hall')}** on connector pin "
        f"{prim.get('connector')} ({prim.get('pin')}), wheel type **{trigger['type']}**.\n\n"
        "| Jumper | Connector pins | Hall (2-3) | VR (2-1) |\n"
        "| --- | --- | --- | --- |\n"
        f"| {prim.get('jumper', 'JP4')} | {prim.get('minus_connector', 7)} / "
        f"{prim.get('connector', 8)} | {prim.get('pin')} | {prim.get('vr_pin', '')} |\n"
    )
    if trigger.get("secondary"):
        sec = trigger["secondary"]
        jps = ", ".join(sec.get("jumpers") or [])
        trigger_md += (
            f"\nSecondary trigger (unused in the default tune) is on pins "
            f"{sec.get('connectors')}, jumpers {jps} "
            f"({sec.get('plus_pin')} / {sec.get('minus_pin')}).\n"
        )
    trigger_md += "\nCLT/IAT pull-ups are **permanent** 2.49 k resistors R85/R86 on IN_A1/IN_A2. There is no SW10-SW12 jumper block on this 33-pin board.\n\n"
    if hall:
        trigger_md += f"### HALL Trigger Configuration\n\n![image]({hall})\n\n"
    if vr:
        trigger_md += f"### VR Trigger Configuration\n\n![image]({vr})\n\n"

    return f"""# {b['name']}

{b['name']} {b.get('hardware_revision', '')} - {b.get('mcu', '')} ECU.

Generated from `config/{b['id']}/board.yaml`. Do not hand-edit this file; change the YAML and re-run `tools/boardgen/generate_board.py`.

## Features

{features}

## Firmware

Downloads are public. Badge links point at the `{host_branch}` board branch of `{host_repo}`
(raw files under `rusefi/` and `fome/`). GitHub Releases are also published from `master-grok`.
(Right click and 'Save link as...')

## FOME (RUSEFI fork) Firmware

Stable URL tag: `{fome_tag}`. Flash `fome.bin` for a first DFU install (OpenBLT + FOME). Use `fome_update.srec` for later OpenBLT updates.

{fome_btns}

## RUSEFI Firmware

Stable URL tag: `{rusefi_tag}`.

{rusefi_btns}

## Interactive Pinout Manual

<!-- BEGIN LATEST DOWNLOAD BUTTON -->
[![Download zip](https://custom-icon-badges.demolab.com/badge/-Pinout%20Manual-black?style=for-the-badge&logo=download&logoColor=white "Pinout Manual")]({pages_base}/{b['id']}.html)
<!-- END LATEST DOWNLOAD BUTTON -->

{b['name']} {b.get('hardware_revision', '')} uses a single **{d['connector']['name']}** connector. Pins 23-31 have back-silkscreen labels. The interactive page is [{pages_base}/{b['id']}.html]({pages_base}/{b['id']}.html) (live after this file is on `main`).

{pin_table}

{pcb}{trigger_md}## Notes

{notes_md}
"""


def write(path: Path, text: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text)
    if executable:
        path.chmod(path.stat().st_mode | 0o111)
    print("wrote", path)



def render_pinout_html(d: dict) -> str:
    """Standalone pinout page for docs/<id>.html (GitHub Pages)."""
    b = d["board"]
    docs = d.get("docs") or {}
    notes = docs.get("notes") or []
    images = docs.get("images") or {}
    rows = []
    for p in d["connector"]["pins"]:
        silk = _dash(p.get("silk"))
        mcu = p.get("mcu") or p.get("via") or "-"
        if p.get("alt_mcu"):
            alt_fn = p.get("alt_function") or "alt"
            mcu = f"{mcu} / {p['alt_mcu']} ({alt_fn})"
        note = p.get("note") or ""
        if p.get("via") and not p.get("mcu"):
            via = f"via {p['via']}"
            if via not in note:
                note = (note + " " if note else "") + via
        rows.append(
            "<tr>"
            f"<td>{p['pin']}</td><td>{silk}</td><td>{_dash(p.get('net'))}</td>"
            f"<td>{mcu}</td><td>{_dash(p.get('function'))}</td><td>{note or '-'}</td>"
            "</tr>"
        )
    def img(url, alt):
        if not url:
            return ""
        return f'<p><img src="{url}" alt="{alt}" style="max-width:100%;height:auto"></p>'
    notes_html = "".join(f"<li>{n}</li>" for n in notes)
    title = f"{b['name']} {b.get('hardware_revision','')} pinout"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 1.5rem; line-height: 1.4; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 1100px; }}
  th, td {{ border: 1px solid #333; padding: 6px 8px; text-align: left; }}
  th {{ background: #111; color: #fff; }}
  tr:nth-child(even) {{ background: #eee; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #111; color: #eee; }}
    th {{ background: #000; }}
    th, td {{ border-color: #888; }}
    tr:nth-child(even) {{ background: #1c1c1c; }}
    a {{ color: #71b7ff; }}
  }}
</style>
</head>
<body>
<h1>{title}</h1>
<p>{b['name']} uses a single <strong>{d['connector']['name']}</strong> connector.
Pins 23-31 have back-silkscreen labels. Generated from <code>config/{b['id']}/board.yaml</code>.</p>
<table>
  <thead><tr><th>Pin</th><th>Back silk</th><th>Net</th><th>MCU</th><th>Function</th><th>Notes</th></tr></thead>
  <tbody>
  {''.join(rows)}
  </tbody>
</table>
<h2>PCB</h2>
{img(images.get("pcb_top"), "PCB top")}
{img(images.get("pcb_back"), "PCB back")}
<h2>Trigger</h2>
{img(images.get("hall_setup"), "Hall trigger setup")}
{img(images.get("vr_setup"), "VR trigger setup")}
<h2>Notes</h2>
<ul>{notes_html}</ul>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("yaml_path", type=Path)
    ap.add_argument("--docs-dir", type=Path, default=None,
                    help="If set, also write docs/<board>.html for GitHub Pages")
    args = ap.parse_args()
    yaml_path = args.yaml_path.resolve()
    data = load(yaml_path)
    out_board = yaml_path.parent

    gen = out_board / "generated"
    rusefi = gen / "rusefi"
    fome = gen / "fome"
    board_id = data["board"]["id"]

    write(rusefi / "board_configuration.cpp", render_rusefi_cpp(data))
    write(rusefi / "board.mk", render_rusefi_mk(data))
    write(rusefi / "prepend.txt", render_prepend(data))
    write(rusefi / "board.env", render_env(data))
    write(fome / "board_configuration.cpp", render_fome_cpp(data))
    write(fome / "board.mk", render_fome_mk(data))
    write(fome / "prepend.txt", render_prepend(data))
    write(fome / f"compile_{board_id}.sh", render_compile_sh(data), executable=True)

    readme = render_readme(data)
    write(gen / "README.md", readme)
    write(out_board / "readme.md", readme)
    if args.docs_dir:
        html = render_pinout_html(data)
        write(args.docs_dir / f"{board_id}.html", html)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
