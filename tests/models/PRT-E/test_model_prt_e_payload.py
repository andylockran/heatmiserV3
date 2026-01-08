def test_prt_e_payload_semantics(thermostat):
    assert thermostat.get_temperature_format() == 'C'
    assert thermostat.get_sensor_selection() == 'Remote + floor'
    # floor temp should come from index 31 when sensor selection includes floor
    assert abs(thermostat.get_floor_temp() - 23.5) < 0.01
