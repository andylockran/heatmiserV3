"""
Example demonstrating connection via a local RS485 serial device (e.g. /dev/ttyACM0)
and querying floor temperature from a PRT thermostat.
"""
import logging
from heatmiserv3 import connection, heatmiser

logging.basicConfig(level=logging.INFO)

# Connect directly to a local USB RS485 adapter
uh1 = connection.HeatmiserUH1(dev="/dev/ttyACM0")
thermostat = heatmiser.HeatmiserThermostat(1, "prt", uh1)

logging.info("Floor temperature: %s", thermostat.get_floor_temp())
