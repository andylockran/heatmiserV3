"""
Example demonstrating a single UH1 Heatmiser Wiring Centre connection
and setting target temperatures across 4 'prt' thermostats.
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

# Set target temperature to 20°C across all thermostats
for tstat_addr, tstat in uh1.thermostats.items():
    success = tstat.set_target_temp(20)
    logging.info("Set address %s target temp to 20°C: %s", tstat_addr, success)

# Read updated values
logging.info("Thermo 1 Target Temp: %s", thermo1.get_target_temp())
