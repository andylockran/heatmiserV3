import pytest
from tests.conftest import FakeUH1
from heatmiserv3 import heatmiser


@pytest.fixture
def thermostat():
    # DT model payload: temperature format = Fahrenheit, sensor selection = built-in air, program mode = 5/2
    payload = list(range(64))
    payload[5] = 1
    payload[13] = 0
    payload[16] = 0
    return heatmiser.HeatmiserThermostat(1, 'dt', FakeUH1(payload=payload))
