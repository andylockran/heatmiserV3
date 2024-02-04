import unittest
from heatmiserv3 import connection

class TestConnection(unittest.TestCase):
    """Tests for the connection code"""
    def test_init(self):
        uh1 = connection.HeatmiserUH1("mock", 123)
        assert uh1.status == True

    def test_open(self):
        uh1 = connection.HeatmiserUH1("mock", 123)
        assert uh1.status == True
        uh1._open()
        assert uh1.status == True
    
    def xtest_reopen(self):
        """Skipping this test as doesn't work with mock implementation."""
        uh1 = connection.HeatmiserUH1("mock", 123)
        uh1.serialport.close()
        assert uh1.serialport.closed == True

    def test_registration(self):
        uh1 = connection.HeatmiserUH1("mock", 123)
        try:
            uh1.registerThermostat(1)
        except Exception as e:
            assert type(e) == AttributeError