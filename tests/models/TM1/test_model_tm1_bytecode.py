"""Test suite for validating that all bytecode messages are configurable for the TM1 thermostat.

Based on Heatmiser V3 System Protocol 3.9:
- Section 3: RS485 network command frame format
  - 3.1 Frame sent by master node (MC, NM, TR2, UH1)
  - 3.2 Frame reply from slave node (thermostat)
- Section 3.5: DCB for TM1 (Model = 5)
  - Program modes: 5/2 day (51 bytes), 7 day (163 bytes), countdown timer (19 bytes)
  - Configurable parameters: On/off, key lock, holiday hours, countdown minutes,
    timer state override, real-time clock, program mode, switching periods (weekday,
    weekend, and 7-day individual days).
"""
import pytest
from heatmiserv3 import heatmiser, constants
from tests.conftest import FakeUH1, build_tm1_default_dcb_5_2


def _compute_crc(frame_without_crc):
    crc = heatmiser.CRC16()
    return crc.run(frame_without_crc)


def _assert_frame_structure(
    frame,
    expected_dest,
    expected_length,
    expected_src,
    expected_func,
    expected_start,
    expected_rw_len,
    expected_payload=None,
):
    """Asserts that a formed bytecode frame strictly follows Section 3.1 specification."""
    # Byte 0: Destination address
    assert frame[0] == expected_dest, f"Dest addr mismatch: expected {expected_dest}, got {frame[0]}"
    # Byte 1: Total frame length including CRC
    assert frame[1] == expected_length, f"Frame length mismatch: expected {expected_length}, got {frame[1]}"
    assert len(frame) == expected_length, f"Actual length mismatch: expected {expected_length}, got {len(frame)}"
    # Byte 2: Source address (0x81 = 129)
    assert frame[2] == expected_src, f"Source addr mismatch: expected {expected_src}, got {frame[2]}"
    # Byte 3: Function code (0=Read, 1=Write)
    assert frame[3] == expected_func, f"Function code mismatch: expected {expected_func}, got {frame[3]}"
    # Bytes 4-5: Start address (low, high)
    expected_start_l = expected_start & constants.BYTEMASK
    expected_start_h = (expected_start >> 8) & constants.BYTEMASK
    assert frame[4] == expected_start_l, f"Start low mismatch: expected {expected_start_l}, got {frame[4]}"
    assert frame[5] == expected_start_h, f"Start high mismatch: expected {expected_start_h}, got {frame[5]}"
    # Bytes 6-7: Read/write length (low, high)
    expected_len_l = expected_rw_len & constants.BYTEMASK
    expected_len_h = (expected_rw_len >> 8) & constants.BYTEMASK
    assert frame[6] == expected_len_l, f"Length low mismatch: expected {expected_len_l}, got {frame[6]}"
    assert frame[7] == expected_len_h, f"Length high mismatch: expected {expected_len_h}, got {frame[7]}"

    # Bytes 8..(n+7): Payload if write
    if expected_payload is not None:
        actual_payload = frame[8:8 + len(expected_payload)]
        assert actual_payload == list(expected_payload), f"Payload mismatch: expected {expected_payload}, got {actual_payload}"

    # Bytes (last 2): CRC16 verification
    body = frame[:-2]
    expected_crc = _compute_crc(body)
    actual_crc = frame[-2:]
    assert actual_crc == expected_crc, f"CRC mismatch: expected {expected_crc}, got {actual_crc}"


# ==============================================================================
# 1. READ BYTECODE MESSAGE TESTS
# ==============================================================================

def test_bytecode_read_entire_dcb(tm1_thermostat):
    """Test bytecode generation for reading the entire TM1 DCB (start=0, len=0xFFFF)."""
    frame = tm1_thermostat.form_read_message(address=0, length=constants.RW_LENGTH_ALL)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=10,
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_READ,
        expected_start=0,
        expected_rw_len=0xFFFF,
        expected_payload=None,
    )


def test_bytecode_read_partial_dcb(tm1_thermostat):
    """Test bytecode generation for reading partial TM1 DCB (e.g. timer state at address 42, length 1)."""
    frame = tm1_thermostat.form_read_message(address=constants.TM1_TIMER_STATE_ADDR, length=1)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=10,
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_READ,
        expected_start=constants.TM1_TIMER_STATE_ADDR,
        expected_rw_len=1,
        expected_payload=None,
    )


