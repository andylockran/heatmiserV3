import pytest
from tests.conftest import FakeUH1
from heatmiserv3 import heatmiser


@pytest.fixture
def thermostat():
    # PRT-HW model payload: Celsius, floor sensor, 7day
    payload = list(range(64))
    payload[5] = 0
    payload[13] = 2
    payload[16] = 1
    payload[31] = 185
    return heatmiser.HeatmiserThermostat(1, 'prt-hw', FakeUH1(payload=payload))
