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
        self.thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', self.con)

    def test_read_dcb(self):
        """This test makes sure that the values map correctly"""
        data = self.thermostat1.get_dcb()
        print(json.dumps(data, indent=2))
        assert data[11]['value'] == 1



example = ExmapleThermostat()
print(example.test_read_dcb())
example.con.close()