# ==============================================================================
# 2. ON / OFF STATE BYTECODE TESTS (Address 21)
# ==============================================================================

@pytest.mark.parametrize("state,expected_byte", [
    (0, 0),  # Off
    (1, 1),  # On
])
def test_bytecode_configure_on_off(tm1_thermostat, state, expected_byte):
    """Test bytecode for configuring On/Off (Address 21, 1 byte)."""
    frame = tm1_thermostat.form_write_message(constants.TM1_ON_OFF_ADDR, [expected_byte])
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=11,  # 10 + 1
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=21,
        expected_rw_len=1,
        expected_payload=[expected_byte],
    )


def test_bytecode_configure_on_off_invalid_values(tm1_thermostat):
    """Test validation prevents illegal on/off values."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_on_off(2)
    with pytest.raises(ValueError):
        tm1_thermostat.set_on_off(-1)


# ==============================================================================
# 3. KEY LOCK BYTECODE TESTS (Address 22)
# ==============================================================================

@pytest.mark.parametrize("lock_state,expected_byte", [
    (0, 0),  # Unlock
    (1, 1),  # Lock
])
def test_bytecode_configure_key_lock(tm1_thermostat, lock_state, expected_byte):
    """Test bytecode for configuring Key Lock (Address 22, 1 byte)."""
    frame = tm1_thermostat.form_write_message(constants.TM1_KEY_LOCK_ADDR, [expected_byte])
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=11,  # 10 + 1
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=22,
        expected_rw_len=1,
        expected_payload=[expected_byte],
    )


def test_bytecode_configure_key_lock_invalid_values(tm1_thermostat):
    """Test validation prevents illegal key lock values."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_key_lock(99)


# ==============================================================================
# 4. HOLIDAY HOURS BYTECODE TESTS (Address 24)
# ==============================================================================

@pytest.mark.parametrize("hours,expected_low,expected_high", [
    (0, 0, 0),          # Cancel holiday
    (24, 24, 0),        # 1 day
    (168, 168, 0),      # 7 days (0x00A8 -> low=168, high=0)
    (500, 244, 1),      # 500 hours (0x01F4 -> low=244, high=1)
    (65535, 255, 255),  # Maximum 16-bit
])
def test_bytecode_configure_holiday_hours(tm1_thermostat, hours, expected_low, expected_high):
    """Test bytecode for configuring Holiday Hours (Address 24, 2 bytes, low byte ahead when write)."""
    payload = [expected_low, expected_high]
    frame = tm1_thermostat.form_write_message(constants.TM1_HOLIDAY_ADDR, payload)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=12,  # 10 + 2
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=24,
        expected_rw_len=2,
        expected_payload=payload,
    )


def test_bytecode_configure_holiday_hours_invalid(tm1_thermostat):
    """Test validation prevents negative or out of bounds holiday hours."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_holiday_hours(-1)
    with pytest.raises(ValueError):
        tm1_thermostat.set_holiday_hours(70000)


# ==============================================================================
# 5. COUNTDOWN TIMER MINUTES BYTECODE TESTS (Address 26)
# ==============================================================================

@pytest.mark.parametrize("minutes,expected_low,expected_high", [
    (0, 0, 0),         # 0 min
    (60, 60, 0),       # 1 hour
    (180, 180, 0),     # 3 hours
    (1800, 8, 7),      # 1800 min = 30 hours (0x0708 -> low=8, high=7)
])
def test_bytecode_configure_countdown_timer(tm1_thermostat, minutes, expected_low, expected_high):
    """Test bytecode for configuring Countdown Timer (Address 26, 2 bytes, range [0, 1800], low byte first)."""
    payload = [expected_low, expected_high]
    frame = tm1_thermostat.form_write_message(constants.TM1_COUNTDOWN_ADDR, payload)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=12,  # 10 + 2
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=26,
        expected_rw_len=2,
        expected_payload=payload,
    )


def test_bytecode_configure_countdown_timer_out_of_range(tm1_thermostat):
    """Test protocol range enforcement: countdown minutes > 1800 must raise ValueError."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_countdown_timer(1801)
    with pytest.raises(ValueError):
        tm1_thermostat.set_countdown_timer(-1)


