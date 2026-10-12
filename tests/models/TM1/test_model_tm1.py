"""Tests for Heatmiser TM1 Thermostat / Timer Model (Protocol 3.9 Section 3.5)."""
import yaml
import importlib_resources
from heatmiserv3 import heatmiser, constants
from tests.conftest import (
    FakeUH1,
    build_tm1_default_dcb_5_2,
)


def _load_config():
    cfg_path = importlib_resources.files("heatmiserv3").joinpath("config.yml")
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def test_tm1_config_keys_structure():
    """Verify TM1 configuration keys exist in config.yml matching Protocol 3.9 section 3.5."""
    cfg = _load_config()
    assert "tm1" in cfg, "tm1 model configuration missing from config.yml"
    assert "TM1" in cfg, "TM1 alias missing from config.yml"

    tm1_cfg = cfg["tm1"]
    assert tm1_cfg.get("offset") == 9
    assert tm1_cfg.get("model_id") == 5

    keys = tm1_cfg.get("keys")
    assert isinstance(keys, dict)

    # Base parameters (indices 0..18)
    expected_base_indices = {
        0: "High 8 bit",
        1: "Low 8 bit",
        2: "Vendor ID",
        3: "Version",
        4: "Model",
        5: "Address",
        6: "Program mode",
        7: "Reserved",
        8: "On/off",
        9: "Key lock",
        10: "Holiday hours high",
        11: "Holiday hours low",
        12: "Countdown min high",
        13: "Countdown min low",
        14: "Current timer state",
        15: "Week 1~7",
        16: "Hour",
        17: "Min",
        18: "Sec",
    }
    for idx, name in expected_base_indices.items():
        assert idx in keys, f"DCB index {idx} missing from TM1 configuration"
        assert name.lower() in keys[idx].lower(), f"Mismatch in DCB index {idx} label: {keys[idx]}"

    # 5/2 mode indices (19..50)
    for idx in range(19, 51):
        assert idx in keys, f"5/2 mode DCB index {idx} missing from TM1 configuration"

    # 7-day mode indices (51..162)
    for idx in range(51, 163):
        assert idx in keys, f"7-day mode DCB index {idx} missing from TM1 configuration"


def test_tm1_model_identification(tm1_thermostat):
    """Verify model ID is 5 (TM1 = 0x05) per protocol specification."""
    assert tm1_thermostat.get_model() == constants.MODEL_TM1
    assert tm1_thermostat.get_model() == 5


def test_tm1_dcb_reading_5_2_mode(tm1_uh1_5_2):
    """Verify TM1 DCB parsing in 5/2 day mode."""
    stat = heatmiser.TM1Thermostat(1, tm1_uh1_5_2)
    assert stat.get_model() == 5
    assert stat.get_program_mode() == "5/2 mode"
    assert stat.get_on_off() == 0
    assert stat.get_key_lock() == 0
    assert stat.get_holiday_hours() == 0
    assert stat.get_countdown_minutes() == 0
    assert stat.get_timer_state() == 0

    time_info = stat.get_time()
    assert time_info["week"] == 1
    assert time_info["hour"] == 12
    assert time_info["min"] == 30
    assert time_info["sec"] == 0


def test_tm1_dcb_reading_7_day_mode(tm1_uh1_7_day):
    """Verify TM1 DCB parsing in 7-day mode."""
    stat = heatmiser.TM1Thermostat(1, tm1_uh1_7_day)
    assert stat.get_model() == 5
    assert stat.get_program_mode() == "7 day mode"
    # Check that day switching periods are mapped
    assert 51 in stat.dcb  # Monday Time1 On Hour
    assert 162 in stat.dcb  # Sunday Time4 Off Min


def test_tm1_dcb_reading_countdown_mode(tm1_uh1_countdown):
    """Verify TM1 DCB parsing in countdown timer mode."""
    stat = heatmiser.TM1Thermostat(1, tm1_uh1_countdown)
    assert stat.get_model() == 5
    assert stat.get_program_mode() == "Countdown timer mode"
    assert 18 in stat.dcb  # Seconds


def test_tm1_holiday_hours_decoding():
    """Verify reading holiday hours decodes big-endian correctly (high byte at index 10, low at 11)."""
    dcb = build_tm1_default_dcb_5_2()
    # 168 hours = 7 days -> 0x00A8 -> high 0, low 168
    dcb[10] = 0
    dcb[11] = 168
    stat = heatmiser.TM1Thermostat(1, FakeUH1(payload=dcb, model="tm1"))
    assert stat.get_holiday_hours() == 168

    # 500 hours -> 0x01F4 -> high 1, low 244
    dcb[10] = 1
    dcb[11] = 244
    stat2 = heatmiser.TM1Thermostat(1, FakeUH1(payload=dcb, model="tm1"))
    assert stat2.get_holiday_hours() == 500


def test_tm1_countdown_minutes_decoding():
    """Verify reading countdown minutes decodes high byte at index 12, low at 13."""
    dcb = build_tm1_default_dcb_5_2()
    # 1800 minutes -> 0x0708 -> high 7, low 8
    dcb[12] = 7
    dcb[13] = 8
    stat = heatmiser.TM1Thermostat(1, FakeUH1(payload=dcb, model="tm1"))
    assert stat.get_countdown_minutes() == 1800


def test_tm1_generic_heatmiser_thermostat_instantiation(tm1_uh1_5_2):
    """Verify generic HeatmiserThermostat class can instantiate with model='tm1'."""
    stat = heatmiser.HeatmiserThermostat(1, "tm1", tm1_uh1_5_2)
    assert stat.dcb[4]["value"] == 5
    assert stat.model == "tm1"
