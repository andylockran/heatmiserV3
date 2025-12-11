def test_prt_hw_payload_semantics(thermostat):
    assert thermostat.get_temperature_format() == 'C'
    assert thermostat.get_sensor_selection() == 'Floor sensor'
    # check floor temp uses index 31
    assert abs(thermostat.get_floor_temp() - 18.5) < 0.01