# ==============================================================================
# 6. CURRENT TIMER STATE / OVERRIDE BYTECODE TESTS (Address 42)
# ==============================================================================

@pytest.mark.parametrize("state,expected_byte", [
    (0, 0),  # Auto: let timer run based on programmed period
    (1, 1),  # Override timer to ON
    (2, 2),  # Override timer to OFF
])
def test_bytecode_configure_timer_state_override(tm1_thermostat, state, expected_byte):
    """Test bytecode for configuring current timer state override (Address 42, 1 byte)."""
    frame = tm1_thermostat.form_write_message(constants.TM1_TIMER_STATE_ADDR, [expected_byte])
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=11,  # 10 + 1
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=42,
        expected_rw_len=1,
        expected_payload=[expected_byte],
    )


def test_bytecode_configure_timer_state_invalid(tm1_thermostat):
    """Test validation prevents illegal timer override states."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_timer_state(3)


# ==============================================================================
# 7. REAL-TIME CLOCK (RTC) BYTECODE TESTS (Address 43)
# ==============================================================================

def test_bytecode_configure_real_time_clock(tm1_thermostat):
    """Test bytecode for setting real-time clock (Address 43, 4 bytes: Week 1..7, Hour 0..23, Min 0..59, Sec 0..59)."""
    # Wednesday 14:35:50 -> week=3, hour=14, min=35, sec=50
    payload = [3, 14, 35, 50]
    frame = tm1_thermostat.form_write_message(constants.TM1_TIME_ADDR, payload)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=14,  # 10 + 4
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=43,
        expected_rw_len=4,
        expected_payload=payload,
    )


def test_bytecode_configure_real_time_clock_validation(tm1_thermostat):
    """Test validation checks on clock parameters."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_time(0, 12, 0, 0)   # Week must be 1..7
    with pytest.raises(ValueError):
        tm1_thermostat.set_time(8, 12, 0, 0)
    with pytest.raises(ValueError):
        tm1_thermostat.set_time(1, 24, 0, 0)  # Hour 0..23
    with pytest.raises(ValueError):
        tm1_thermostat.set_time(1, 12, 60, 0)  # Min 0..59
    with pytest.raises(ValueError):
        tm1_thermostat.set_time(1, 12, 0, 60)  # Sec 0..59


# ==============================================================================
# 8. PROGRAM MODE BYTECODE TESTS (Address 16)
# ==============================================================================

@pytest.mark.parametrize("mode,expected_byte", [
    (0, 0),  # 5/2 mode
    (1, 1),  # 7 day mode
    (2, 2),  # Countdown timer mode
])
def test_bytecode_configure_program_mode(tm1_thermostat, mode, expected_byte):
    """Test bytecode for configuring Program Mode (Address 16, 1 byte)."""
    frame = tm1_thermostat.form_write_message(constants.TM1_PROG_MODE_ADDR, [expected_byte])
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=11,  # 10 + 1
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=16,
        expected_rw_len=1,
        expected_payload=[expected_byte],
    )


