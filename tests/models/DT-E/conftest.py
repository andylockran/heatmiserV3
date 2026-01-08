import pytest
from tests.conftest import FakeUH1
from heatmiserv3 import heatmiser


@pytest.fixture
def thermostat():
    # DT-E model payload: temperature format = Celsius, sensor selection = remote air, program mode = 7day
    payload = list(range(64))
    payload[5] = 0
    payload[13] = 1
    payload[16] = 1
    return heatmiser.HeatmiserThermostat(1, 'dt-e', FakeUH1(payload=payload))
