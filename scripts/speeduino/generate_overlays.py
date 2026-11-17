#!/usr/bin/env python3
"""Generate scripts/speeduino/board-overlay/<board>/board.json from config/.

Pin precedence:
  1. config/<board>/board.yaml (OPF33 V1.1)
  2. pins already assigned in board_configuration.cpp (what rusEFI/FOME use)
  3. labelled functions in connectors/*.yaml and the board manual
  4. for Core8 variants that only ship a generic main.yaml, the core8_24c
     manual/black connector aux+sensor map (same STM32F407 family pinout)

Existing handwritten overlays for opf33 and core48_21 are left untouched
(they already built and, for core48_21, were published).
"""
from __future__ import annotations

import json, re, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required")

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
OUT = Path(__file__).resolve().parent / "board-overlay"
# Keep proven, already-validated overlays.
KEEP = {"opf33", "core48_21"}

ADC = {0:"PA0",1:"PA1",2:"PA2",3:"PA3",4:"PA4",5:"PA5",6:"PA6",7:"PA7",
       8:"PB0",9:"PB1",10:"PC0",11:"PC1",12:"PC2",13:"PC3",14:"PC4",15:"PC5"}
GPIO_LTR = "ABCDEFGHI"

def gpio_to_pin(s: str | None) -> str | None:
    if not s: return None
    s = s.strip()
    if "Unassigned" in s or s in ("EFI_ADC_NONE", "ADC_NONE"): return None
    m = re.search(r"Gpio::([A-I])(\d{1,2})", s)
    if m: return f"P{m.group(1)}{int(m.group(2))}"
    m = re.fullmatch(r"EFI_ADC_(\d+)", s)
    if m: return ADC.get(int(m.group(1)))
    m = re.fullmatch(r"([A-I])(\d{1,2})", s)
    if m: return f"P{m.group(1)}{int(m.group(2))}"
    m = re.fullmatch(r"P[A-I]\d{1,2}", s)
    if m: return s
    return None

def first_id(val) -> str | None:
    if isinstance(val, list) and val:
        return str(val[0])
    if val is None: return None
    return str(val)

def load_yaml(p: Path):
    return yaml.safe_load(p.read_text()) or {}

def parse_cpp(text: str) -> dict:
    out = {}
    for m in re.finditer(r"injectionPins\[(\d+)\]\s*=\s*(Gpio::\w+)", text):
        pin = gpio_to_pin(m.group(2))
        if pin: out[f"pinInjector{int(m.group(1))+1}"] = pin
    for m in re.finditer(r"ignitionPins\[(\d+)\]\s*=\s*(Gpio::\w+)", text):
        pin = gpio_to_pin(m.group(2))
        if pin: out[f"pinCoil{int(m.group(1))+1}"] = pin
    mapping = {
        "fuelPumpPin": "pinFuelPump",
        "fanPin": "pinFan",
        "tachoOutputPin": "pinTachOut",
        "boostControlPin": "pinBoost",
        "idle.solenoidPin": "pinIdle1",
        "triggerInputPins[0]": "pinTrigger",
        "triggerInputPins[1]": "pinTrigger2",
        "vbattAdcChannel": "pinBat",
        "clt.adcChannel": "pinCLT",
        "iat.adcChannel": "pinIAT",
        "tpsAdcChannel": "pinTPS",
        "tps.hwChannel": "pinTPS",
        "afr.hwChannel": "pinO2",
        "map.sensor.hwChannel": "pinMAP",
        "can2RxPin": "_can2rx",
        "can2TxPin": "_can2tx",
        "lps25BaroSensorScl": "_baro_scl",
        "lps25BaroSensorSda": "_baro_sda",
    }
    for src, dst in mapping.items():
        m = re.search(r"engineConfiguration->%s\s*=\s*([^;]+);" % re.escape(src), text)
        if not m: continue
        pin = gpio_to_pin(m.group(1))
        if pin: out[dst] = pin
    return out