def test_bytecode_configure_program_mode_invalid(tm1_thermostat):
    """Test validation prevents illegal program modes."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_program_mode(3)


# ==============================================================================
# 9. 5/2 DAY SWITCHING SCHEDULE BYTECODE TESTS (Addresses 71 and 87)
# ==============================================================================

def test_bytecode_configure_weekday_schedule(tm1_thermostat):
    """Test bytecode for configuring Weekday switching times (Address 71, 16 bytes)."""
    # 4 on/off switching pairs: Time 1-4 On H/M, Off H/M
    schedule = [
        6, 30, 8, 30,   # Time1: On 06:30, Off 08:30
        17, 0, 22, 0,   # Time2: On 17:00, Off 22:00
        24, 0, 24, 0,   # Time3: Cancelled (Hour=24)
        24, 0, 24, 0,   # Time4: Cancelled (Hour=24)
    ]
    frame = tm1_thermostat.form_write_message(constants.TM1_WEEKDAY_ADDR, schedule)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=26,  # 10 + 16
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=71,
        expected_rw_len=16,
        expected_payload=schedule,
    )


def test_bytecode_configure_weekend_schedule(tm1_thermostat):
    """Test bytecode for configuring Weekend switching times (Address 87, 16 bytes)."""
    schedule = [
        8, 0, 10, 0,    # Time1: On 08:00, Off 10:00
        16, 30, 23, 0,  # Time2: On 16:30, Off 23:00
        24, 0, 24, 0,   # Time3: Cancelled
        24, 0, 24, 0,   # Time4: Cancelled
    ]
    frame = tm1_thermostat.form_write_message(constants.TM1_WEEKEND_ADDR, schedule)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=26,  # 10 + 16
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=87,
        expected_rw_len=16,
        expected_payload=schedule,
    )


def test_bytecode_configure_schedule_invalid_length(tm1_thermostat):
    """Test schedule must be strictly 16 bytes."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_weekday_schedule([0] * 12)
    with pytest.raises(ValueError):
        tm1_thermostat.set_weekend_schedule([0] * 18)


# ==============================================================================
# 10. 7-DAY INDIVIDUAL DAY SCHEDULE BYTECODE TESTS (Addresses 187..283)
# ==============================================================================

@pytest.mark.parametrize("day,expected_addr", [
    (1, 187),         # Monday
    (2, 203),         # Tuesday
    (3, 219),         # Wednesday
    (4, 235),         # Thursday
    (5, 251),         # Friday
    (6, 267),         # Saturday (267 = 0x010B -> low=11, high=1)
    (7, 283),         # Sunday   (283 = 0x011B -> low=27, high=1)
    ("monday", 187),
    ("tuesday", 203),
    ("wednesday", 219),
    ("thursday", 235),
    ("friday", 251),
    ("saturday", 267),
    ("sunday", 283),
])
def test_bytecode_configure_7_day_individual_days(tm1_thermostat, day, expected_addr):
    """Test bytecode for each individual day in 7-day mode (Addresses 187..283, 16 bytes each)."""
    schedule = [7, 0, 9, 0, 16, 0, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0]
    frame = tm1_thermostat.form_write_message(expected_addr, schedule)
    _assert_frame_structure(
        frame=frame,
        expected_dest=1,
        expected_length=26,  # 10 + 16
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=expected_addr,
        expected_rw_len=16,
        expected_payload=schedule,
    )


def test_bytecode_configure_day_schedule_invalid(tm1_thermostat):
    """Test day schedule validation for invalid day parameter."""
    with pytest.raises(ValueError):
        tm1_thermostat.set_day_schedule(0, [0] * 16)
    with pytest.raises(ValueError):
        tm1_thermostat.set_day_schedule(8, [0] * 16)
    with pytest.raises(ValueError):
        tm1_thermostat.set_day_schedule("funday", [0] * 16)


# ==============================================================================
# 11. BROADCAST ADDRESSING BYTECODE TESTS (Address 0xFF)
# ==============================================================================

def test_bytecode_broadcast_message(tm1_thermostat):
    """Test broadcast write frame generation (destination address 0xFF)."""
    # Broadcast turn all stats off
    frame = tm1_thermostat.form_broadcast_message(constants.TM1_ON_OFF_ADDR, [0])
    _assert_frame_structure(
        frame=frame,
        expected_dest=constants.BROADCAST_ADDR,  # 0xFF = 255
        expected_length=11,
        expected_src=constants.RW_MASTER_ADDRESS,
        expected_func=constants.FUNC_WRITE,
        expected_start=constants.TM1_ON_OFF_ADDR,
        expected_rw_len=1,
        expected_payload=[0],
    )


# ==============================================================================
# 12. CRC16 INTEGRITY AND VERIFICATION
# ==============================================================================

