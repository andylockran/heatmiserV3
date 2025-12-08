"""Named semantic tests for selected DCB indexes following PDF semantics.

These tests create small FakeUH1 payloads (via the test helper
`FakeUH1` in `tests/conftest.py`) and instantiate a
`HeatmiserThermostat` to verify library interpretation/semantics.
"""
from tests.conftest import FakeUH1
from heatmiserv3 import heatmiser


def make_thermostat_with_payload(payload):
    uh = FakeUH1(payload=payload)
    return heatmiser.HeatmiserThermostat(1, 'prt', uh)


def test_temperature_format_mapping():
    # 0 -> Celsius, non-zero -> Fahrenheit (library maps 0 to 'C')
    payload = list(range(64))
    payload[5] = 0
    th = make_thermostat_with_payload(payload)
    assert th.get_temperature_format() == 'C'

    payload[5] = 1
    th2 = make_thermostat_with_payload(payload)
    assert th2.get_temperature_format() == 'F'


def test_sensor_selection_mapping_values():
    # Valid sensor selection values 0..4 map to human-readable strings
    mapping = {
        0: 'Built in air sensor',
        1: 'Remote air sensor',
        2: 'Floor sensor',
        3: 'Built in + floor',
        4: 'Remote + floor',
    }
    for val, text in mapping.items():
        payload = list(range(64))
        payload[13] = val
        th = make_thermostat_with_payload(payload)
        assert th.get_sensor_selection() == text


def test_program_mode_mapping():
    payload = list(range(64))
    payload[16] = 0
    th = make_thermostat_with_payload(payload)
    assert th.get_program_mode() == '5/2 mode'

    payload[16] = 1
    th2 = make_thermostat_with_payload(payload)
    assert th2.get_program_mode() == '7 day mode'


def test_floor_temp_source_logic():
    # When sensor selection > 1 use dcb[31], otherwise use dcb[33]
    payload = list(range(64))
    # Case: floor sensor selected -> use index 31
    payload[13] = 2
    payload[31] = 235
    payload[33] = 100
    th = make_thermostat_with_payload(payload)
    assert abs(th.get_floor_temp() - (235 / 10)) < 1e-6

    # Case: remote air sensor selected -> use index 33
    payload2 = list(range(64))
    payload2[13] = 1
    payload2[31] = 235
    payload2[33] = 180
    th2 = make_thermostat_with_payload(payload2)
    assert abs(th2.get_floor_temp() - (180 / 10)) < 1e-6


def test_thermostat_id_and_address_semantics():
    # dcb[11] holds thermostat address/id; assert it's a byte value
    payload = list(range(64))
    payload[11] = 5
    th = make_thermostat_with_payload(payload)
    tid = th.get_thermostat_id()
    assert isinstance(tid, int)
    assert 0 <= tid <= 0xFF


def test_invalid_sensor_selection_raises_keyerror():
    # If an out-of-spec sensor selection is present library will KeyError
    payload = list(range(64))
    payload[13] = 99
    th = make_thermostat_with_payload(payload)
    try:
        _ = th.get_sensor_selection()
        raised = False
    except KeyError:
        raised = True
    assert raised, "Expected KeyError for invalid sensor selection"
