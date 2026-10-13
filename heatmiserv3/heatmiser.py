#
# Neil Trimboy 2011
# Assume Python 2.7.x +
#
import logging
import sys
import time
import serial
import yaml
from . import constants

try:
    from importlib.resources import files as resource_files
except ImportError:
    from importlib_resources import files as resource_files

config_yml = resource_files('heatmiserv3').joinpath('config.yml')

logger = logging.getLogger(__name__)

#
# Believe this is known as CCITT (0xFFFF)
# This is the CRC function converted directly from the Heatmiser C code
# provided in their API


class CRC16:
    """This is the CRC hashing mechanism used by the V3 protocol."""

    LookupHigh = [
        0x00,
        0x10,
        0x20,
        0x30,
        0x40,
        0x50,
        0x60,
        0x70,
        0x81,
        0x91,
        0xA1,
        0xB1,
        0xC1,
        0xD1,
        0xE1,
        0xF1,
    ]
    LookupLow = [
        0x00,
        0x21,
        0x42,
        0x63,
        0x84,
        0xA5,
        0xC6,
        0xE7,
        0x08,
        0x29,
        0x4A,
        0x6B,
        0x8C,
        0xAD,
        0xCE,
        0xEF,
    ]

    def __init__(self):
        self.high = constants.BYTEMASK
        self.low = constants.BYTEMASK

    def extract_bits(self, val):
        """Extras the 4 bits, XORS the message data, and does table lookups."""
        # Step one, extract the Most significant 4 bits of the CRC register
        thisval = self.high >> 4
        # XOR in the Message Data into the extracted bits
        thisval = thisval ^ val
        # Shift the CRC Register left 4 bits
        self.high = (self.high << 4) | (self.low >> 4)
        self.high = self.high & constants.BYTEMASK  # force char
        self.low = self.low << 4
        self.low = self.low & constants.BYTEMASK  # force char
        # Do the table lookups and XOR the result into the CRC tables
        self.high = self.high ^ self.LookupHigh[thisval]
        self.high = self.high & constants.BYTEMASK  # force char
        self.low = self.low ^ self.LookupLow[thisval]
        self.low = self.low & constants.BYTEMASK  # force char

    def update(self, val):
        """Updates the CRC value using bitwise operations."""
        self.extract_bits(val >> 4)  # High nibble first
        self.extract_bits(val & 0x0F)  # Low nibble

    def run(self, message):
        """Calculates a CRC"""
        for value in message:
            self.update(value)
        return [self.low, self.high]


