import unittest
from heatmiserV3 import heatmiser, protocol, constants
from mock import Mock
from datetime import datetime, time

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

class TestProtocolSerial(unittest.TestCase):
    def setUp(self):
        self.protocol = protocol.HeatmiserV3Protocol(constants.Constants.CONNECTION_TYPES[0])

    def test_crc16(self):
        crc = self.protocol.crc16([4])
        assert crc == 41332
        # As defined in original test
        assert crc & 0xff == 116
        assert crc >> 8 == 161

    def test_get_status_cmd(self):
        cmd = self.protocol.read_dcb_serial(5, 42)
        assert len(cmd) == 8

    def test_parse_response(self):
        resp = [129, 62, 0, 5, 0, 0, 0, 51, 0, 0, 51, 0, 16, 5, 5, 0, 0, 1, 0, 0, 0, 0, 0, 0, 5, 22, 42, 45, 6, 0, 9, 0, 16, 0, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0, 6, 30, 9, 0, 15, 30, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0, 180, 24]
        dcb = self.protocol.parse_serial_response(resp, constants.Constants.FUNC_READ)
        status = self.protocol.dcb_to_status(dcb)
        assert status['product']['model'] == 'TM1'
        assert status['product']['version'] == 1.6
        assert len(status['timer']) == 2
        assert len(status['timer'][0]) == 2 # a pair of on, off times
        assert len(status['timer'][1]) == 2 # a pair of on, off times
        assert status['timer'][0][0].get('on', None) == time(6, 0)
        assert status['timer'][0][0].get('off', None) == time(9, 0)

class TestProtocolTCP(unittest.TestCase):
    def setUp(self):
        self.protocol = protocol.HeatmiserV3Protocol(constants.Constants.CONNECTION_TYPES[1])

    def test_get_status_cmd(self):
        cmd = self.protocol.read_dcb_tcp(1234)
        assert len(cmd) == 11