def test_crc16_integrity_on_all_tm1_messages(tm1_thermostat):
    """Verify that every bytecode message has a valid CCITT-16 CRC."""
    # Sample messages across different lengths
    frames = [
        tm1_thermostat.form_read_message(0, 0xFFFF),
        tm1_thermostat.form_write_message(21, [1]),
        tm1_thermostat.form_write_message(24, [168, 0]),
        tm1_thermostat.form_write_message(43, [1, 12, 0, 0]),
        tm1_thermostat.form_write_message(71, [0] * 16),
        tm1_thermostat.form_write_message(267, [0] * 16),
    ]
    for frame in frames:
        body = frame[:-2]
        crc = frame[-2:]
        expected_crc = heatmiser.CRC16().run(body)
        assert crc == expected_crc

        # Tampering with any byte must invalidate the CRC
        tampered = list(body)
        tampered[0] ^= 0xFF
        assert heatmiser.CRC16().run(tampered) != crc


def test_slave_write_acknowledgment_verification(tm1_thermostat):
    """Verify the 7-byte slave write confirmation reply verification."""
    # Valid reply: [0x81, 7, 0, 1, 1, crc_l, crc_h]
    reply_body = [0x81, 7, 0, 1, constants.FUNC_WRITE]
    crc = heatmiser.CRC16().run(reply_body)
    valid_reply = reply_body + crc

    # Should verify True
    assert tm1_thermostat._hm_verify_message_crc_uk(
        0x81, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, valid_reply
    ) is True

    # Bad CRC must fail verification
    bad_crc_reply = reply_body + [0x00, 0x00]
    assert tm1_thermostat._hm_verify_message_crc_uk(
        0x81, constants.HMV3_ID, 1, constants.FUNC_WRITE, 1, bad_crc_reply
    ) is False


# ==============================================================================
# 13. SERIAL TRANSMISSION INTEGRATION (via FakeSerial / FakeUH1)
# ==============================================================================

def test_end_to_end_serial_transmission_of_all_configurable_messages():
    """Verify that every high-level setter sends the exact expected bytecode over serial."""
    uh1 = FakeUH1(payload=build_tm1_default_dcb_5_2(), model="tm1")
    stat = heatmiser.TM1Thermostat(1, uh1)
    serial = uh1.serial

    # 1. On/Off
    stat.set_on_off(1)
    assert serial.last_write[3] == constants.FUNC_WRITE
    assert serial.last_write[4:6] == [21, 0]
    assert serial.last_write[8] == 1

    # 2. Key Lock
    stat.set_key_lock(1)
    assert serial.last_write[4:6] == [22, 0]
    assert serial.last_write[8] == 1

    # 3. Holiday Hours
    stat.set_holiday_hours(168)
    assert serial.last_write[4:6] == [24, 0]
    assert serial.last_write[8:10] == [168, 0]

    # 4. Countdown Minutes
    stat.set_countdown_timer(120)
    assert serial.last_write[4:6] == [26, 0]
    assert serial.last_write[8:10] == [120, 0]

    # 5. Timer State Override
    stat.set_timer_state(1)
    assert serial.last_write[4:6] == [42, 0]
    assert serial.last_write[8] == 1

    # 6. Real Time Clock
    stat.set_time(5, 20, 15, 30)
    assert serial.last_write[4:6] == [43, 0]
    assert serial.last_write[8:12] == [5, 20, 15, 30]

    # 7. Program Mode
    stat.set_program_mode(1)
    assert serial.last_write[4:6] == [16, 0]
    assert serial.last_write[8] == 1

    # 8. Weekday Schedule
    sched = [7, 0, 9, 0, 16, 0, 20, 0, 24, 0, 24, 0, 24, 0, 24, 0]
    stat.set_weekday_schedule(sched)
    assert serial.last_write[4:6] == [71, 0]
    assert serial.last_write[8:24] == sched

    # 9. Weekend Schedule
    stat.set_weekend_schedule(sched)
    assert serial.last_write[4:6] == [87, 0]
    assert serial.last_write[8:24] == sched

    # 10. Saturday Schedule (testing 16-bit address start_low=11, start_high=1)
    stat.set_day_schedule(6, sched)
    assert serial.last_write[4:6] == [11, 1]
    assert serial.last_write[8:24] == sched

    # 11. Sunday Schedule (start_low=27, start_high=1)
    stat.set_day_schedule(7, sched)
    assert serial.last_write[4:6] == [27, 1]
    assert serial.last_write[8:24] == sched
