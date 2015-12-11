import unittest
from heatmiserV3 import heatmiser

class TestCRCMethods(unittest.TestCase):

    def test_crc16(self):
        crc = heatmiser.crc16()
        assert crc.high == crc.low

    def test_Update4Bits(self):
        crc = heatmiser.crc16()
        assert crc.high == crc.low
        crc.Update4Bits(4)
        assert crc.high == 78
        assert crc.low == 155

        crc = heatmiser.crc16()
        assert crc.high == crc.low
        crc.Update4Bits(8)
        assert crc.high == 143
        assert crc.low == 23

    def test_CRC16_Update(self):
        crc = heatmiser.crc16()
        crc.CRC16_Update(4)
        assert crc.high == 161
        assert crc.low == 116

