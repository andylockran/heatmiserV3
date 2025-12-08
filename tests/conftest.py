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
    # Default payload: zeroed list so tests can set explicit values if needed
    payload = [0] * 64
    # Set some sensible defaults used in tests
    payload[5] = 0   # temperature format -> Celsius
    payload[11] = 99  # thermostat id value
    payload[13] = 2   # sensor selection -> floor sensor
    payload[17] = 42  # frost protect temp
    payload[18] = 210 # set room temp (21.0)
    # use byte-sized values (<256)
    payload[19] = 200 # floor max raw value (e.g. 20.0 represented as 200)
    payload[31] = 235 # floor temp raw (23.5)
    payload[33] = 180 # built in air temp (18.0)
    payload[34] = 0   # sensor error
    payload[35] = 1   # current state
    return FakeUH1(payload=payload)


@pytest.fixture
def thermostat(fake_uh1):
    # Create a real HeatmiserThermostat which will call registerThermostat
    th = heatmiser.HeatmiserThermostat(1, 'prt', fake_uh1)
    return th
