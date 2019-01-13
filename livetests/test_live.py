"""Live tests"""
import unittest
import json
from heatmiserV3 import heatmiser, connection


class TestLiveHeatmiserThermostat(unittest.TestCase):
    """Testing an actual thermostat"""
    def setUp(self):
        """Creates serial con and thermostat"""
        self.con = connection.hmserial('192.168.1.57', '102')
        self.con.open()
        self.thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', self.con)

    def test_read_dcb(self):
        """This test makes sure that the values map correctly"""
        data = self.thermostat1.get_target_temperature()
        print(json.dumps(data, indent=2))
        assert data[11]['value'] == 1

    def tearDown(self):
        """Shutdown serial conn"""
        self.con.close()
