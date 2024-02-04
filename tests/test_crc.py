
import unittest
from heatmiserv3 import crc16

class TestCRCMethods(unittest.TestCase):
    """Tests for the CRC Methods"""

    def test_crc16(self):
        """Test that CRC matches"""
        crc = crc16.CRC16()
        assert crc.high == crc.low

    def test_update_4_bits(self):
        """Updating 4 bits"""
        crc = crc16.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(4)
        assert crc.high == 78
        assert crc.low == 155
    
    def test_update_8_bits(self):
        crc = crc16.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(8)
        assert crc.high == 143
        assert crc.low == 23

    def test_crc16_update(self):
        """check that updates work with other numbers"""
        crc = crc16.CRC16()
        crc.update(4)
        assert crc.high == 161
        assert crc.low == 116
    
    def test_crc_run(self):
        """Checks that crc runs against a single 8 byte run"""
        example = [1,2,3,4,5,6,7,8]
        crc = crc16.CRC16()
        checksum = crc.run(example)
        assert checksum == [ 146, 71 ]