LABELS = [
    (r"INJECTOR\s*(\d+)", lambda m: f"pinInjector{int(m.group(1))}"),
    (r"IGNITION\s*(\d+)|COIL\s*(\d+)", lambda m: f"pinCoil{int(m.group(1) or m.group(2))}"),
    (r"FUEL\s*PUMP|\bPUMP\b", lambda m: "pinFuelPump"),
    (r"FAN(\s*RELAY)?\b", lambda m: "pinFan"),
    (r"\bIDLE\b", lambda m: "pinIdle1"),
    (r"\bBOOST\b", lambda m: "pinBoost"),
    (r"TACH", lambda m: "pinTachOut"),
    (r"\bVVTI?\b", lambda m: "pinVVT_1"),
    (r"\bCLT\b", lambda m: "pinCLT"),
    (r"\bIAT\b", lambda m: "pinIAT"),
    (r"\bTPS\b", lambda m: "pinTPS"),
    (r"OIL PRESSURE", lambda m: "pinOilPressure"),
    (r"FUEL PRESSURE", lambda m: "pinFuelPressure"),
    (r"SPARE TEMP|SPARE ANALOG", lambda m: "pinSpareTemp1"),
    (r"PRIMARY ON-BOARD O2|ON-BOARD AFR|\bO2 SENSOR\b", lambda m: "pinO2"),
    (r"SECONDARY ON-BOARD O2", lambda m: "pinO2_2"),
    (r"ON-BOARD MAP|\bMAP SENSOR\b", lambda m: "pinMAP"),
    (r"ON-BOARD BATTERY|\bBATTERY SENSE\b", lambda m: "pinBat"),
    (r"VR1\+|HALL 1|HALL1|VR/HALL 1", lambda m: "pinTrigger"),
    (r"VR2\+|HALL 2|HALL2|VR/HALL 2", lambda m: "pinTrigger2"),
]

# Do not treat generic "On-board BARO (B0)" as pinCLT etc.

CORE8_24C_MANUAL_AUX = {
    # From config/core8_24c/readme.md (agrees with black.yaml + cpp inj/ign)
    "pinFuelPump": "PG3",
    "pinFan": "PG4",
    "pinBoost": "PG5",
    "pinIdle1": "PG6",
    "pinVVT_1": "PG7",
    "pinTachOut": "PD14",
    "pinTrigger": "PE2",
    "pinTrigger2": "PE3",
    "pinCLT": "PB0",
    "pinIAT": "PA7",
    "pinTPS": "PC5",
    "pinOilPressure": "PC4",
    "pinFuelPressure": "PA5",
}

CORE8_FAMILY = {
    "core8_21", "core8_23", "core8_24ab", "core8_24c",
    "core8_24d",
}

UNUSED = [
    "pinTrigger2", "pinTrigger3", "pinEMAP", "pinMAP2", "pinO2_2", "pinDisplayReset",
    "pinIdle2", "pinIdleUp", "pinIdleUpOutput", "pinCTPS", "pinFuel2Input", "pinSpark2Input",
    "pinSpareTemp1", "pinSpareTemp2", "pinOilPressure", "pinFuelPressure",
    "pinSpareOut1", "pinSpareOut2", "pinSpareOut3", "pinSpareOut4", "pinSpareOut5", "pinSpareOut6",
    "pinSpareHOut1", "pinSpareHOut2", "pinSpareLOut1", "pinSpareLOut2", "pinSpareLOut3",
    "pinSpareLOut4", "pinSpareLOut5", "pinVVT_1", "pinVVT_2",
    "pinStepperDir", "pinStepperStep", "pinStepperEnable", "pinLaunch", "pinIgnBypass",
    "pinFlex", "pinVSS", "pinBaro", "pinResetControl", "pinWMIEmpty", "pinWMIIndicator",
    "pinWMIEnabled", "pinMC33810_1_CS", "pinMC33810_2_CS",
]

def connector_pins(board: Path) -> dict:
    out = {}
    cdir = board / "connectors"
    if not cdir.is_dir():
        return out
    # black/grey first (labelled typical functions), then main
    files = []
    for name in ("black.yaml", "grey.yaml", "main.yaml"):
        p = cdir / name
        if p.exists(): files.append(p)
    for p in sorted(cdir.glob("*.yaml")):
        if p not in files: files.append(p)
    for yf in files:
        data = load_yaml(yf)
        for ent in data.get("pins") or []:
            pin = gpio_to_pin(ent.get("pin_name")) or gpio_to_pin(first_id(ent.get("id")))
            if not pin: continue
            blob = " ".join(str(ent.get(k) or "") for k in ("function", "ts_name", "type"))
            # Skip generic Analog Inputs N without a typical function
            for pat, fn in LABELS:
                m = re.search(pat, blob, re.I)
                if m:
                    key = fn(m)
                    out.setdefault(key, pin)
                    break
    return out

def leds_and_buses(board: Path) -> dict:
    defines = {}
    cdir = board / "connectors"
    if not cdir.is_dir():
        return defines
    for yf in cdir.glob("*.yaml"):
        for ent in (load_yaml(yf).get("pins") or []):
            ts = str(ent.get("ts_name") or "")
            pin = gpio_to_pin(ent.get("pin_name")) or gpio_to_pin(first_id(ent.get("id")))
            if not pin: continue
            if re.search(r"Running LED", ts, re.I): defines["OPF_LED_RUNNING"] = pin
            elif re.search(r"Warning LED", ts, re.I): defines["OPF_LED_WARNING"] = pin
            elif re.search(r"Error LED|Alert LED", ts, re.I): defines["OPF_LED_ALERT"] = pin
            elif re.search(r"Communication LED", ts, re.I): defines["OPF_LED_COMS"] = pin
            elif re.search(r"BARO SCL", ts, re.I): defines["OPF_BARO_SCL"] = pin
            elif re.search(r"BARO SDA", ts, re.I): defines["OPF_BARO_SDA"] = pin
    return defines

