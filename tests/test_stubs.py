"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
from heatmiserv3 import heatmiser
from heatmiserv3 import connection
from heatmiserv3 import crc16
import logging, sys
from heatmiserv3.formats import message

from .serial_stubs import MockUH1, MockHeatmiserPRT

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)


class TestStubs(unittest.TestCase):
    """
    This test case tests the PRT Thermostat in 5/2 mode, where there are 64 bytes of information
    """

    def setUp(self):
        # @TODO - Setup the mock interface for serial to write the tests.
        self.uh1 = MockUH1
        self.thermo1 = MockHeatmiserPRT(1, self.uh1)

    def test_thermo1_get_target_temperature(self):
        """ Initialises the thermo1 thermostat, and checks the temperature is at 21*C"""
        assert self.thermo1.get_target_temp() == 21

    # def test_thermo1_set_target_temperature(self):
    #     """ Initialises the thermo1 thermostat, and checks the temperature is at 21*C"""
    #     self.thermo1.set_target_temp(22)
    #     assert self.thermo1.get_target_temp() == 22


    def tearDown(self):
        pass