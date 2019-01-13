from heatmiserV3 import heatmiser, connection
import json

IP_ADDRESS='192.168.1.57'
PORT='102'

class ExmapleThermostat():
    """Creating an actual thermostat"""
    def __init__(self):
        """Creates serial con and thermostat"""
        self.con = connection.hmserial(IP_ADDRESS, PORT)
        self.con.open()
        self.thermostat1 = heatmiser.HeatmiserThermostat(2, 'prt', self.con)

    def test_read_dcb(self):
        """This test makes sure that the values map correctly"""
        data = self.thermostat1.get_status()
        print(json.dumps(data, indent=2))



example = ExmapleThermostat()
 example.test_read_dcb()
 example.con.close()

# HeatmiserUH1 = connection.HeatmiserUH1(IP_ADDRESS, PORT)
# Thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', HeatmiserUH1)
# print(Thermostat1.get_thermostat_id())