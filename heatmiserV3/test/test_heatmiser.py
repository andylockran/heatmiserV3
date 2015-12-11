import unittest
from heatmiserV3 import heatmiser
from mock import Mock


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

    def test_hmSendAddress(self):
        dest = 4
        addr = 21
        state = 1
        rw = 1
        assert rw == 1
        serspec = ['read','write']
        serport = Mock(name="serport",spec=serspec)
        serport.read.return_value = [129, 62, 0, 5, 0, 0, 0, 51, 0, 0, 51, 0, 16, 5, 5, 0, 0, 1, 0, 0, 0, 0, 0, 0, 5, 22, 42, 45, 6, 0, 9, 0, 16, 0, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0, 6, 30, 9, 0, 15, 30, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0, 180, 24]
        request = heatmiser.hmSendAddress(5,42,1,0,serport)
        

    def hmFormMsg(self):
        pass

    def hmFormMsgCRC(self):
        pass

    def hmVerifyMsgCRCOK(self):
        pass

    def hmSendMsg(self):
        pass

    def hmReadAddress(self):
        pass
