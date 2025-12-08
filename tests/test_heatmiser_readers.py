"""Tests that exercise read-only DCB parsing using fixtures."""

def test_read_dcb_populates_dcb(thermostat):
    # After init, thermostat.dcb should be populated
    assert thermostat.dcb


def test_getters_return_expected_values(thermostat):
    # Values set in the fixture payload
    assert thermostat.get_frost_temp() == 42
    assert thermostat.get_target_temp() == 210
    assert thermostat.get_floormax_temp() == 200
    assert thermostat.get_sensor_error() == 0
    assert thermostat.get_current_state() == 1


def test_temperature_format_and_sensor_selection(thermostat):
    assert thermostat.get_temperature_format() == 'C'
    assert thermostat.get_sensor_selection() == 'Floor sensor'


def test_floor_temp_calculation(thermostat):
    # With sensor selection 2 (floor sensor), floor temp should use dcb[31]
    assert abs(thermostat.get_floor_temp() - 23.5) < 0.01
