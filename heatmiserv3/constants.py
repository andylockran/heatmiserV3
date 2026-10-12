#
# Neil Trimboy 2011
#

import serial

RW_MASTER_ADDRESS = 0x81

# Protocol for each controller
HMV2_ID = 2
HMV3_ID = 3

BYTEMASK = 0xFF

# Constants for Methods
# Passed to hmVerifyMsgCRCOK when message is of type FUNC_WRITE
DONT_CARE_LENGTH = 1

#
# HM Version 3 Magic Numbers
#

# Master must be in range [0x81,0xa0] = [129,160]
MASTER_ADDR_MIN = 0x81
MASTER_ADDR_MAX = 0xA0

# Define magic numbers used in messages
FUNC_READ = 0
FUNC_WRITE = 1

BROADCAST_ADDR = 0xFF
RW_LENGTH_ALL = 0xFFFF

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

#
# TM1 Specific Constants (Protocol 3.9 Section 3.5)
#
MODEL_TM1 = 5

TM1_PROG_MODE_ADDR = 16
TM1_ON_OFF_ADDR = 21
TM1_KEY_LOCK_ADDR = 22
TM1_HOLIDAY_ADDR = 24
TM1_COUNTDOWN_ADDR = 26
TM1_TIMER_STATE_ADDR = 42
TM1_TIME_ADDR = 43

# TM1 5/2 Day Schedule Addresses
TM1_WEEKDAY_ADDR = 71
TM1_WEEKEND_ADDR = 87

# TM1 7-Day Schedule Addresses
TM1_MON_ADDR = 187
TM1_TUE_ADDR = 203
TM1_WED_ADDR = 219
TM1_THU_ADDR = 235
TM1_FRI_ADDR = 251
TM1_SAT_ADDR = 267
TM1_SUN_ADDR = 283

# TM1 Program Modes
TM1_MODE_5_2 = 0
TM1_MODE_7_DAY = 1
TM1_MODE_COUNTDOWN = 2

# TM1 Timer Override States (address 42)
TM1_TIMER_AUTO = 0          # let timer run based on programmed timer period
TM1_TIMER_OVERRIDE_ON = 1   # override timer to on
TM1_TIMER_OVERRIDE_OFF = 2  # override timer to off

# TM1 On/Off states (address 21)
TM1_STATE_OFF = 0
TM1_STATE_ON = 1

# TM1 Key Lock states (address 22)
TM1_KEY_UNLOCK = 0
TM1_KEY_LOCK = 1


# COMM SETTINGS

COM_PORT = 6  # 1 less than com port, USB is 6=com7, ether is 9=10
COM_BAUD = 4800
COM_SIZE = serial.EIGHTBITS
COM_PARITY = serial.PARITY_NONE
COM_STOP = serial.STOPBITS_ONE
COM_TIMEOUT = 3
