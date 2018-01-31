#
# Neil Trimboy 2011
#

import serial

RW_MASTER_ADDRESS = 0x81

# Protocol for each controller
HMV2_ID = 2
HMV3_ID = 3

BYTEMASK = 0xff

# Constants for Methods
# Passed to hmVerifyMsgCRCOK when message is of type FUNC_WRITE
DONT_CARE_LENGTH = 1

#
# HM Version 3 Magic Numbers
#

# Master must be in range [0x81,0xa0] = [129,160]
MASTER_ADDR_MIN = 0x81
MASTER_ADDR_MAX = 0xa0

# Define magic numbers used in messages
FUNC_READ = 0
FUNC_WRITE = 1

BROADCAST_ADDR = 0xff
RW_LENGTH_ALL = 0xffff

SET_TEMP_ADDR = 18
KEY_LOCK_ADDR = 22
HOL_HOURS_LO_ADDR = 24
HOL_HOURS_HI_ADDR = 25
CUR_TIME_ADDR = 43

KEY_LOCK_UNLOCK = 0
KEY_LOCK_LOCK = 1

HOT_WATER_ADDR = 42

HOT_WATER_ON = 1
HOT_WATER_OFF = 0

# COMM SETTINGS

COM_PORT = 6  # 1 less than com port, USB is 6=com7, ether is 9=10
COM_BAUD = 4800
COM_SIZE = serial.EIGHTBITS
COM_PARITY = serial.PARITY_NONE
COM_STOP = serial.STOPBITS_ONE
COM_TIMEOUT = 3
