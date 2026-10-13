from heatmiserv3 import connection, heatmiser


uh1 = connection.HeatmiserUH1(dev="/dev/ttyACM0")
thermostat = heatmiser.HeatmiserThermostat(1, "prt", uh1)

print(thermostat.get_floor_temp())
