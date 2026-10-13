"""Tests for HeatmiserThermostat and CRC Methods."""
import unittest
from unittest.mock import MagicMock, call, patch
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

    def test_set_on_off_valid_and_bounds(self):
        assert self.thermostat.set_on_off(1) is True
        assert self.thermostat.set_on_off(0) is True
        assert self.thermostat.set_on_off(True) is True
        assert self.thermostat.set_on_off(False) is True
        assert self.thermostat.set_on_off(2) is False
        assert self.thermostat.set_on_off(-1) is False
        assert self.thermostat.set_on_off("on") is False

    def test_get_on_off(self):
        self.thermostat.dcb[21] = {"value": 1, "label": "On/off"}
        assert self.thermostat.get_on_off() == 1
        self.thermostat.dcb[21] = {"value": 0, "label": "On/off"}
        assert self.thermostat.get_on_off() == 0

    def test_set_key_lock_valid_and_bounds(self):
        assert self.thermostat.set_key_lock(1) is True
        assert self.thermostat.set_key_lock(0) is True
        assert self.thermostat.set_key_lock(True) is True
        assert self.thermostat.set_key_lock(False) is True
        assert self.thermostat.set_key_lock(2) is False
        assert self.thermostat.set_key_lock(-1) is False
        assert self.thermostat.set_key_lock("lock") is False

    def test_get_key_lock(self):
        self.thermostat.dcb[22] = {"value": 1, "label": "Key lock"}
        assert self.thermostat.get_key_lock() == 1
        self.thermostat.dcb[22] = {"value": 0, "label": "Key lock"}
        assert self.thermostat.get_key_lock() == 0

    def test_set_temperature_format_valid_and_bounds(self):
        assert self.thermostat.set_temperature_format(0) is True
        assert self.thermostat.set_temperature_format(1) is True
        assert self.thermostat.set_temperature_format("C") is True
        assert self.thermostat.set_temperature_format("c") is True
        assert self.thermostat.set_temperature_format("Celsius") is True
        assert self.thermostat.set_temperature_format("F") is True
        assert self.thermostat.set_temperature_format("f") is True
        assert self.thermostat.set_temperature_format("Fahrenheit") is True
        assert self.thermostat.set_temperature_format(2) is False
        assert self.thermostat.set_temperature_format(-1) is False
        assert self.thermostat.set_temperature_format(True) is False
        assert self.thermostat.set_temperature_format("Kelvin") is False

    def test_set_differential_valid_and_bounds(self):
        assert self.thermostat.set_differential(1) is True
        assert self.thermostat.set_differential(2) is True
        assert self.thermostat.set_differential(3) is True
        assert self.thermostat.set_differential(0) is False
        assert self.thermostat.set_differential(4) is False
        assert self.thermostat.set_differential(-1) is False
        assert self.thermostat.set_differential(True) is False

    def test_get_differential(self):
        self.thermostat.dcb[6] = {"value": 2, "label": "Switch Differential"}
        assert self.thermostat.get_differential() == 2

    def test_set_sensor_selection_valid_and_bounds(self):
        for mode in (0, 1, 2, 3, 4):
            assert self.thermostat.set_sensor_selection(mode) is True
        assert self.thermostat.set_sensor_selection("built in") is True
        assert self.thermostat.set_sensor_selection("built-in") is True
        assert self.thermostat.set_sensor_selection("remote air") is True
        assert self.thermostat.set_sensor_selection("floor") is True
        assert self.thermostat.set_sensor_selection("built-in+floor") is True
        assert self.thermostat.set_sensor_selection("remote+floor") is True
        assert self.thermostat.set_sensor_selection(5) is False
        assert self.thermostat.set_sensor_selection(-1) is False
        assert self.thermostat.set_sensor_selection(True) is False
        assert self.thermostat.set_sensor_selection("invalid_mode") is False

    def test_set_holiday_hours_valid_and_bounds(self):
        assert self.thermostat.set_holiday_hours(0) is True
        assert self.thermostat.set_holiday_hours(168) is True
        assert self.thermostat.set_holiday_hours(65535) is True
        assert self.thermostat.set_holiday_hours(-1) is False
        assert self.thermostat.set_holiday_hours(65536) is False
        assert self.thermostat.set_holiday_hours(True) is False

    def test_get_holiday_hours(self):
        self.thermostat.dcb[24] = {"value": 1, "label": "Holiday hours"}
        self.thermostat.dcb[25] = {"value": 44, "label": "Holiday hours"}
        # (1 << 8) | 44 = 300
        assert self.thermostat.get_holiday_hours() == 300

    def test_set_temp_hold_valid_and_bounds(self):
        assert self.thermostat.set_temp_hold(0) is True
        assert self.thermostat.set_temp_hold(60) is True
        assert self.thermostat.set_temp_hold(1800) is True
        assert self.thermostat.set_temp_hold(120, temperature=22) is True
        assert self.thermostat.set_temp_hold(-1) is False
        assert self.thermostat.set_temp_hold(1801) is False
        assert self.thermostat.set_temp_hold(True) is False
        assert self.thermostat.set_temp_hold(60, temperature=4) is False
        assert self.thermostat.set_temp_hold(60, temperature=36) is False
        assert self.thermostat.set_temp_hold(60, temperature=True) is False

    def test_get_temp_hold_minutes(self):
        self.thermostat.dcb[26] = {"value": 0, "label": "Temp hold mins"}
        self.thermostat.dcb[27] = {"value": 90, "label": "Temp hold mins"}
        assert self.thermostat.get_temp_hold_minutes() == 90

    def test_set_time_valid_and_bounds(self):
        assert self.thermostat.set_time(1, 14, 30, 0) is True
        assert self.thermostat.set_time(7, 23, 59, 59) is True
        assert self.thermostat.set_time(0, 14, 30, 0) is False
        assert self.thermostat.set_time(8, 14, 30, 0) is False
        assert self.thermostat.set_time(1, 24, 30, 0) is False
        assert self.thermostat.set_time(1, -1, 30, 0) is False
        assert self.thermostat.set_time(1, 14, 60, 0) is False
        assert self.thermostat.set_time(1, 14, 30, 60) is False
        assert self.thermostat.set_time(True, 14, 30, 0) is False

    def test_get_time(self):
        self.thermostat.dcb[36] = {"value": 3, "label": "Week 1~7"}
        self.thermostat.dcb[37] = {"value": 15, "label": "Hour"}
        self.thermostat.dcb[38] = {"value": 45, "label": "Min"}
        self.thermostat.dcb[39] = {"value": 30, "label": "Sec"}
        rtc = self.thermostat.get_time()
        assert rtc == {"week": 3, "hour": 15, "min": 45, "sec": 30}


