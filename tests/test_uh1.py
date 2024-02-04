import unittest
from heatmiserv3 import connection, constants

from .serial_stubs import MockSerialThermostat
import serial

class TestUH1(unittest.TestCase):
    """Tests related to the connection"""

    def setUp(self):
        """Initialise the serial port and the connection"""
        
        device = MockSerialThermostat
        self.serialport = serial.Serial(device.port)
        # self.serialport = serial.serial_for_url("socket://" + ipaddress + ":" + port)
        ### Serial Connection Settings
        self.serialport.baudrate = constants.COM_BAUD
        self.serialport.bytesize = constants.COM_SIZE
        self.serialport.parity = constants.COM_PARITY
        self.serialport.stopbits = constants.COM_STOP
        self.serialport.timeout = constants.COM_TIMEOUT

        
        self.uh1 = connection.HeatmiserUH1(self.serialport)
        assert self.uh1.serialport.is_open == True