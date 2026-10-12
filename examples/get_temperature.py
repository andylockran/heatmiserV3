"""
Example demonstrating a single UH1 Heatmiser Wiring Centre connection
and reading floor temperatures from 4 'prt' thermostats.
"""
import logging
from heatmiserv3 import connection, heatmiser

IP_ADDRESS = "192.168.1.57"
PORT = "102"

logging.basicConfig(level=logging.INFO)

# Create a HeatmiserUH1 connection
uh1 = connection.HeatmiserUH1(IP_ADDRESS, PORT)

# Add thermostats
thermo1 = heatmiser.HeatmiserThermostat(1, "prt", uh1)
thermo2 = heatmiser.HeatmiserThermostat(2, "prt", uh1)
thermo3 = heatmiser.HeatmiserThermostat(3, "prt", uh1)
thermo4 = heatmiser.HeatmiserThermostat(4, "prt", uh1)

# Show them registered against the UH1
for tstat_addr, tstat in uh1.thermostats.items():
    logging.info("Address %s Floor Temp: %s", tstat_addr, tstat.get_floor_temp())

# You can also read directly from individual thermostat objects:
logging.info("Thermo 1 Target Temp: %s", thermo1.get_target_temp())
logging.info("Thermo 1 Floor Temp: %s", thermo1.get_floor_temp())
