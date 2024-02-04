#
# Neil Trimboy 2011
# Assume Python 2.7.x +
#
import sys
import serial
import yaml
import logging
from . import constants
import importlib_resources
from . import crc16

config_yml = importlib_resources.files('heatmiserv3').joinpath('config.yml').read_bytes()


logging.basicConfig(level=logging.INFO)


class HeatmiserThermostat(object):
    """Initialises a heatmiser thermostat, by taking an address and model."""
    
    def __init__(self, address, model, uh1):
        self.address = address
        self.model = model
        try:
            with open(config_yml) as config_file:
                self.config = yaml.safe_load(config_file)[model]
        except yaml.YAMLError as exc:
            logging.info("The YAML file is invalid: %s", exc)
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
                logging.debug("msg is of type, %s", type(msg))
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
        crc = crc16.CRC16()
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
            checksum = datal[len(datal) - 2:]
            logging.info(f"Checksum value is: {checksum}")
            rxmsg = datal[: len(datal) - 2]
            logging.info(f"RXmsg value is: {rxmsg}")
            crc = crc16.CRC16()  # Initialises the CRC
            expectedchecksum = crc.run(rxmsg)
            logging.debug("Expected CRC: %s", expectedchecksum)
            logging.debug("Actual CRC: %s", checksum)
            if expectedchecksum == checksum:
                logging.info("CRC is correct")
            else:
                logging.error("CRC is INCORRECT")
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
                logging.info("dest_addr is ILLEGAL")
                serror = "Illegal Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if dest_addr != thermostat_id:
                logging.info("dest_addr is INCORRECT")
                serror = "Incorrect Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if source_addr < 1 or source_addr > 32:
                logging.info("source_addr is ILLEGAL")
                serror = "Illegal Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if source_addr != source:
                logging.info("source addr is INCORRECT")
                serror = "Incorrect Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code != constants.FUNC_WRITE and func_code != constants.FUNC_READ:
                logging.info("Func Code is UNKNWON")
                serror = "Unknown Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code != expectedFunction:
                logging.info("Func Code is UNEXPECTED")
                serror = "Unexpected Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code == constants.FUNC_WRITE and frame_len != 7:
                # Reply to Write is always 7 long
                logging.info("response length is INCORRECT")
                serror = "Incorrect length: %s\n" % (frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            if len(datal) != frame_len:
                logging.info("response length MISMATCHES header")
                serror = "Mismatch length: %s %s\n" % (len(datal), frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            # if (func_code == constants.FUNC_READ and
            #   expectedLength !=len(datal) ):
            #   # Read response length is wrong
            #   logging.info("response length
            #    not EXPECTED value")
            #   logging.info("Got %s when expecting %s",
            #   len(datal), expectedLength)
            #   logging.info("Data is:\n %s", datal)
            #   s = "Incorrect length: %s\n" % (frame_len)
            #   sys.stderr.write(s)
            #   badresponse += 1

            if badresponse == 0:
                return True
            else:
                return False

        else:
            assert 0, "Un-supported protocol found %s" % protocol

    def _hm_send_msg(self, message):
        """This is the only interface to the serial connection."""
        logging.debug("Sending serial message")
        try:
            serial_message = message
            logging.debug(f"Writing {serial_message} to serial connection.")
            self.conn.write(serial_message)  # Write a string
        except serial.SerialTimeoutException:
            serror = "Write timeout error: \n"
            sys.stderr.write(serror)
        # Now wait for reply
        byteread = self.conn.read(159)
        # NB max return is 75 in 5/2 mode or 159 in 7day mode
        datal = list(byteread)
        logging.debug(f"Received message from serial {datal}")
        return datal

    def _hm_send_address(self, thermostat_id, address, state, readwrite):
        protocol = constants.HMV3_ID
        logging.info("Sending data with protocol 3.")
        if protocol == constants.HMV3_ID:
            payload = [state]
            msg = self._hm_form_message_crc(
                thermostat_id,
                protocol,
                constants.RW_MASTER_ADDRESS,
                readwrite,
                address,
                payload,
            )
            logging.info(f"Formed payload {msg}")
        else:
            assert 0, "Un-supported protocol found %s" % protocol
        string = bytes(msg)
        datal = self._hm_send_msg(string)
        if readwrite == 1:
            logging.debug("Verifying write CRC")
            verification = self._hm_verify_message_crc_uk(
                0x81, protocol, thermostat_id, readwrite, 1, datal
            )
            if verification is False:
                logging.info("OH DEAR BAD RESPONSE")
            return datal
        else:
            logging.debug("Verifying read CRC")
            verification = self._hm_verify_message_crc_uk(
                0x81, protocol, thermostat_id, readwrite, 75, datal
            )
            if verification is False:
                logging.info("OH DEAR BAD RESPONSE")
            return datal

    def _hm_read_address(self):
        """Reads from the DCB and maps to yaml config file."""
        logging.info("Sending read frame")
        response = self._hm_send_address(self.address, 0, 0, 0)
        logging.debug(response)
        lookup = self.config["keys"]
        offset = self.config["offset"]
        keydata = {}
        for i in lookup:
            try:
                kdata = lookup[i]
                ddata = response[i + offset]
                keydata[i] = {"label": kdata, "value": ddata}
            except IndexError:
                logging.info("Finished processing at %d", i)
        return keydata

    def read_dcb(self):
        """
        Returns the full DCB, only use for non read-only operations
        Use self.dcb for read-only operations.
        """
        logging.info("Getting latest data from DCB....")
        self.dcb = self._hm_read_address()
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
        if temp_format == 00:
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

    def get_frost_protection(self):
        pass

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
        if 17 < frost_temp < 7:
            logging.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 17, frost_temp, 1)
            return True

    def set_target_temp(self, temperature):
        """
        Sets the target temperature, to the requested int
        """
        if 35 < temperature < 5:
            logging.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 18, temperature, 1)
            return True

    def set_floormax_temp(self, floor_max):
        if 45 < floor_max < 20:
            logging.info("Refusing to set temp outside of allowed range")
            return False
        else:
            self._hm_send_address(self.address, 19, floor_max, 1)
            return True
