"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
from heatmiserv3 import heatmiser
from heatmiserv3 import connection
from heatmiserv3 import crc16
import logging, sys
from heatmiserv3.formats import message

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)


class TestHeatmiserPRTThermostatMethods(unittest.TestCase):
    """
    This test case tests the PRT Thermostat in 5/2 mode, where there are 64 bytes of information
    """

    def setUp(self):
        # @TODO - Setup the mock interface for serial to write the tests.
        self.HeatmiserUH1 = connection.HeatmiserUH1("mock", "123")

        self.thermo1 = heatmiser.HeatmiserThermostat(1,"prt", self.HeatmiserUH1)
        self.thermo2 = heatmiser.HeatmiserThermostat(2,"prt", self.HeatmiserUH1)
        self.thermo3 = heatmiser.HeatmiserThermostat(3,"prt", self.HeatmiserUH1)


    def test_thermo1_temperature(self):
        """ Initialises the thermo1 thermostat, and checks the temperature is at 21*C"""

        assert self.thermo1.dcb[18]['label'] == 'Set room temp'
        assert self.thermo1.dcb[18]['value'] == 21

    def tearDown(self):
        pass