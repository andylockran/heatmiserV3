"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
from heatmiserv3 import heatmiser
from heatmiserv3 import connection
from heatmiserv3 import crc16
import logging, sys
from heatmiserv3.formats import message

from .serial_stubs import MockUH1

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)


class TestHeatmiserThermostatMethods(unittest.TestCase):
    """
    This test case tests the PRT Thermostat in 5/2 mode, where there are 64 bytes of information
    """

    def setUp(self):
        # @TODO - Setup the mock interface for serial to write the tests.
        self.uh1 = MockUH1

    def test_thermo1_temperature(self):
        """ Initialises the thermo1 thermostat, and checks the temperature is at 21*C"""
        thermo1 = heatmiser.HeatmiserThermostatPRT(1, self.uh1)
        assert thermo1.get_target_temp() == 21

    def tearDown(self):
        pass