import unittest
from heatmiserV3 import heatmiser
from mock import Mock
import json

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

class TestHeatmiserThermostatMethods(unittest.TestCase):

    def test_readDCB(self):
        """This test makes sure that the values map correctly"""
        serspec = ['read', 'write']
        serport = Mock(name="serport", spec=serspec)
        serport.read.return_value = [129,
                                     75,
                                     0,
                                     1,
                                     0,
                                     0,
                                     0,
                                     64,
                                     0,
                                     0,
                                     64,
                                     0,
                                     19,
                                     3,
                                     0,
                                     1,
                                     0,
                                     0,
                                     0,
                                     0,
                                     1,
                                     0,
                                     0,
                                     0,
                                     20,
                                     0,
                                     12,
                                     22,
                                     28,
                                     1,
                                     1,
                                     0,
                                     0,
                                     0,
                                     0,
                                     0,
                                     0,
                                     255,
                                     255,
                                     255,
                                     255,
                                     0,
                                     170,
                                     0,
                                     1,
                                     3,
                                     22,
                                     22,
                                     22,
                                     8,
                                     0,
                                     21,
                                     9,
                                     30,
                                     16,
                                     16,
                                     30,
                                     22,
                                     23,
                                     0,
                                     17,
                                     9,
                                     0,
                                     21,
                                     22,
                                     0,
                                     16,
                                     24,
                                     0,
                                     16,
                                     24,
                                     0,
                                     16,
                                     127,
                                     117]
        thermostat1 = heatmiser.HeatmiserThermostat(1, 'prt', serport)
        data = thermostat1._hm_read_address()
        print(json.dumps(data, indent=2))
        assert(data[11]['value'] == 1)

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
