from heatmiserv3 import heatmiser, connection
import logging

"""
This examples shows a simple setup of a single UH1 Heatmiser Wiring Centre, and the addition of 4 'prt' thermostats.

The script below then iterates through, setting the target temp on them all to 20.

"""


IP_ADDRESS = "192.168.1.57"
PORT = "102"

logging.basicConfig(level=logging.INFO)

# Create a HeatmiserUH! connection
HeatmiserUH1 = connection.HeatmiserUH1(IP_ADDRESS, PORT)

# Add my thermostats
thermo1 = heatmiser.HeatmiserThermostat(1, "prt", HeatmiserUH1)
thermo2 = heatmiser.HeatmiserThermostat(2, "prt", HeatmiserUH1)
thermo3 = heatmiser.HeatmiserThermostat(3, "prt", HeatmiserUH1)
thermo4 = heatmiser.HeatmiserThermostat(4, "prt", HeatmiserUH1)

# Show them registeresd against the UH1
for tstat in HeatmiserUH1.thermostats:
    logging.info(HeatmiserUH1.thermostats[tstat].get_floor_temp())


# You can also just hit the themos directly:

thermo1.get_target_temp()
thermo1.get_floor_temp()
