#
# Neil Trimboy 2011
#

import serial

class Constants(object):
    MY_MASTER_ADDR = 0x81

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
    FUNC_READ  = 0
    FUNC_WRITE = 1

    BROADCAST_ADDR = 0xff
    RW_LENGTH_ALL = 0xffff
    DCB_OFFSET_SERIAL = 9
    DCB_OFFSET_TCP = 4

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

    COM_PORT = 6 # 1 less than com port, USB is 6=com7, ether is 9=10
    COM_BAUD = 4800
    COM_SIZE = serial.EIGHTBITS
    COM_PARITY = serial.PARITY_NONE
    COM_STOP = serial.STOPBITS_ONE
    COM_TIMEOUT = 3

    CONNECTION_TYPES = (
        (0, 'SERIAL'),
        (1, 'TCP')
    )

    DEFAULT_TCP_OPTIONS = {
        'host': 'heatmiser',
        'port': 8068,
        'pin': 0000
    }

    DCB_OFFSETS = {
        'serial': {
            'TM1': {
                'program_mode': 6,
                'timebase': 16,
                'onoff': 8,
                'keylock': 9,
                'holiday_hours_high': 10,
                'holiday_hours_low': 11,
                'progbase': 19,
            },
        },
        'WiFi': {
            'DT':{
                'program_mode': 16,
                'away': 24,
                'timebase': 41,
                'onoff': 21,
                'keylock': 22,
                'holiday_start': 25,
                'holiday_end': 30,
                'progbase': 48,
            },
            'PRTHW': {
                'program_mode': 16,
                'away': 24,
                'timebase': 44,
                'onoff': 21,
                'keylock': 22,
                'holiday_start': 25,
                'holiday_end': 30,
                'progbase': 51,
                'hotwater': 43,
                'boostbase': 31
            },
            'TM1': {
                'program_mode': 6,
                'timebase': 19,
                'away': 7,
                'onoff': 8,
                'keylock': 9,
                'holiday_start': 10,
                'holiday_end': 15,
                'progbase': 51,
            },
        }
    }
