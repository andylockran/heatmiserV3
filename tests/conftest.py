"""Pytest fixtures and test doubles for Heatmiser tests."""
import pytest
from heatmiserv3 import heatmiser, constants


def build_tm1_default_dcb_5_2():
    """Build default 51-byte TM1 DCB for 5/2 mode per protocol 3.9 section 3.5."""
    dcb = [0] * 51
    dcb[0] = 0        # DCB length high
    dcb[1] = 51       # DCB length low
    dcb[2] = 0        # Vendor ID (0=Heatmiser)
    dcb[3] = 10       # Version 10 = VER 1.0
    dcb[4] = 5        # Model (TM1 = 5)
    dcb[5] = 1        # Address
    dcb[6] = 0        # Program mode: 00 = 5/2 mode
    dcb[7] = 0        # Reserved
    dcb[8] = 0        # On/off (0=off)
    dcb[9] = 0        # Key lock (0=unlock)
    dcb[10] = 0       # Holiday hours high
    dcb[11] = 0       # Holiday hours low
    dcb[12] = 0       # Countdown min high
    dcb[13] = 0       # Countdown min low
    dcb[14] = 0       # Current timer state (0=auto)
    dcb[15] = 1       # Week 1~7 (1=Mon)
    dcb[16] = 12      # Hour
    dcb[17] = 30      # Min
    dcb[18] = 0       # Sec
    # Weekday Time 1-4 (indices 19..34)
    dcb[19] = 7       # Time1 On Hour
    dcb[20] = 0       # Time1 On Min
    dcb[21] = 9       # Time1 Off Hour
    dcb[22] = 0       # Time1 Off Min
    dcb[23] = 16      # Time2 On Hour
    dcb[24] = 0       # Time2 On Min
    dcb[25] = 20      # Time2 Off Hour
    dcb[26] = 0       # Time2 Off Min
    dcb[27] = 24      # Time3 On Hour (24=cancelled)
    dcb[28] = 0       # Time3 On Min
    dcb[29] = 24      # Time3 Off Hour (24=cancelled)
    dcb[30] = 0       # Time3 Off Min
    dcb[31] = 24      # Time4 On Hour (24=cancelled)
    dcb[32] = 0       # Time4 On Min
    dcb[33] = 24      # Time4 Off Hour (24=cancelled)
    dcb[34] = 0       # Time4 Off Min
    # Weekend Time 1-4 (indices 35..50)
    dcb[35] = 7       # Time1 On Hour
    dcb[36] = 0       # Time1 On Min
    dcb[37] = 9       # Time1 Off Hour
    dcb[38] = 0       # Time1 Off Min
    dcb[39] = 16      # Time2 On Hour
    dcb[40] = 0       # Time2 On Min
    dcb[41] = 20      # Time2 Off Hour
    dcb[42] = 0       # Time2 Off Min
    dcb[43] = 24      # Time3 On Hour (24=cancelled)
    dcb[44] = 0       # Time3 On Min
    dcb[45] = 24      # Time3 Off Hour (24=cancelled)
    dcb[46] = 0       # Time3 Off Min
    dcb[47] = 24      # Time4 On Hour (24=cancelled)
    dcb[48] = 0       # Time4 On Min
    dcb[49] = 24      # Time4 Off Hour (24=cancelled)
    dcb[50] = 0       # Time4 Off Min
    return dcb


def build_tm1_default_dcb_7_day():
    """Build default 163-byte TM1 DCB for 7-day mode per protocol 3.9 section 3.5."""
    dcb = build_tm1_default_dcb_5_2()[:19]
    dcb[0] = 0
    dcb[1] = 163
    dcb[6] = 1  # 7-day mode
    # Append 7 days of 16-byte schedules (indices 51..162)
    default_day = [
        7, 0, 9, 0,     # Time1 On/Off
        16, 0, 20, 0,   # Time2 On/Off
        24, 0, 24, 0,   # Time3 cancelled
        24, 0, 24, 0,   # Time4 cancelled
    ]
    # In TM1 table, indices 19..50 are 5/2 mode.
    # When in 7-day mode, indices 19..50 can be present or 0-padded up to index 50
    dcb += [0] * (51 - 19)
    # Days Mon through Sun: 7 * 16 = 112 bytes
    for _ in range(7):
        dcb.extend(default_day)
    return dcb


