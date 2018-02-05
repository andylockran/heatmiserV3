"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
import json
from mock import Mock
from heatmiserV3 import heatmiser


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
        serspec = ['read', 'write', 'open', 'close']
        serport = Mock(name="serport", spec=serspec)
        serport.open.return_value = True
        serport.close.return_value = True
        serport.read.return_value = [
            129, 75, 0, 1, 0, 0, 0, 64, 0, 0, 64, 0, 19, 3, 0, 1, 0, 0, 0, 0,
            1, 0, 0, 0, 20, 0, 12, 22, 28, 1, 1, 0, 0, 0, 0, 0, 0, 255, 255,
            255, 255, 0, 170, 0, 1, 3, 22, 22, 22, 8, 0, 21, 9, 30, 16, 16, 30,
            22, 23, 0, 17, 9, 0, 21, 22, 0, 16, 24, 0, 16, 24, 0, 16, 127, 117
        ]
        self.con = serport
        self.thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', self.con)

    def test__hm_send_message(self):
        """This is an example message that returns the stuff above"""
        message = b'\x01\n\x81\x00\x00\x00\xff\xff,\t'
        pass

    def test_get_dcb(self):
        """
        Checks that the dcb returns full length.
        Either 64 bits for 5/2 mode, or 159 for 7 day mode.
        """
        data = self.thermostat1.get_dcb()
        print(json.dumps(data, indent=2))
        assert(data[11]['value'] == 1)
        assert(len(data) == 64 or len(data) == 159)

    def test_get_target_temperature(self):
        """
        Checks the target temperature is set to 22*C.
        """
        response = self.thermostat1.get_target_temperature()
        assert(response == 22)
        