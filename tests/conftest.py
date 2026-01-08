"""Pytest fixtures for heatmiserv3 tests."""
import pytest

from heatmiserv3 import heatmiser, constants


class FakeSerial:
    def __init__(self, source_addr, payload=None):
        self.source_addr = source_addr
        # payload should be a list of 64 ints representing keys 0..63
        if payload is None:
            self.payload = [i for i in range(64)]
        else:
            self.payload = list(payload)

    def write(self, data):
        # record last write if needed
        self.last_write = data

    def read(self, n):
        # Construct a read response with 9-byte header, 64-byte payload and 2-byte CRC (total 75)
        frame_len = 75
        frame_len_l = frame_len & constants.BYTEMASK
        frame_len_h = (frame_len >> 8) & constants.BYTEMASK
        func_code = constants.FUNC_READ

        header = [0x81, frame_len_l, frame_len_h, self.source_addr, func_code, 0, 0, 0, 0]
        # ensure payload is length 64
        payload = self.payload[:64]
        rxmsg = header + payload
        crc = heatmiser.CRC16()
        checksum = crc.run(rxmsg)
        datal = rxmsg + checksum
        return bytes(datal)


class FakeUH1:
    def __init__(self, payload=None):
        self.thermostats = {}
        self.payload = payload

    def registerThermostat(self, thermostat):
        # simple registration and return a FakeSerial bound to thermostat address
        if thermostat.address in self.thermostats:
            raise ValueError("Key already present")
        self.thermostats[thermostat.address] = thermostat
        return FakeSerial(thermostat.address, payload=self.payload)


@pytest.fixture
def fake_uh1():
    # Default payload: use deterministic values 0..63
    payload = list(range(64))
    # Override indexes that must fall into expected ranges for getters
    payload[5] = 0    # temperature format -> Celsius (0)
    payload[13] = 2   # sensor selection -> floor sensor (2)
    payload[16] = 1   # program mode -> 7 day mode (1)
    return FakeUH1(payload=payload)


@pytest.fixture
def thermostat(fake_uh1):
    # Create a real HeatmiserThermostat which will call registerThermostat
    th = heatmiser.HeatmiserThermostat(1, 'prt', fake_uh1)
    return th
