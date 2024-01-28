"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
from heatmiserv3 import heatmiser


class TestCRCMethods(unittest.TestCase):
    """Tests for the CRC Methods"""

    def test_crc16(self):
        """Test that CRC matches"""
        crc = heatmiser.CRC16()
        assert crc.high == crc.low

    def test_update_4_bits(self):
        """Updating 4 bits"""
        crc = heatmiser.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(4)
        assert crc.high == 78
        assert crc.low == 155
    
    def test_update_8_bits(self):
        crc = heatmiser.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(8)
        assert crc.high == 143
        assert crc.low == 23

    def test_crc16_update(self):
        """check that updates work with other numbers"""
        crc = heatmiser.CRC16()
        crc.update(4)
        assert crc.high == 161
        assert crc.low == 116


class TestHeatmiserThermostatMethods(unittest.TestCase):
    """
    Tests for the Heatmiser functions.
    """

    def setUp(self):
        # @TODO - Setup the mock interface for serial to write the tests.
        # self.uh1 = connection.HeatmiserUH1('192.168.1.57', '102')
        # self.thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', self.uh1)
        pass
