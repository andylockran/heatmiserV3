import unittest
from heatmiserv3 import connection, constants
from .serial_stubs import MockUH1

class TestConnection(unittest.TestCase):

    def setUp(self):
        """Initialise the serial port and the connection"""
        
        self.uh1 = MockUH1
        assert self.uh1.serialport.is_open == True

    """Tests for the connection code"""
    def test_init(self):
        assert self.uh1.serialport.is_open == True

    def test_open(self):
        self.uh1._open()
        assert self.uh1.serialport.is_open == True
    
    def test_reopen(self):
        self.uh1.serialport.close()
        assert self.uh1.serialport.is_open == False
        self.uh1.reopen()
        assert self.uh1.serialport.is_open == True