class TestPRTHWThermostatMethods(unittest.TestCase):
    """Tests for PRTHWThermostat methods and restrictions."""

    def setUp(self):
        dcb_data = build_prt_default_dcb()
        # Ensure DCB is large enough for PRTHW (e.g. index 36 is hot water state)
        while len(dcb_data) <= 36:
            dcb_data.append(0)
        dcb_data[4] = constants.MODEL_PRTHW
        dcb_data[35] = 1  # heating on
        dcb_data[36] = 1  # hot water on
        self.fake_uh1 = FakeUH1(payload=dcb_data, model="prt-hw")
        self.thermostat = heatmiser.PRTHWThermostat(1, self.fake_uh1)

    def test_init_prthw(self):
        assert self.thermostat.address == 1
        assert self.thermostat.model == "prt-hw"

    def test_prthw_sensor_selection_restriction(self):
        # PRT-HW hardware only supports built-in sensor (mode 0)
        assert self.thermostat.set_sensor_selection(0) is True
        assert self.thermostat.set_sensor_selection("built in") is True
        assert self.thermostat.set_sensor_selection(1) is False
        assert self.thermostat.set_sensor_selection(2) is False
        assert self.thermostat.set_sensor_selection(3) is False
        assert self.thermostat.set_sensor_selection(4) is False
        assert self.thermostat.set_sensor_selection("remote air") is False

    def test_prthw_hot_water_boost(self):
        assert self.thermostat.set_hot_water_boost(1) is True
        assert self.thermostat.set_hot_water_boost(0) is True
        assert self.thermostat.set_hot_water_boost(True) is True
        assert self.thermostat.set_hot_water_boost(False) is True
        assert self.thermostat.set_hot_water_boost(2) is False
        assert self.thermostat.set_hot_water_boost(-1) is False
        assert self.thermostat.set_hot_water_boost("boost") is False

    def test_prthw_get_states(self):
        self.thermostat.dcb[35] = {"value": 1, "label": "Current heating state"}
        self.thermostat.dcb[36] = {"value": 0, "label": "Current Hot water state"}
        assert self.thermostat.get_heating_state() == 1
        assert self.thermostat.get_hot_water_state() == 0


