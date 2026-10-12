"""Fixtures for TM1 model tests."""
import pytest
from tests.conftest import (
    FakeUH1,
    build_tm1_default_dcb_5_2,
    build_tm1_default_dcb_7_day,
    build_tm1_default_dcb_countdown,
)
from heatmiserv3 import heatmiser


@pytest.fixture
def tm1_uh1_5_2():
    return FakeUH1(payload=build_tm1_default_dcb_5_2(), model="tm1")


@pytest.fixture
def tm1_uh1_7_day():
    return FakeUH1(payload=build_tm1_default_dcb_7_day(), model="tm1")


@pytest.fixture
def tm1_uh1_countdown():
    return FakeUH1(payload=build_tm1_default_dcb_countdown(), model="tm1")


@pytest.fixture
def tm1_thermostat(tm1_uh1_5_2):
    return heatmiser.TM1Thermostat(1, tm1_uh1_5_2)


@pytest.fixture
def tm1_thermostat_generic(tm1_uh1_5_2):
    return heatmiser.HeatmiserThermostat(1, "tm1", tm1_uh1_5_2)
