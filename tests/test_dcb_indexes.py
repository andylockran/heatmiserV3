"""Test that every DCB index 0..35 is present and matches config labels/values."""

def test_dcb_indexes_0_to_35(thermostat):
    cfg_keys = thermostat.config["meta"]
    # Ensure we have keys to check
    overrides = {5: 0, 13: 2, 16: 1}
    for i in range(0, 36):
        assert i in thermostat.dcb, f"Index {i} missing from dcb"
        # label in dcb should match config label
        assert thermostat.dcb[i]["label"] == cfg_keys[i]
        # determine expected value (fixtures override a few indices)
        expected = overrides.get(i, i)
        assert thermostat.dcb[i]["value"] == expected
