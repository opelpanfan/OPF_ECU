# List of all the board related files.
BOARDCPPSRC =  $(PROJECT_DIR)/config/boards/core48/board_configuration.cpp

BOARDINC = $(PROJECT_DIR)/config/boards/core48

# Override DEFAULT_ENGINE_TYPE
SHORT_BOARD_NAME=core48
DDEFS += -DFIRMWARE_ID=\"core48\"
DDEFS += -DDEFAULT_ENGINE_TYPE=MINIMAL_PINS
# OPF33 PINFIX: no knock hardware on OPF33
DDEFS += -DEFI_SOFTWARE_KNOCK=FALSE -DSTM32_ADC_USE_ADC3=TRUE  # ADC3 kept: knock_config.h references ADCD3
DDEFS += -DRAM_UNUSED_SIZE=1000
