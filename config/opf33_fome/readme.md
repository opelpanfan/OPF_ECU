# OPF33 (FOME)

FOME board overlay for the OPF33 V1.1 STM32F407 ECU. Pin and sensor
defaults match ECU_Build/config/opf33 (rusEFI).

Do not confuse this with the stock FOME core48 / core8 boards — those
use a different injector, ignition and analog map.

Build from a FOME firmware tree:

    cp -a board-opf33/. firmware/config/boards/opf33/
    cd firmware/config/boards/opf33
    bash ./compile_opf33.sh

Outputs: firmware/deliver/fome.bin (OpenBLT + FOME, for a first DFU
flash) and firmware/deliver/fome_update.srec (later OpenBLT updates),
plus tunerstudio/generated/fome_opf33.ini.
