import unittest
from heatmiserV3 import heatmiser, connection
import json

class TestCRCMethods(unittest.TestCase):

    def setUp(self):
        self.con = connection.hmserial('192.168.1.57','100')
        self.con.open()

    def test_readDCB(self):
        """This test makes sure that the values map correctly"""
        data = heatmiser._hm_read_address(1, 'prt', self.con)
        print(json.dumps(data, indent=2))
        assert(data == 0)

    def tearDown(self):
        self.con.close()