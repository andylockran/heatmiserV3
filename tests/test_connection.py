import unittest
from heatmiserv3 import connection, constants
import serial
from .serial_stubs import MockSerialThermostat

class TestConnection(unittest.TestCase):

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

    """Tests for the connection code"""
    def test_init(self):
        uh1 = connection.HeatmiserUH1(self.serialport)
        assert uh1.serialport.is_open == True

    def test_open(self):
        uh1 = connection.HeatmiserUH1(self.serialport)
        assert uh1.serialport.is_open == True
        uh1._open()
        assert uh1.serialport.is_open == True
    
    def test_reopen(self):
        uh1 = connection.HeatmiserUH1(self.serialport)
        uh1.serialport.close()
        assert uh1.serialport.is_open == False
        uh1.reopen()
        assert uh1.serialport.is_open == True

    def test_registration(self):
        uh1 = connection.HeatmiserUH1(self.serialport)
        try:
            uh1.registerThermostat(1)
        except Exception as e:
            assert type(e) == AttributeError