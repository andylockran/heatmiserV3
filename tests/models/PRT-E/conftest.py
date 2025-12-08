import pytest
from tests.conftest import FakeUH1
from heatmiserv3 import heatmiser


@pytest.fixture
def thermostat():
    # PRT-E model payload: Celsius, remote+floor sensor, 7day
    payload = list(range(64))
    payload[5] = 0
    payload[13] = 4
    payload[16] = 1
    # Set a realistic floor temp in high/low (store as single byte for library)
    payload[31] = 235
    return heatmiser.HeatmiserThermostat(1, 'prt-e', FakeUH1(payload=payload))
