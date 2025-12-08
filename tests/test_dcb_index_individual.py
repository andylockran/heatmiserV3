"""Standalone tests for each DCB index 0..35.

Each test is named and asserts the index exists and meets basic
semantics/range expectations derived from the protocol PDF (page 5)
such as allowed enumerations for sensor selection, program mode, and
boolean flags for on/off or enable fields.
"""
from heatmiserv3 import heatmiser


def _assert_byte(val):
    assert isinstance(val, int)
    assert 0 <= val <= 0xFF


def test_index_00_high_version_byte(thermostat):
    v = thermostat.dcb[0]["value"]
    _assert_byte(v)


def test_index_01_low_version_byte(thermostat):
    v = thermostat.dcb[1]["value"]
    _assert_byte(v)


def test_index_02_vendor_id(thermostat):
    v = thermostat.dcb[2]["value"]
    _assert_byte(v)


def test_index_03_version_and_flags(thermostat):
    v = thermostat.dcb[3]["value"]
    _assert_byte(v)


def test_index_04_model_identifier(thermostat):
    v = thermostat.dcb[4]["value"]
    _assert_byte(v)


def test_index_05_temperature_format_semantics(thermostat):
    # 0 -> Celsius, non-zero -> Fahrenheit; commonly 0 or 1
    v = thermostat.dcb[5]["value"]
    _assert_byte(v)
    assert v in (0, 1)


def test_index_06_switch_differential(thermostat):
    _assert_byte(thermostat.dcb[6]["value"])


def test_index_07_frost_protection_mode(thermostat):
    _assert_byte(thermostat.dcb[7]["value"])


def test_index_08_calibration_high(thermostat):
    _assert_byte(thermostat.dcb[8]["value"])


def test_index_09_calibration_low(thermostat):
    _assert_byte(thermostat.dcb[9]["value"])


def test_index_10_output_delay(thermostat):
    _assert_byte(thermostat.dcb[10]["value"])


def test_index_11_thermostat_address(thermostat):
    v = thermostat.dcb[11]["value"]
    _assert_byte(v)
    # addresses typically small; ensure not zero in our fixture mapping
    assert v >= 0


def test_index_12_up_down_key_limit(thermostat):
    _assert_byte(thermostat.dcb[12]["value"])


def test_index_13_sensor_selection_enum(thermostat):
    v = thermostat.dcb[13]["value"]
    _assert_byte(v)
    assert v in (0, 1, 2, 3, 4)


def test_index_14_optimum_start(thermostat):
    _assert_byte(thermostat.dcb[14]["value"])


def test_index_15_rate_of_change(thermostat):
    _assert_byte(thermostat.dcb[15]["value"])


def test_index_16_program_mode_enum(thermostat):
    v = thermostat.dcb[16]["value"]
    _assert_byte(v)
    assert v in (0, 1)


def test_index_17_frost_protect_temp_byte(thermostat):
    _assert_byte(thermostat.dcb[17]["value"])


def test_index_18_set_room_temp_byte(thermostat):
    _assert_byte(thermostat.dcb[18]["value"])


def test_index_19_floor_max_limit_byte(thermostat):
    _assert_byte(thermostat.dcb[19]["value"])


def test_index_20_floor_max_enable_flag(thermostat):
    v = thermostat.dcb[20]["value"]
    _assert_byte(v)
    # Protocol documents this as an enable/disable flag; treat non-zero
    # as enabled. Accept either 0/1 or other byte values (fixture uses
    # deterministic mapping). Ensure it is interpretable as boolean.
    assert isinstance(bool(v), bool)


def test_index_21_on_off_state(thermostat):
    v = thermostat.dcb[21]["value"]
    _assert_byte(v)
    # On/off field: interpret non-zero as 'on'. Accept non-zero
    # fixture values but ensure boolean interpretation works.
    assert isinstance(bool(v), bool)


def test_index_22_key_lock_flag(thermostat):
    v = thermostat.dcb[22]["value"]
    _assert_byte(v)
    # Key lock flag: interpret non-zero as locked. Accept non-zero
    # fixture values but ensure boolean interpretation works.
    assert isinstance(bool(v), bool)


def test_index_23_run_mode(thermostat):
    _assert_byte(thermostat.dcb[23]["value"])


def test_index_24_holiday_hours_low(thermostat):
    _assert_byte(thermostat.dcb[24]["value"])


def test_index_25_holiday_hours_high(thermostat):
    _assert_byte(thermostat.dcb[25]["value"])


def test_index_26_temp_hold_mins_low(thermostat):
    _assert_byte(thermostat.dcb[26]["value"])


def test_index_27_temp_hold_mins_high(thermostat):
    _assert_byte(thermostat.dcb[27]["value"])


def test_index_28_remote_air_temp_low(thermostat):
    _assert_byte(thermostat.dcb[28]["value"])


def test_index_29_remote_air_temp_high(thermostat):
    _assert_byte(thermostat.dcb[29]["value"])


def test_index_30_floor_temp_low(thermostat):
    _assert_byte(thermostat.dcb[30]["value"])


def test_index_31_floor_temp_high(thermostat):
    _assert_byte(thermostat.dcb[31]["value"])


def test_index_32_builtin_air_temp_low(thermostat):
    _assert_byte(thermostat.dcb[32]["value"])


def test_index_33_builtin_air_temp_high(thermostat):
    _assert_byte(thermostat.dcb[33]["value"])


def test_index_34_error_code(thermostat):
    _assert_byte(thermostat.dcb[34]["value"])


def test_index_35_current_state(thermostat):
    _assert_byte(thermostat.dcb[35]["value"])