class HeatmiserThermostat:
    """Initialises a heatmiser thermostat, by taking an address and model."""

    def __init__(self, address, model, uh1, cache_ttl=None):
        self.address = address
        self.model = model
        self.uh1 = uh1
        self.cache_ttl = (
            float(cache_ttl)
            if cache_ttl is not None
            else constants.DEFAULT_CACHE_TTL
        )
        self._dcb_cache = None
        self._dcb_timestamp = 0.0
        try:
            with open(config_yml) as config_file:
                cfg = yaml.safe_load(config_file)
                self.config = cfg[model] if model in cfg else cfg[model.lower()]
        except yaml.YAMLError as exc:
            logger.info("The YAML file is invalid: %s", exc)
        self.conn = uh1.registerThermostat(self)
        self.dcb = ""
        self.read_dcb()

    def _hm_form_message(
        self, thermostat_id, protocol, source, function, start, payload
    ):
        """Forms a message payload, excluding CRC"""
        if protocol == constants.HMV3_ID:
            start_low = start & constants.BYTEMASK
            start_high = (start >> 8) & constants.BYTEMASK
            if function == constants.FUNC_READ:
                payload_length = 0
                length_low = constants.RW_LENGTH_ALL & constants.BYTEMASK
                length_high = (constants.RW_LENGTH_ALL >> 8) & constants.BYTEMASK
            else:
                payload_length = len(payload)
                length_low = payload_length & constants.BYTEMASK
                length_high = (payload_length >> 8) & constants.BYTEMASK
            msg = [
                thermostat_id,
                10 + payload_length,
                source,
                function,
                start_low,
                start_high,
                length_low,
                length_high,
            ]
            if function == constants.FUNC_WRITE:
                msg = msg + payload
                type(msg)
            return msg
        else:
            assert 0, "Un-supported protocol found %s" % protocol

    def _hm_form_message_crc(
        self, thermostat_id, protocol, source, function, start, payload
    ):
        """Forms a message payload, including CRC"""
        data = self._hm_form_message(
            thermostat_id, protocol, source, function, start, payload
        )
        crc = CRC16()
        data = data + crc.run(data)
        return data

    def _hm_verify_message_crc_uk(
        self, thermostat_id, protocol, source, expectedFunction, expectedLength, datal
    ):
        """Verifies message appears legal"""
        # expectedLength only used for read msgs as always 7 for write
        assert expectedLength == expectedLength
        badresponse = 0
        if protocol == constants.HMV3_ID:
            if len(datal) < 7:
                logger.error("Response is too short to contain a valid frame")
                return False
            checksum = datal[len(datal) - 2:]
            rxmsg = datal[: len(datal) - 2]
            crc = CRC16()  # Initialises the CRC
            expectedchecksum = crc.run(rxmsg)
            if expectedchecksum == checksum:
                logger.info("CRC is correct")
            else:
                logger.error("CRC is INCORRECT")
                serror = "Incorrect CRC"
                sys.stderr.write(serror)
                badresponse += 1
            dest_addr = datal[0]
            frame_len_l = datal[1]
            frame_len_h = datal[2]
            frame_len = (frame_len_h << 8) | frame_len_l
            source_addr = datal[3]
            func_code = datal[4]

            if dest_addr != 129 and dest_addr != 160:
                logger.info("dest_addr is ILLEGAL")
                serror = "Illegal Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if dest_addr != thermostat_id:
                logger.info("dest_addr is INCORRECT")
                serror = "Incorrect Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if source_addr < 1 or source_addr > 32:
                logger.info("source_addr is ILLEGAL")
                serror = "Illegal Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if source_addr != source:
                logger.info("source addr is INCORRECT")
                serror = "Incorrect Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code != constants.FUNC_WRITE and func_code != constants.FUNC_READ:
                logger.info("Func Code is UNKNWON")
                serror = "Unknown Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code != expectedFunction:
                logger.info("Func Code is UNEXPECTED")
                serror = "Unexpected Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code == constants.FUNC_WRITE and frame_len != 7:
                # Reply to Write is always 7 long
                logger.info("response length is INCORRECT")
                serror = "Incorrect length: %s\n" % (frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            if len(datal) != frame_len:
                logger.info("response length MISMATCHES header")
                serror = "Mismatch length: %s %s\n" % (len(datal), frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            return badresponse == 0

        else:
            assert 0, "Un-supported protocol found %s" % protocol

    def _hm_send_msg(self, message):
        """This is the only interface to the serial connection."""
        if hasattr(self, "uh1") and self.uh1 is not None and hasattr(self.uh1, "transact"):
            try:
                return self.uh1.transact(message, 159)
            except Exception as e:
                logger.error("UH1 transaction error: %s", e)
                return []

        try:
            serial_message = message
            self.conn.write(serial_message)  # Write a string
        except serial.SerialTimeoutException:
            serror = "Write timeout error: \n"
            sys.stderr.write(serror)
        # Now wait for reply
        byteread = b""
        try:
            byteread = self.conn.read(159)
        except (serial.serialutil.SerialException, AttributeError):
            logger.error("Connection failed, attempting reconnect")
            if hasattr(self, "uh1") and self.uh1 is not None and hasattr(self.uh1, "reopen"):
                self.uh1.reopen(force=True)
        # NB max return is 75 in 5/2 mode or 159 in 7day mode
        datal = list(byteread) if byteread else []
        return datal

    def _hm_send_address(self, thermostat_id, address, state, readwrite):
        protocol = constants.HMV3_ID
        if protocol == constants.HMV3_ID:
            if isinstance(state, (list, tuple, bytes)):
                payload = list(state)
            else:
                payload = [state]
            msg = self._hm_form_message_crc(
                thermostat_id,
                protocol,
                constants.RW_MASTER_ADDRESS,
                readwrite,
                address,
                payload,
            )
        else:
            assert 0, "Un-supported protocol found %s" % protocol
        string = bytes(msg)
        datal = self._hm_send_msg(string)
        pro = protocol
        if readwrite == 1:
            self.invalidate_cache()
            verification = self._hm_verify_message_crc_uk(
                0x81, pro, thermostat_id, readwrite, 1, datal
            )
            if verification is False:
                logger.info("OH DEAR BAD RESPONSE")
            return datal
        else:
            verification = self._hm_verify_message_crc_uk(
                0x81, pro, thermostat_id, readwrite, len(datal), datal
            )
            if verification is False:
                logger.info("OH DEAR BAD RESPONSE")
            return datal

    def invalidate_cache(self):
        """Invalidates the cached DCB telemetry."""
        self._dcb_cache = None
        self._dcb_timestamp = 0.0

    def set_cache_ttl(self, ttl_seconds):
        """Sets the DCB cache TTL in seconds (0 to disable caching)."""
        if ttl_seconds < 0:
            raise ValueError("cache_ttl must be non-negative")
        self.cache_ttl = float(ttl_seconds)

    def _hm_read_address(self, force=False):
        """Reads from the DCB and maps to yaml config file."""
        now = time.monotonic()
        if (
            not force
            and self._dcb_cache is not None
            and (now - self._dcb_timestamp) < self.cache_ttl
        ):
            return self._dcb_cache

        response = self._hm_send_address(self.address, 0, 0, 0)
        lookup = self.config["keys"]
        offset = self.config["offset"]
        keydata = {}
        for i in lookup:
            try:
                kdata = lookup[i]
                ddata = response[i + offset]
                keydata[i] = {"label": kdata, "value": ddata}
            except IndexError:
                logger.info("Finished processing at %d", i)
        self._dcb_cache = keydata
        self._dcb_timestamp = now
        self.dcb = keydata
        return keydata

    def read_dcb(self, force=False):
        """
        Returns the full DCB. If cached and valid within cache_ttl,
        returns cached data. Set force=True to query fresh wire telemetry.
        """
        logger.info("Getting latest data from DCB....")
        self.dcb = self._hm_read_address(force=force)
        return self.dcb

    def get_frost_temp(self):
        """
        Returns the temperature
        """
        return self._hm_read_address()[17]["value"]

    def get_target_temp(self):
        """
        Returns the temperature
        """
        return self._hm_read_address()[18]["value"]

    def get_floormax_temp(self):
        """
        Returns the temperature
        """
        return self._hm_read_address()[19]["value"]

    def get_status(self):
        return self._hm_read_address()[21]["value"]

    def get_heating(self):
        return self._hm_read_address()[23]["value"]

    def get_thermostat_id(self):
        return self.dcb[11]["value"]

    def get_temperature_format(self):
        temp_format = self.dcb[5]["value"]
        if temp_format == 0:
            return "C"
        else:
            return "F"

    def get_sensor_selection(self):
        sensor = self.dcb[13]["value"]
        answers = {
            0: "Built in air sensor",
            1: "Remote air sensor",
            2: "Floor sensor",
            3: "Built in + floor",
            4: "Remote + floor",
        }
        return answers[sensor]

    def get_program_mode(self):
        mode = self.dcb[16]["value"]
        modes = {0: "5/2 mode", 1: "7 day mode"}
        return modes[mode]

    def get_frost_protection(self) -> bool:
        """
        Return whether frost protection mode is enabled.
        This is represented by the snowflake icon and is
        the same as on/off
        """
        return self._hm_read_address()[23]["value"] == 1

    def get_floor_temp(self):
        return (
            (self.dcb[31]["value"] / 10)
            if (int(self.dcb[13]["value"]) > 1)
            else (self.dcb[33]["value"] / 10)
        )

    def get_sensor_error(self):
        return self.dcb[34]["value"]

    def get_current_state(self):
        return self.dcb[35]["value"]

    def set_frost_protect_mode(self, onoff):
        self._hm_send_address(self.address, 23, onoff, 1)
        return True

    def set_frost_protect_temp(self, frost_temp):
        if not (7 <= frost_temp <= 17):
            logger.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 17, frost_temp, 1)
            return True

    def set_target_temp(self, temperature):
        """
        Sets the target temperature, to the requested int
        """
        if not (5 <= temperature <= 35):
            logger.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 18, temperature, 1)
            return True

    def set_floormax_temp(self, floor_max):
        if not (20 <= floor_max <= 45):
            logger.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 19, floor_max, 1)
            return True

    #
    # General Device & Operating Mode
    #
    def set_on_off(self, state):
        """
        Sets On/Off run state (Address 21).
        0 = Off (Frost protection active)
        1 = On (Normal operation)
        """
        if state not in (0, 1) and not isinstance(state, bool):
            logger.info("Invalid on/off state %s; must be 0 (off) or 1 (on)", state)
            return False
        val = 1 if state else 0
        self._hm_send_address(self.address, constants.ON_OFF_ADDR, val, constants.FUNC_WRITE)
        return True

    def get_on_off(self):
        """Returns on/off state (0 = Off, 1 = On)."""
        return self.dcb[21]["value"]

    def set_key_lock(self, lock):
        """
        Sets Keypad Lock state (Address 22).
        0 = Unlocked, 1 = Locked
        """
        if lock not in (0, 1) and not isinstance(lock, bool):
            logger.info("Invalid key lock state %s; must be 0 (unlocked) or 1 (locked)", lock)
            return False
        val = 1 if lock else 0
        self._hm_send_address(self.address, constants.KEY_LOCK_ADDR, val, constants.FUNC_WRITE)
        return True

    def get_key_lock(self):
        """Returns keypad lock state (0 = Unlocked, 1 = Locked)."""
        return self.dcb[22]["value"]

    #
    # Temperature & Regulation Settings
    #
    def set_temperature_format(self, temp_format):
        """
        Sets temperature format (Address 5).
        0 or "C" = Celsius
        1 or "F" = Fahrenheit
        """
        if isinstance(temp_format, str):
            tf_upper = temp_format.strip().upper()
            if tf_upper in ("C", "CELSIUS"):
                val = constants.TEMP_FORMAT_CELSIUS
            elif tf_upper in ("F", "FAHRENHEIT"):
                val = constants.TEMP_FORMAT_FAHRENHEIT
            else:
                logger.info("Invalid temperature format: %s", temp_format)
                return False
        elif temp_format in (0, 1) and not isinstance(temp_format, bool):
            val = temp_format
        else:
            logger.info("Invalid temperature format: %s", temp_format)
            return False
        self._hm_send_address(self.address, constants.TEMP_FORMAT_ADDR, val, constants.FUNC_WRITE)
        return True

    def set_differential(self, diff):
        """
        Sets switching differential (Address 6).
        Allowed range: 1 to 3 °C.
        """
        if isinstance(diff, bool) or not (1 <= diff <= 3):
            logger.info("Switching differential %s out of allowed range [1, 3]", diff)
            return False
        self._hm_send_address(self.address, constants.SWITCH_DIFF_ADDR, int(diff), constants.FUNC_WRITE)
        return True

    def get_differential(self):
        """Returns switching differential in °C (1..3)."""
        return self.dcb[6]["value"]

    #
    # Sensor Selection
    #
    def set_sensor_selection(self, sensor_mode):
        """
        Sets temperature sensor selection mode (Address 13).
        0 = Built-in air sensor
        1 = Remote air sensor
        2 = Floor sensor only
        3 = Built-in air + Floor sensor
        4 = Remote air + Floor sensor
        """
        mode_map = {
            "built in": 0,
            "built-in": 0,
            "built in air": 0,
            "built-in air": 0,
            "built in air sensor": 0,
            "remote air": 1,
            "remote": 1,
            "remote air sensor": 1,
            "floor": 2,
            "floor only": 2,
            "floor sensor": 2,
            "built-in+floor": 3,
            "built in + floor": 3,
            "remote+floor": 4,
            "remote + floor": 4,
        }
        if isinstance(sensor_mode, str):
            cleaned = sensor_mode.strip().lower()
            if cleaned not in mode_map:
                logger.info("Invalid sensor mode string: %s", sensor_mode)
                return False
            mode_val = mode_map[cleaned]
        elif isinstance(sensor_mode, int) and not isinstance(sensor_mode, bool) and 0 <= sensor_mode <= 4:
            mode_val = sensor_mode
        else:
            logger.info("Invalid sensor mode: %s", sensor_mode)
            return False
        self._hm_send_address(self.address, constants.SENSOR_SELECTION_ADDR, mode_val, constants.FUNC_WRITE)
        return True

    #
    # Timing, Hold & Vacation / Holiday
    #
    def set_holiday_hours(self, hours):
        """
        Sets holiday hours (Address 24).
        Range: 0 to 65535 hours (0 to cancel).
        Transmitted 2 bytes, low byte first on write.
        """
        if isinstance(hours, bool) or not (0 <= hours <= 65535):
            logger.info("Holiday hours %s out of allowed range [0, 65535]", hours)
            return False
        payload = [hours & constants.BYTEMASK, (hours >> 8) & constants.BYTEMASK]
        self._hm_send_address(self.address, constants.HOLIDAY_ADDR, payload, constants.FUNC_WRITE)
        return True

    def get_holiday_hours(self):
        """Returns remaining holiday hours from DCB."""
        return (self.dcb[24]["value"] << 8) | self.dcb[25]["value"]

    def set_temp_hold(self, minutes, temperature=None):
        """
        Sets temperature hold duration in minutes (Address 26) and optional setpoint.
        Range: 0 to 1800 minutes (0 to cancel).
        Transmitted 2 bytes, low byte first on write.
        If temperature is provided, also sets target temperature.
        """
        if isinstance(minutes, bool) or not (0 <= minutes <= 1800):
            logger.info("Hold minutes %s out of allowed range [0, 1800]", minutes)
            return False
        if temperature is not None:
            if isinstance(temperature, bool) or not (5 <= temperature <= 35):
                logger.info("Refusing to set hold temp outside of allowed range [5, 35]")
                return False
            self.set_target_temp(temperature)
        payload = [minutes & constants.BYTEMASK, (minutes >> 8) & constants.BYTEMASK]
        self._hm_send_address(self.address, constants.TEMP_HOLD_ADDR, payload, constants.FUNC_WRITE)
        return True

    def get_temp_hold_minutes(self):
        """Returns remaining temperature hold minutes from DCB."""
        return (self.dcb[26]["value"] << 8) | self.dcb[27]["value"]

    def set_time(self, week, hour, minute, second):
        """
        Sets real-time clock (RTC) (Address 43).
        week: 1..7 (1=Monday .. 7=Sunday)
        hour: 0..23, minute: 0..59, second: 0..59
        """
        for v in (week, hour, minute, second):
            if isinstance(v, bool):
                return False
        if not (1 <= week <= 7 and 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            logger.info("Invalid time/date values: week=%s, hr=%s, min=%s, sec=%s", week, hour, minute, second)
            return False
        payload = [week, hour, minute, second]
        self._hm_send_address(self.address, constants.CUR_TIME_ADDR, payload, constants.FUNC_WRITE)
        return True

    def get_time(self):
        """Returns real-time clock dictionary from DCB."""
        return {
            "week": self.dcb[36]["value"],
            "hour": self.dcb[37]["value"],
            "min": self.dcb[38]["value"],
            "sec": self.dcb[39]["value"],
        }


class TM1Thermostat(HeatmiserThermostat):
    """
    Representation of a Heatmiser TM1 timer thermostat.
    Based on Section 3.5 of Heatmiser V3 System Protocol 3.9.
    """

    def __init__(self, address, uh1, model="tm1", cache_ttl=None):
        super(TM1Thermostat, self).__init__(address, model, uh1, cache_ttl=cache_ttl)

    def form_write_message(self, address, payload):
        """Forms a write bytecode frame including CRC."""
        if not isinstance(payload, (list, tuple, bytes)):
            payload = [payload]
        return self._hm_form_message_crc(
            self.address,
            constants.HMV3_ID,
            constants.RW_MASTER_ADDRESS,
            constants.FUNC_WRITE,
            address,
            list(payload),
        )

    def form_read_message(self, address=0, length=constants.RW_LENGTH_ALL):
        """Forms a read bytecode frame including CRC."""
        msg = self._hm_form_message(
            self.address,
            constants.HMV3_ID,
            constants.RW_MASTER_ADDRESS,
            constants.FUNC_READ,
            address,
            [],
        )
        if length != constants.RW_LENGTH_ALL:
            msg[6] = length & constants.BYTEMASK
            msg[7] = (length >> 8) & constants.BYTEMASK
        crc = CRC16()
        return msg + crc.run(msg)

    def form_broadcast_message(self, address, payload):
        """Forms a broadcast write bytecode frame (destination=0xFF)."""
        if not isinstance(payload, (list, tuple, bytes)):
            payload = [payload]
        return self._hm_form_message_crc(
            constants.BROADCAST_ADDR,
            constants.HMV3_ID,
            constants.RW_MASTER_ADDRESS,
            constants.FUNC_WRITE,
            address,
            list(payload),
        )

    #
    # Configurable setters (bytecode command senders)
    #
    def set_on_off(self, state):
        """
        Sets On/Off state (Unique address 21).
        0 = Off, 1 = On
        """
        if state not in (0, 1):
            raise ValueError(f"Invalid on/off state {state}; must be 0 (off) or 1 (on)")
        return self._hm_send_address(self.address, constants.TM1_ON_OFF_ADDR, state, constants.FUNC_WRITE)

    def set_key_lock(self, lock):
        """
        Sets Key lock state (Unique address 22).
        0 = Unlock, 1 = Lock
        """
        if lock not in (0, 1):
            raise ValueError(f"Invalid key lock state {lock}; must be 0 (unlock) or 1 (lock)")
        return self._hm_send_address(self.address, constants.TM1_KEY_LOCK_ADDR, lock, constants.FUNC_WRITE)

    def set_holiday_hours(self, hours):
        """
        Sets Holiday hours (Unique address 24).
        2 bytes: low 8-bit ahead when write. Write 0 to cancel.
        """
        if not (0 <= hours <= 65535):
            raise ValueError(f"Holiday hours {hours} out of range [0, 65535]")
        payload = [hours & constants.BYTEMASK, (hours >> 8) & constants.BYTEMASK]
        return self._hm_send_address(self.address, constants.TM1_HOLIDAY_ADDR, payload, constants.FUNC_WRITE)

    def set_countdown_timer(self, minutes):
        """
        Sets Countdown timer minutes (Unique address 26).
        Range: [0, 1800] minutes.
        2 bytes: low 8-bit ahead when write.
        """
        if not (0 <= minutes <= 1800):
            raise ValueError(f"Countdown minutes {minutes} out of range [0, 1800]")
        payload = [minutes & constants.BYTEMASK, (minutes >> 8) & constants.BYTEMASK]
        return self._hm_send_address(self.address, constants.TM1_COUNTDOWN_ADDR, payload, constants.FUNC_WRITE)

    def set_timer_state(self, state):
        """
        Sets current timer state / override (Unique address 42).
        0 = let timer run based on programmed period (auto)
        1 = override timer to ON
        2 = override timer to OFF
        """
        if state not in (0, 1, 2):
            raise ValueError(f"Invalid timer state {state}; must be 0 (auto), 1 (override on), 2 (override off)")
        return self._hm_send_address(self.address, constants.TM1_TIMER_STATE_ADDR, state, constants.FUNC_WRITE)

    def set_program_mode(self, mode):
        """
        Sets program mode (Unique address 16).
        0 = 5/2 mode
        1 = 7 day mode
        2 = countdown timer mode
        """
        if mode not in (0, 1, 2):
            raise ValueError(f"Invalid program mode {mode}; must be 0 (5/2), 1 (7 day), or 2 (countdown)")
        return self._hm_send_address(self.address, constants.TM1_PROG_MODE_ADDR, mode, constants.FUNC_WRITE)

    def set_time(self, week, hour, minute, second):
        """
        Sets real time clock (RTC) (Unique address 43).
        week: 1..7 (1=Monday .. 7=Sunday)
        hour: 0..23
        minute: 0..59
        second: 0..59
        """
        if not (1 <= week <= 7):
            raise ValueError(f"Weekday {week} out of range [1, 7]")
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour {hour} out of range [0, 23]")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute {minute} out of range [0, 59]")
        if not (0 <= second <= 59):
            raise ValueError(f"Second {second} out of range [0, 59]")
        payload = [week, hour, minute, second]
        return self._hm_send_address(self.address, constants.TM1_TIME_ADDR, payload, constants.FUNC_WRITE)

    def set_weekday_schedule(self, schedule):
        """
        Sets weekday switching times (Unique address 71).
        schedule: list of 16 bytes representing 4 On/Off periods (Time1-4 On H/M, Off H/M).
        """
        if len(schedule) != 16:
            raise ValueError(f"Schedule must be exactly 16 bytes, got {len(schedule)}")
        return self._hm_send_address(self.address, constants.TM1_WEEKDAY_ADDR, list(schedule), constants.FUNC_WRITE)

    def set_weekend_schedule(self, schedule):
        """
        Sets weekend switching times (Unique address 87).
        schedule: list of 16 bytes representing 4 On/Off periods.
        """
        if len(schedule) != 16:
            raise ValueError(f"Schedule must be exactly 16 bytes, got {len(schedule)}")
        return self._hm_send_address(self.address, constants.TM1_WEEKEND_ADDR, list(schedule), constants.FUNC_WRITE)

    def set_day_schedule(self, day, schedule):
        """
        Sets individual day switching times for 7-day mode.
        day: 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat, 7=Sun (or string day name)
        schedule: list of 16 bytes.
        """
        day_map = {
            1: constants.TM1_MON_ADDR,
            2: constants.TM1_TUE_ADDR,
            3: constants.TM1_WED_ADDR,
            4: constants.TM1_THU_ADDR,
            5: constants.TM1_FRI_ADDR,
            6: constants.TM1_SAT_ADDR,
            7: constants.TM1_SUN_ADDR,
            "monday": constants.TM1_MON_ADDR,
            "tuesday": constants.TM1_TUE_ADDR,
            "wednesday": constants.TM1_WED_ADDR,
            "thursday": constants.TM1_THU_ADDR,
            "friday": constants.TM1_FRI_ADDR,
            "saturday": constants.TM1_SAT_ADDR,
            "sunday": constants.TM1_SUN_ADDR,
        }
        addr = day_map.get(day if isinstance(day, int) else str(day).lower())
        if addr is None:
            raise ValueError(f"Invalid day {day}; must be 1..7 or weekday name")
        if len(schedule) != 16:
            raise ValueError(f"Schedule must be exactly 16 bytes, got {len(schedule)}")
        return self._hm_send_address(self.address, addr, list(schedule), constants.FUNC_WRITE)

    #
    # DCB Getters for TM1
    #
    def get_model(self):
        return self.dcb[4]["value"]

    def get_on_off(self):
        return self.dcb[8]["value"]

    def get_key_lock(self):
        return self.dcb[9]["value"]

    def get_holiday_hours(self):
        # Read: high byte ahead at index 10, low byte at index 11
        high = self.dcb[10]["value"]
        low = self.dcb[11]["value"]
        return (high << 8) | low

    def get_countdown_minutes(self):
        # Read: high byte ahead at index 12, low byte at index 13
        high = self.dcb[12]["value"]
        low = self.dcb[13]["value"]
        return (high << 8) | low

    def get_timer_state(self):
        return self.dcb[14]["value"]

    def get_time(self):
        return {
            "week": self.dcb[15]["value"],
            "hour": self.dcb[16]["value"],
            "min": self.dcb[17]["value"],
            "sec": self.dcb[18]["value"],
        }

    def get_program_mode(self):
        mode = self.dcb[6]["value"]
        modes = {
            0: "5/2 mode",
            1: "7 day mode",
            2: "Countdown timer mode",
        }
        return modes.get(mode, "Unknown mode")