class TestHeatmiserThermostatCachingAndDelegation(unittest.TestCase):
    """Tests for DCB caching, TTL, invalidation, and UH1 bus delegation."""

    def setUp(self):
        self.dcb_data = build_prt_default_dcb()
        self.fake_uh1 = FakeUH1(payload=self.dcb_data, model="prt")
        self.thermostat = heatmiser.HeatmiserThermostat(1, "prt", self.fake_uh1, cache_ttl=2.0)

    def test_dcb_cache_hit(self):
        with patch.object(self.thermostat, "_hm_send_address") as mock_send:
            dcb1 = self.thermostat.read_dcb()
            dcb2 = self.thermostat.read_dcb()
            assert dcb1 is dcb2
            mock_send.assert_not_called()

    def test_dcb_cache_force_refresh(self):
        with patch.object(self.thermostat, "_hm_send_address", wraps=self.thermostat._hm_send_address) as mock_send:
            self.thermostat.read_dcb(force=True)
            mock_send.assert_called_once()

    def test_dcb_cache_invalidation(self):
        with patch.object(self.thermostat, "_hm_send_address", wraps=self.thermostat._hm_send_address) as mock_send:
            self.thermostat.read_dcb()
            mock_send.reset_mock()
            self.thermostat.invalidate_cache()
            self.thermostat.read_dcb()
            mock_send.assert_called_once()

    def test_write_operation_invalidates_cache(self):
        with patch.object(self.thermostat, "_hm_send_address", wraps=self.thermostat._hm_send_address) as mock_send:
            self.thermostat.read_dcb()
            mock_send.reset_mock()
            self.thermostat.set_target_temp(21)
            self.thermostat.read_dcb()
            assert mock_send.call_count == 2

    def test_set_cache_ttl(self):
        self.thermostat.set_cache_ttl(10.5)
        assert self.thermostat.cache_ttl == 10.5
        import pytest
        with pytest.raises(ValueError):
            self.thermostat.set_cache_ttl(-1.0)

    def test_delegation_to_uh1_transact(self):
        mock_uh1 = MagicMock()
        mock_uh1.transact.return_value = [0x81, 7, 0, 1, 1, 0xb0, 0xeb]
        stat = heatmiser.HeatmiserThermostat(1, "prt", mock_uh1)
        res = stat._hm_send_msg(b"test")
        assert res == [0x81, 7, 0, 1, 1, 0xb0, 0xeb]
        assert mock_uh1.transact.call_args_list[-1] == call(b"test", 159)

    def test_delegation_to_uh1_transact_exception_handled(self):
        mock_uh1 = MagicMock()
        mock_uh1.transact.side_effect = serial.serialutil.SerialException("Port disconnected")
        stat = heatmiser.HeatmiserThermostat(1, "prt", mock_uh1)
        res = stat._hm_send_msg(b"test")
        assert res == []