def build_tm1_default_dcb_countdown():
    """Build default 19-byte TM1 DCB for countdown timer mode per section 3.5."""
    dcb = build_tm1_default_dcb_5_2()[:19]
    dcb[0] = 0
    dcb[1] = 19
    dcb[6] = 2  # countdown mode
    return dcb


class FakeSerial:
    """Mock serial port that simulates RS485 communication with Heatmiser thermostat."""

    def __init__(self, source_addr=1, payload=None, model="tm1"):
        self.source_addr = source_addr
        self.model = model
        if payload is None:
            if model == "tm1":
                self.payload = build_tm1_default_dcb_5_2()
            else:
                self.payload = list(range(64))
        else:
            self.payload = list(payload)
        self.writes = []
        self.last_write = None

    def write(self, data):
        data_list = list(data)
        self.last_write = data_list
        self.writes.append(data_list)

    def read(self, n=159):
        if not self.last_write:
            return b""

        # Check function code of the last sent message
        # Format: [dest, len, src, func, start_l, start_h, len_l, len_h, ...]
        func_code = self.last_write[3]

        if func_code == constants.FUNC_WRITE:
            # Slave replies to write with 7-byte acknowledgment frame
            # [dest (0x81), frame_len_l (7), frame_len_h (0), src_addr, func (1), crc_l, crc_h]
            reply = [0x81, 7, 0, self.source_addr, constants.FUNC_WRITE]
            crc = heatmiser.CRC16()
            checksum = crc.run(reply)
            return bytes(reply + checksum)

        else:
            # Read command reply:
            # Header: 9 bytes
            # [dest (0x81), len_l, len_h, src_addr, func (0), start_l, start_h, read_len_l, read_len_h]
            start_l = self.last_write[4]
            start_h = self.last_write[5]
            start = (start_h << 8) | start_l

            req_len_l = self.last_write[6]
            req_len_h = self.last_write[7]
            req_len = (req_len_h << 8) | req_len_l

            if req_len == constants.RW_LENGTH_ALL:
                # Return entire payload
                payload_to_return = self.payload[start:]
            else:
                payload_to_return = self.payload[start:start + req_len]

            payload_len = len(payload_to_return)
            frame_len = 11 + payload_len  # 9 header + payload + 2 CRC
            frame_len_l = frame_len & constants.BYTEMASK
            frame_len_h = (frame_len >> 8) & constants.BYTEMASK

            header = [
                0x81,
                frame_len_l,
                frame_len_h,
                self.source_addr,
                constants.FUNC_READ,
                start_l,
                start_h,
                payload_len & constants.BYTEMASK,
                (payload_len >> 8) & constants.BYTEMASK,
            ]
            rxmsg = header + payload_to_return
            crc = heatmiser.CRC16()
            checksum = crc.run(rxmsg)
            return bytes(rxmsg + checksum)


class FakeUH1:
    """Mock HeatmiserUH1 interface."""

    def __init__(self, payload=None, model="tm1"):
        self.thermostats = {}
        self.payload = payload
        self.model = model
        self.serial = None

    def registerThermostat(self, thermostat):
        if thermostat.address in self.thermostats:
            raise ValueError("Key already present")
        self.thermostats[thermostat.address] = thermostat
        self.serial = FakeSerial(thermostat.address, payload=self.payload, model=self.model)
        return self.serial


@pytest.fixture
def fake_uh1_tm1_5_2():
    return FakeUH1(payload=build_tm1_default_dcb_5_2(), model="tm1")


@pytest.fixture
def tm1_uh1_5_2(fake_uh1_tm1_5_2):
    return fake_uh1_tm1_5_2


@pytest.fixture
def fake_uh1_tm1_7_day():
    return FakeUH1(payload=build_tm1_default_dcb_7_day(), model="tm1")


@pytest.fixture
def tm1_uh1_7_day(fake_uh1_tm1_7_day):
    return fake_uh1_tm1_7_day


@pytest.fixture
def fake_uh1_tm1_countdown():
    return FakeUH1(payload=build_tm1_default_dcb_countdown(), model="tm1")


@pytest.fixture
def tm1_uh1_countdown(fake_uh1_tm1_countdown):
    return fake_uh1_tm1_countdown


@pytest.fixture
def tm1_thermostat(fake_uh1_tm1_5_2):
    return heatmiser.TM1Thermostat(1, fake_uh1_tm1_5_2)
