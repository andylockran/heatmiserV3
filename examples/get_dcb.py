from heatmiserV3 import heatmiser, connection
import logging

IP_ADDRESS='192.168.1.57'
PORT='102'

logging.basicConfig(level=logging.INFO)

# Create a HeatmiserUH! connection
HeatmiserUH1 = connection.HeatmiserUH1(IP_ADDRESS, PORT)

# Add my thermostats
thermo1 = heatmiser.HeatmiserThermostat(1, 'prt', HeatmiserUH1)
thermo2 = heatmiser.HeatmiserThermostat(2, 'prt', HeatmiserUH1)
thermo3 = heatmiser.HeatmiserThermostat(3, 'prt', HeatmiserUH1)
thermo4 = heatmiser.HeatmiserThermostat(4, 'prt', HeatmiserUH1)

# Show them registeresd against the UH1
for tstat in HeatmiserUH1.thermostats:
    logging.info(HeatmiserUH1.thermostats[tstat].set_target_temp(20))