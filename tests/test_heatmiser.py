"""Tests for HeatmiserThermostat and CRC Methods."""
import unittest
from unittest.mock import MagicMock
import serial
from heatmiserv3 import heatmiser, constants
from tests.conftest import FakeUH1, build_prt_default_dcb


class TestCRCMethods(unittest.TestCase):
    """Tests for the CRC Methods."""

    def test_crc16(self):
        """Test that CRC initial state matches."""
        crc = heatmiser.CRC16()
        assert crc.high == crc.low

    def test_update_4_bits(self):
        """Updating 4 bits."""
        crc = heatmiser.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(4)
        assert crc.high == 78
        assert crc.low == 155

    def test_update_8_bits(self):
        crc = heatmiser.CRC16()
        assert crc.high == crc.low
        crc.extract_bits(8)
        assert crc.high == 143
        assert crc.low == 23

    def test_crc16_update(self):
        """Check that updates work with other numbers."""
        crc = heatmiser.CRC16()
        crc.update(4)
        assert crc.high == 161
        assert crc.low == 116

    def test_crc16_run(self):
        """Check calculating CRC for a full byte sequence."""
        crc = heatmiser.CRC16()
        result = crc.run([0x81, 7, 0, 1, 1])
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)


class TestHeatmiserThermostatMethods(unittest.TestCase):
    """Tests for HeatmiserThermostat getters, setters, and protocol logic."""

    def setUp(self):
        self.dcb_data = build_prt_default_dcb()
        self.fake_uh1 = FakeUH1(payload=self.dcb_data, model="prt")
        self.thermostat = heatmiser.HeatmiserThermostat(1, "prt", self.fake_uh1)

    def test_init_and_read_dcb(self):
        """Verify thermostat initializes and DCB is read correctly."""
        assert self.thermostat.address == 1
        assert self.thermostat.model == "prt"
        assert self.thermostat.uh1 is self.fake_uh1
        assert isinstance(self.thermostat.dcb, dict)
        assert 17 in self.thermostat.dcb
        assert self.thermostat.dcb[17]["value"] == 12

    def test_get_frost_temp(self):
        assert self.thermostat.get_frost_temp() == 12

    def test_get_target_temp(self):
        assert self.thermostat.get_target_temp() == 21

    def test_get_floormax_temp(self):
        assert self.thermostat.get_floormax_temp() == 28

    def test_get_status(self):
        assert self.thermostat.get_status() == 1

    def test_get_heating(self):
        assert self.thermostat.get_heating() == 1

    def test_get_thermostat_id(self):
        assert self.thermostat.get_thermostat_id() == 1

    def test_get_temperature_format(self):
        assert self.thermostat.get_temperature_format() == "C"
        # Simulate Fahrenheit format
        self.thermostat.dcb[5]["value"] = 1
        assert self.thermostat.get_temperature_format() == "F"

    def test_get_sensor_selection(self):
        assert self.thermostat.get_sensor_selection() == "Built in air sensor"
        mappings = {
            1: "Remote air sensor",
            2: "Floor sensor",
            3: "Built in + floor",
            4: "Remote + floor",
        }
        for sensor_id, label in mappings.items():
            self.thermostat.dcb[13]["value"] = sensor_id
            assert self.thermostat.get_sensor_selection() == label

    def test_get_program_mode(self):
        assert self.thermostat.get_program_mode() == "5/2 mode"
        self.thermostat.dcb[16]["value"] = 1
        assert self.thermostat.get_program_mode() == "7 day mode"

    def test_get_frost_protection(self):
        assert self.thermostat.get_frost_protection() is True

    def test_get_floor_temp(self):
        # When sensor <= 1 (air sensor), floor temp reads from built-in (offset 33 / 10 = 21.5)
        self.thermostat.dcb[13]["value"] = 0
        assert self.thermostat.get_floor_temp() == 21.5

        # When sensor > 1 (floor sensor), reads from floor (offset 31 / 10 = 24.0)
        self.thermostat.dcb[13]["value"] = 2
        assert self.thermostat.get_floor_temp() == 24.0

    def test_get_sensor_error(self):
        assert self.thermostat.get_sensor_error() == 0

    def test_get_current_state(self):
        assert self.thermostat.get_current_state() == 1

    def test_set_frost_protect_mode(self):
        assert self.thermostat.set_frost_protect_mode(1) is True
        assert self.thermostat.set_frost_protect_mode(0) is True

    def test_set_frost_protect_temp_valid_and_bounds(self):
        # Valid range: [7, 17]
        assert self.thermostat.set_frost_protect_temp(7) is True
        assert self.thermostat.set_frost_protect_temp(12) is True
        assert self.thermostat.set_frost_protect_temp(17) is True

        # Out-of-bounds must be rejected
        assert self.thermostat.set_frost_protect_temp(6) is False
        assert self.thermostat.set_frost_protect_temp(18) is False
        assert self.thermostat.set_frost_protect_temp(-5) is False
        assert self.thermostat.set_frost_protect_temp(100) is False

    def test_set_target_temp_valid_and_bounds(self):
        # Valid range: [5, 35]
        assert self.thermostat.set_target_temp(5) is True
        assert self.thermostat.set_target_temp(21) is True
        assert self.thermostat.set_target_temp(35) is True

        # Out-of-bounds must be rejected
        assert self.thermostat.set_target_temp(4) is False
        assert self.thermostat.set_target_temp(36) is False
        assert self.thermostat.set_target_temp(-1) is False
        assert self.thermostat.set_target_temp(50) is False

    def test_set_floormax_temp_valid_and_bounds(self):
        # Valid range: [20, 45]
        assert self.thermostat.set_floormax_temp(20) is True
        assert self.thermostat.set_floormax_temp(30) is True
        assert self.thermostat.set_floormax_temp(45) is True

        # Out-of-bounds must be rejected
        assert self.thermostat.set_floormax_temp(19) is False
        assert self.thermostat.set_floormax_temp(46) is False
        assert self.thermostat.set_floormax_temp(0) is False

    def test_crc_verification_failure_detected(self):
        """Simulate a corrupted frame with bad CRC and ensure verification fails."""
        # Corrupted frame with invalid checksum
        corrupted_frame = [0x81, 7, 0, 1, constants.FUNC_WRITE, 0xFF, 0xFE]
        valid = self.thermostat._hm_verify_message_crc_uk(
            0x81, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, corrupted_frame
        )
        assert valid is False

    def test_verify_short_response_fails_cleanly(self):
        for response in ([], [0x81, 7, 0, 1, constants.FUNC_WRITE]):
            with self.subTest(response=response):
                assert self.thermostat._hm_verify_message_crc_uk(
                    0x81,
                    constants.HMV3_ID,
                    1,
                    constants.FUNC_WRITE,
                    1,
                    response,
                ) is False

    def test_serial_exception_triggers_reconnect(self):
        """Simulate serial exception in read and verify reconnect attempt."""
        mock_conn = MagicMock()
        mock_conn.read.side_effect = serial.serialutil.SerialException("Connection reset")
        self.thermostat.conn = mock_conn

        # Call _hm_send_msg - should not crash, should attempt reopen on self.uh1
        data = self.thermostat._hm_send_msg(b"test")
        assert data == []
        assert self.fake_uh1.reopened is True

    def test_serial_exception_does_not_crash_response_verification(self):
        mock_conn = MagicMock()
        mock_conn.read.side_effect = serial.serialutil.SerialException("Connection reset")
        self.thermostat.conn = mock_conn

        assert self.thermostat._hm_send_address(1, 0, 0, 0) == []
        assert self.fake_uh1.reopened is True

    def test_verify_message_dest_addr_illegal(self):
        frame = [100, 7, 0, 1, constants.FUNC_WRITE]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(100, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_dest_addr_incorrect(self):
        frame = [160, 7, 0, 1, constants.FUNC_WRITE]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_src_addr_illegal(self):
        frame = [129, 7, 0, 33, constants.FUNC_WRITE]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 33, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_src_addr_incorrect(self):
        frame = [129, 7, 0, 2, constants.FUNC_WRITE]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_unknown_func_code(self):
        frame = [129, 7, 0, 1, 99]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, 99, 1, frame) is False

    def test_verify_message_unexpected_func_code(self):
        frame = [129, 7, 0, 1, constants.FUNC_READ]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_write_incorrect_length(self):
        frame = [129, 8, 0, 1, constants.FUNC_WRITE, 0]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_verify_message_mismatch_length(self):
        frame = [129, 10, 0, 1, constants.FUNC_WRITE]
        crc = heatmiser.CRC16()
        frame += crc.run(frame)
        assert self.thermostat._hm_verify_message_crc_uk(129, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, frame) is False

    def test_tm1_broadcast_single_payload(self):
        tm1 = heatmiser.TM1Thermostat(1, FakeUH1(model="tm1"))
        msg = tm1.form_broadcast_message(constants.TM1_ON_OFF_ADDR, 1)
        assert msg[0] == constants.BROADCAST_ADDR
        assert msg[3] == constants.FUNC_WRITE

    def test_tm1_set_day_schedule_invalid_day(self):
        tm1 = heatmiser.TM1Thermostat(1, FakeUH1(model="tm1"))
        with self.assertRaises(ValueError):
            tm1.set_day_schedule("funday", [0] * 16)