class PRTHWThermostat(HeatmiserThermostat):
    """
    Representation of a Heatmiser PRT-HW thermostat.
    Programmable Room Thermostat with independent Hot Water control channel.
    Based on Section 3.4 of Heatmiser V3 System Protocol 3.9.
    """

    def __init__(self, address, uh1, model="prt-hw", cache_ttl=None):
        super(PRTHWThermostat, self).__init__(address, model, uh1, cache_ttl=cache_ttl)

    def set_sensor_selection(self, sensor_mode):
        """
        PRT-HW only supports built-in air sensor (mode 0).
        External and floor sensors are unsupported because terminals are used for hot water.
        """
        allowed = (0, "built in", "built-in", "built in air", "built-in air", "built in air sensor")
        if sensor_mode not in allowed and not (isinstance(sensor_mode, str) and sensor_mode.strip().lower() in allowed):
            logger.info("PRT-HW hardware only supports built-in air sensor (mode 0)")
            return False
        return super(PRTHWThermostat, self).set_sensor_selection(0)

    def set_hot_water_boost(self, state):
        """
        Sets Hot Water boost state (Address 41).
        0 = Auto / Follow schedule
        1 = Boost On
        """
        if state not in (0, 1) and not isinstance(state, bool):
            logger.info("Invalid hot water boost state %s; must be 0 (auto) or 1 (boost)", state)
            return False
        val = 1 if state else 0
        self._hm_send_address(self.address, constants.PRTHW_BOOST_ADDR, val, constants.FUNC_WRITE)
        return True

    def get_hot_water_state(self):
        """
        Returns current hot water state from DCB (index 36).
        0 = Hot water off, 1 = Hot water on.
        """
        return self.dcb[36]["value"]

    def get_heating_state(self):
        """
        Returns current heating state from DCB (index 35).
        0 = Heating off, 1 = Heating on.
        """
        return self.dcb[35]["value"]
