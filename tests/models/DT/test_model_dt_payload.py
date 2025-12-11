def test_dt_payload_semantics(thermostat):
    # thermostat fixture for DT set temperature format to Fahrenheit
    assert thermostat.get_temperature_format() == 'F'
    assert thermostat.get_sensor_selection() == 'Built in air sensor'
    assert thermostat.get_program_mode() == '5/2 mode'