def build(board_name: str) -> dict:
    bdir = CONFIG / board_name
    pins = {}
    notes = [f"Ported from config/{board_name}/ (board_configuration.cpp + connectors) so rusEFI, FOME and Speeduino share one pin map."]
    cpp = bdir / "board_configuration.cpp"
    cpp_pins = parse_cpp(cpp.read_text()) if cpp.exists() else {}
    conn = connector_pins(bdir)
    # cpp first (matches rusEFI/FOME firmware defaults)
    pins.update({k: v for k, v in cpp_pins.items() if not k.startswith("_")})
    # fill gaps from connectors
    for k, v in conn.items():
        if k not in pins:
            pins[k] = v
        elif pins[k] != v and k.startswith(("pinInjector", "pinCoil")):
            notes.append(f"connectors labelled {k}={v} but board_configuration.cpp uses {pins[k]}; Speeduino follows the cpp so all three firmwares agree.")
    # Core8 family: fill remaining aux/sensors from the 24c manual
    if board_name in CORE8_FAMILY:
        for k, v in CORE8_24C_MANUAL_AUX.items():
            pins.setdefault(k, v)
        if board_name != "core8_24c":
            notes.append("Aux/sensor pins not set in this variant's cpp were filled from the core8_24c manual (same Core8 family pinout).")
    # MAP/O2/battery often only in main.yaml as On-board *
    # already handled by LABELS
    extras = {k: v for k, v in cpp_pins.items() if k.startswith("_")}
    defines = leds_and_buses(bdir)
    if extras.get("_baro_scl") or defines.get("OPF_BARO_SCL"):
        defines.setdefault("OPF_I2C_BARO", "1")
        defines.setdefault("OPF_BARO_LPS25HB", "1")
        if extras.get("_baro_scl"): defines["OPF_BARO_SCL"] = extras["_baro_scl"]
        if extras.get("_baro_sda"): defines["OPF_BARO_SDA"] = extras["_baro_sda"]
    if extras.get("_can2rx") and extras.get("_can2tx"):
        defines["OPF_CAN2"] = "1"
    # default LEDs if missing
    defines.setdefault("OPF_LED_RUNNING", "PG10")
    defines.setdefault("OPF_LED_WARNING", "PG11")
    defines.setdefault("OPF_LED_COMS", "PG13")
    inj = [k for k in pins if k.startswith("pinInjector")]
    ign = [k for k in pins if k.startswith("pinCoil")]
    # required keys
    required = ["pinTrigger", "pinInjector1", "pinCoil1", "pinBat", "pinCLT", "pinIAT", "pinTPS", "pinMAP", "pinO2"]
    missing = [k for k in required if k not in pins]
    if missing:
        raise SystemExit(f"{board_name}: incomplete Speeduino pin map, missing {missing}")
    used = set(pins)
    unused = [v for v in UNUSED if v not in used]
    layout = board_name.upper().replace("-", "_")
    if len(layout) > 16:  # keep ini-friendly
        layout = layout[:16]
    return {
        "_comment": " ".join(notes),
        "name": board_name,
        "description": f"OPF {board_name} (STM32F407)",
        "board_id": 59,
        "ts_layout_name": layout,
        "pio_base_env": "black_F407VE",
        "pio_board": "black_f407zg",
        "mcu_guard": "STM32F407xx",
        "firmware_branch": board_name,
        "firmware_dir": "speeduino",
        "firmware_readme": "readme.md",
        "fuel_outputs": len(inj),
        "ign_outputs": len(ign),
        "has_rtc": 0,
        "unused_pin": "PB2",
        "pins": {k: pins[k] for k in sorted(pins, key=lambda s: (re.sub(r'\d+', lambda m: f'{int(m.group()):03}', s)))},
        "unused_pin_vars": unused,
        "defines": defines,
        "base_tune": {
            "seed": "../../base-tune/seed-base-tune-speeduino-202207.msq",
            "overrides": {"pinLayout": f'"{layout}"'},
        },
        "pin_notes": notes,
    }

def main():
    # import list_boards
    sys.path.insert(0, str(ROOT / "scripts" / "ci"))
    from list_boards import list_boards
    boards, _ = list_boards()
    written = []
    for name in boards:
        dest = OUT / name / "board.json"
        if name in KEEP and dest.exists():
            print(f"KEEP  {dest}")
            continue
        data = build(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2) + "\n")
        print(f"WRITE {dest}  fuel={data['fuel_outputs']} ign={data['ign_outputs']} pins={len(data['pins'])}")
        written.append(name)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
