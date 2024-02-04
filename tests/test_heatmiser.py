"""Tests for HeatmiserThermostat and CRC Methods"""
import unittest
from heatmiserv3 import heatmiser
from heatmiserv3 import connection
import logging, sys
from heatmiserv3.formats import message

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)

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

    def test_message_struct_thermo1(self):
        default_message = b'\x01\x0a\x81\x00\x00\x00\xff\xff,\t'
        crc = heatmiser.CRC16()
        data = list(default_message)
        data = data + crc.run(data)
        logging.debug(data)
        assert data[0] == 1 ## Thermostat is 1
        assert data[1] == 10 ## Read operations
        assert data[2] == 129 ## Source address
        assert data[3] == 0 ## Read functionCode
        assert data[4] == 0 ## Start Address of DCB
        assert data[5] == 0 ## Start Address of DCB
        assert data[6] == 255 ## End Address of DCB
        assert data[7] == 255 ## End Address of DCB
        assert data[8] == 44 ## No idea what this is @TODO
        assert data[9] == 9 ## No idea what this is @TODO
        assert data[10] == 212 ## CRC low
        assert data[11] == 141 ## CRC high

    def test_thermo3_temperature(self):
        """ Initialises the thermo3 thermostat, and checks the temperature is at 21*C"""
        # self.thermo3.get_target_temp()
        assert self.thermo3.dcb[18] == {'label': 'Set room temp', 'value': 21}

    def tearDown(self):
        pass