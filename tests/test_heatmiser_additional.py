"""Additional tests for heatmiserv3 to improve coverage."""
import unittest

from heatmiserv3 import heatmiser, constants


class TestCRCAndVerify(unittest.TestCase):
    def test_crc_consistent(self):
        data = [0x01, 0x02, 0x03, 0x04]
        crc = heatmiser.CRC16()
        crc_bytes = crc.run(data)
        # Running again on same data yields same CRC
        crc2 = heatmiser.CRC16()
        self.assertEqual(crc_bytes, crc2.run(data))

    def test_verify_message_crc_ok(self):
        # Build a minimal valid 'write' response: 7 bytes total
        dest_addr = 0x81  # 129, valid master range
        frame_len = 7
        frame_len_l = frame_len & constants.BYTEMASK
        frame_len_h = (frame_len >> 8) & constants.BYTEMASK
        source_addr = 0x01
        func_code = constants.FUNC_WRITE

        rxmsg = [dest_addr, frame_len_l, frame_len_h, source_addr, func_code]
        crc = heatmiser.CRC16()
        checksum = crc.run(rxmsg)
        datal = rxmsg + checksum

        # Create a bare instance (avoid __init__ side-effects)
        th = object.__new__(heatmiser.HeatmiserThermostat)

        ok = heatmiser.HeatmiserThermostat._hm_verify_message_crc_uk(
            th, dest_addr, constants.HMV3_ID, source_addr, func_code, 1, datal
        )
        self.assertTrue(ok)

    def test_verify_message_crc_bad_crc(self):
        dest_addr = 0x81
        frame_len = 7
        frame_len_l = frame_len & constants.BYTEMASK
        frame_len_h = (frame_len >> 8) & constants.BYTEMASK
        source_addr = 0x01
        func_code = constants.FUNC_WRITE

        rxmsg = [dest_addr, frame_len_l, frame_len_h, source_addr, func_code]
        crc = heatmiser.CRC16()
        checksum = crc.run(rxmsg)
        # Corrupt one byte in the message (but leave checksum unchanged)
        bad = rxmsg.copy()
        bad[4] = (bad[4] + 1) & constants.BYTEMASK
        datal = bad + checksum

        th = object.__new__(heatmiser.HeatmiserThermostat)
        ok = heatmiser.HeatmiserThermostat._hm_verify_message_crc_uk(
            th, dest_addr, constants.HMV3_ID, source_addr, func_code, 1, datal
        )
        self.assertFalse(ok)


class TestMessageFormatting(unittest.TestCase):
    def test_form_message_and_crc(self):
        # Create instance without running __init__
        th = object.__new__(heatmiser.HeatmiserThermostat)
        # Provide minimal attributes used by the tested methods
        th.address = 1

        # Test read message formation
        msg = heatmiser.HeatmiserThermostat._hm_form_message(
            th, thermostat_id=1, protocol=constants.HMV3_ID, source=2, function=constants.FUNC_READ, start=0x0010, payload=[]
        )
        # For read, payload_length is 0 and length fields should be RW_LENGTH_ALL
        self.assertIsInstance(msg, list)
        # Now form message including CRC
        msg_crc = heatmiser.HeatmiserThermostat._hm_form_message_crc(
            th, thermostat_id=1, protocol=constants.HMV3_ID, source=2, function=constants.FUNC_READ, start=0x0010, payload=[]
        )
        # CRC adds two bytes
        self.assertEqual(len(msg_crc), len(msg) + 2)


class TestUH1Register(unittest.TestCase):
    def test_register_thermostat_adds_entry_and_returns_port(self):
        from heatmiserv3.connection import HeatmiserUH1

        # Create UH1 instance without calling __init__
        uh = object.__new__(HeatmiserUH1)
        uh.thermostats = {}
        sentinel_port = type('P', (), {'close': lambda self: None})()
        uh._serport = sentinel_port

        th = type('T', (), {})()
        th.address = 5

        ret = HeatmiserUH1.registerThermostat(uh, th)
        self.assertIs(ret, sentinel_port)
        self.assertIn(5, uh.thermostats)


if __name__ == '__main__':
    unittest.main()
