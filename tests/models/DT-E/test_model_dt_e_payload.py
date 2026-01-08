def test_dt_e_payload_semantics(thermostat):
    assert thermostat.get_temperature_format() == 'C'
    assert thermostat.get_sensor_selection() == 'Remote air sensor'
    assert thermostat.get_program_mode() == '7 day mode'
