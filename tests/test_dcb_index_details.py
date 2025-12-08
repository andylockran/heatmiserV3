"""Per-index tests for DCB entries 0..35 with embedded PDF comments.

Each test asserts the presence of the DCB index, that the label used by
the library (`config.yml`) matches what we expect, and that the value
matches the deterministic fixture payload. Tests include the PDF's
comment/meaning for each index as context in assertion messages.
"""
import pytest

# PDF comment strings (page 5) mapped to index 0..35. These are the
# human-readable descriptions shown in the PDF 'Comments' column for
# each DCB index. We embed them in the tests so failures show the exact
# protocol description.
PDF_COMMENTS = {
    0: "High 8 bit of device/version",
    1: "Low 8 bit of device/version",
    2: "Vendor ID",
    3: "0-6 bits = Version, bit 7 = floor limit state",
    4: "Model identifier",
    5: "Temperature format (0=C, else=F)",
    6: "Switch differential (hysteresis)",
    7: "Frost protection mode",
    8: "Calibration - high 8 bit",
    9: "Calibration - low 8 bit",
    10: "Output delay",
    11: "Thermostat address",
    12: "Up/down key limit",
    13: "Sensor selection (0=built-in air,1=remote air,2=floor,3=built-in+floor,4=remote+floor)",
    14: "Optimum start setting",
    15: "Rate of change",
    16: "Program mode (0=5/2,1=7day)",
    17: "Frost protection temperature",
    18: "Set room temperature",
    19: "Floor maximum limit",
    20: "Floor max limit enable/disable",
    21: "On/off state",
    22: "Key lock state",
    23: "Run mode / schedule run state",
    24: "Holiday hours (low byte)",
    25: "Holiday hours (high byte)",
    26: "Temp hold minutes (low byte)",
    27: "Temp hold minutes (high byte)",
    28: "Remote air temp (low byte)",
    29: "Remote air temp (high byte)",
    30: "Floor temp (low byte)",
    31: "Floor temp (high byte)",
    32: "Built-in air temp (low byte)",
    33: "Built-in air temp (high byte)",
    34: "Error code (non-zero indicates fault)",
    35: "Current operating state",
}


@pytest.mark.parametrize(
    "index,expected,comment",
    [
        (i, (0 if i == 5 else 2 if i == 13 else 1 if i == 16 else i), PDF_COMMENTS[i])
        for i in range(0, 36)
    ],
    ids=[f"idx-{i}-{PDF_COMMENTS[i]}" for i in range(0, 36)],
)
def test_dcb_index_has_expected_default(thermostat, index, expected, comment):
    """Index test uses the PDF comment as context and asserts the value.

    On failure the message includes the PDF comment so it's clear which
    protocol field is being tested and what it represents.
    """
    cfg_keys = thermostat.config["keys"]
    assert index in thermostat.dcb, f"DCB index {index} missing ({comment})"
    label = thermostat.dcb[index]["label"]
    # Label should equal the config label (human-friendly name)
    assert label == cfg_keys[index], (
        f"Label mismatch for index {index} ({comment}): {label} != {cfg_keys[index]}"
    )
    value = thermostat.dcb[index]["value"]
    assert value == expected, (
        f"Unexpected value at index {index} ({label} - {comment}): got {value}, expected {expected}"
    )
"""Per-index tests for DCB entries 0..35.

These tests use the `thermostat` fixture (which uses the FakeUH1 fixture)
and assert that each DCB index exists and has the expected default value.

Context for each test is taken from the `config.yml` keys (used by the
library to map index -> label). The PDF's comment column describes the
purpose of each index; here we use the config label as the test context
and include it in the test's id and failure messages.
"""
import pytest


@pytest.mark.parametrize(
    "index,expected",
    [
        (i, (0 if i == 5 else 2 if i == 13 else 1 if i == 16 else i))
        for i in range(0, 36)
    ],
    ids=[f"index-{i}" for i in range(0, 36)],
)
def test_dcb_index_has_expected_default(thermostat, index, expected):
    """Index {index}: verify label from config and expected default value.

    The `expected` value follows the fixture payload defaults used in
    `tests/conftest.py` (deterministic 0..63 mapping with a few overrides).
    The test failure message shows the index and the label from `config.yml`.
    """
    cfg_keys = thermostat.config["keys"]
    assert index in thermostat.dcb, f"DCB index {index} missing"
    label = thermostat.dcb[index]["label"]
    # Ensure label matches config
    assert label == cfg_keys[index], f"Label mismatch for index {index}: {label} != {cfg_keys[index]}"
    value = thermostat.dcb[index]["value"]
    assert value == expected, (
        f"Unexpected value at index {index} ({label}): got {value}, expected {expected}"
    )
