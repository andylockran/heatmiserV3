#
# Neil Trimboy 2011
# Assume Python 2.7.x +
#
import sys
import serial
import yaml
import logging
from . import constants

#
# Believe this is known as CCITT (0xFFFF)
# This is the CRC function converted directly from the Heatmiser C code
# provided in their API


class CRC16:
    """This is the CRC hashing mechanism used by the V3 protocol."""
    LookupHigh = [
        0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
        0x81, 0x91, 0xa1, 0xb1, 0xc1, 0xd1, 0xe1, 0xf1
    ]
    LookupLow = [
        0x00, 0x21, 0x42, 0x63, 0x84, 0xa5, 0xc6, 0xe7,
        0x08, 0x29, 0x4a, 0x6b, 0x8c, 0xad, 0xce, 0xef
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
        self.high = self.high & constants.BYTEMASK    # force char
        self.low = self.low << 4
        self.low = self.low & constants.BYTEMASK      # force char
        # Do the table lookups and XOR the result into the CRC tables
        self.high = self.high ^ self.LookupHigh[thisval]
        self.high = self.high & constants.BYTEMASK    # force char
        self.low = self.low ^ self.LookupLow[thisval]
        self.low = self.low & constants.BYTEMASK      # force char

    def update(self, val):
        """Updates the CRC value using bitwise operations."""
        self.extract_bits(val >> 4)    # High nibble first
        self.extract_bits(val & 0x0f)   # Low nibble

    def run(self, message):
        """Calculates a CRC"""
        for value in message:
            self.update(value)
        return [self.low, self.high]


class HeatmiserThermostat(object):
    """Initialises a heatmiser thermostat, by taking an address and model."""

    def __init__(self, address, model, conn):
        self.address = address
        self.model = model
        self.conn = conn
        with open("heatmiserV3/config.yml", "r") as stream:
            try:
                self.config = yaml.load(stream)[model]
            except yaml.YAMLError as exc:
                print("The YAML file is invalid: %s", exc)

    def _hm_form_message(
            self,
            destination,
            protocol,
            source,
            function,
            start,
            payload
    ):
        """Forms a message payload, excluding CRC"""
        if protocol == constants.HMV3_ID:
            start_low = (start & constants.BYTEMASK)
            start_high = (start >> 8) & constants.BYTEMASK
            if function == constants.FUNC_READ:
                payload_length = 0
                length_low = (constants.RW_LENGTH_ALL & constants.BYTEMASK)
                length_high = (constants.RW_LENGTH_ALL >> 8) & constants.BYTEMASK
            else:
                payload_length = len(payload)
                length_low = (payload_length & constants.BYTEMASK)
                length_high = (payload_length >> 8) & constants.BYTEMASK
            msg = [
                destination,
                10 + payload_length,
                source,
                function,
                start_low,
                start_high,
                length_low,
                length_high
            ]
            if function == constants.FUNC_WRITE:
                msg = msg + payload
                type(msg)
            return msg
        else:
            assert 0, "Un-supported protocol found %s" % protocol

    def _hm_form_message_crc(
            self,
            destination,
            protocol,
            source,
            function,
            start,
            payload
    ):
        """Forms a message payload, including CRC"""
        data = self._hm_form_message(
            destination, protocol, source, function, start, payload)
        crc = CRC16()
        data = data + crc.run(data)
        return data

    def _hm_verify_message_crc_uk(
            self,
            destination,
            protocol,
            source,
            expectedFunction,
            expectedLength,
            datal
    ):
        """Verifies message appears legal"""
        # expectedLength only used for read msgs as always 7 for write
        badresponse = 0
        if protocol == constants.HMV3_ID:
            checksum = datal[len(datal) - 2:]
            rxmsg = datal[:len(datal) - 2]
            crc = CRC16()   # Initialises the CRC
            expectedchecksum = crc.run(rxmsg)
            if expectedchecksum == checksum:
                print("CRC is correct")
            else:
                print("CRC is INCORRECT")
                serror = "Incorrect CRC"
                sys.stderr.write(serror)
                badresponse += 1
            dest_addr = datal[0]
            frame_len_l = datal[1]
            frame_len_h = datal[2]
            frame_len = (frame_len_h << 8) | frame_len_l
            source_addr = datal[3]
            func_code = datal[4]

            if (dest_addr != 129 and dest_addr != 160):
                print("dest_addr is ILLEGAL")
                serror = "Illegal Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if dest_addr != destination:
                print("dest_addr is INCORRECT")
                serror = "Incorrect Dest Addr: %s\n" % (dest_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if (source_addr < 1 or source_addr > 32):
                print("source_addr is ILLEGAL")
                serror = "Illegal Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if source_addr != source:
                print("source addr is INCORRECT")
                serror = "Incorrect Src Addr: %s\n" % (source_addr)
                sys.stderr.write(serror)
                badresponse += 1

            if (
                func_code != constants.FUNC_WRITE and
                    func_code != constants.FUNC_READ
            ):
                print("Func Code is UNKNWON")
                serror = "Unknown Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if func_code != expectedFunction:
                print("Func Code is UNEXPECTED")
                serror = "Unexpected Func Code: %s\n" % (func_code)
                sys.stderr.write(serror)
                badresponse += 1

            if (
                    func_code == constants.FUNC_WRITE and
                    frame_len != 7
            ):
                # Reply to Write is always 7 long
                print("response length is INCORRECT")
                serror = "Incorrect length: %s\n" % (frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            if len(datal) != frame_len:
                print("response length MISMATCHES header")
                serror = "Mismatch length: %s %s\n" % (len(datal), frame_len)
                sys.stderr.write(serror)
                badresponse += 1

            """if (func_code == constants.FUNC_READ and expectedLength !=len(datal) ):
              # Read response length is wrong
              print("response length not EXPECTED value")
              print(len(datal))
              print(datal)
              s = "Incorrect length: %s\n" % (frame_len)
              sys.stderr.write(s)
              badresponse += 1
            """
            if (badresponse == 0):
                return True
            else:
                return False

        else:
            assert 0, "Un-supported protocol found %s" % protocol

    def _hm_send_msg(self, message):
        """This is the only interface to the serial connection."""
        try:
            serial_message = message
            self.conn.write(serial_message)   # Write a string
        except serial.SerialTimeoutException:
            serror = "Write timeout error: \n"
            sys.stderr.write(serror)
        # Now wait for reply
        byteread = self.conn.read(159)
        # NB max return is 75 in 5/2 mode or 159 in 7day mode
        datal = list(byteread)
        return datal

    def _hm_send_address(self, destination, address, state, readwrite):
        protocol = constants.HMV3_ID
        if protocol == constants.HMV3_ID:
            payload = [state]
            msg = self._hm_form_message_crc(
                destination,
                protocol,
                constants.RW_MASTER_ADDRESS,
                readwrite,
                address,
                payload
            )
        else:
            assert 0, "Un-supported protocol found %s" % protocol
        string = bytes(msg)
        datal = self._hm_send_msg(string)
        pro = protocol
        if readwrite == 1:
            verification = self._hm_verify_message_crc_uk(
                0x81, pro, destination, readwrite, 1, datal)
            if verification is False:
                print("OH DEAR BAD RESPONSE")
            return datal
        else:
            verification = self._hm_verify_message_crc_uk(
                0x81, pro, destination, readwrite, 75, datal)
            if verification is False:
                print("OH DEAR BAD RESPONSE")
            return datal

    def _hm_read_address(self):
        """Reads from the DCB and maps to yaml config file."""
        response = self._hm_send_address(self.address, 0, 0, 0)
        lookup = self.config['keys']
        offset = self.config['offset']
        keydata = {}
        for i in lookup:
            try:
                kdata = lookup[i]
                ddata = response[i + offset]
                keydata[i] = {
                    'label': kdata,
                    'value': ddata
                }
            except IndexError:
                print("Finished processing at %d", i)
        return keydata

    def get_dcb(self):
        """
        Returns the full DCB
        """
        return self._hm_read_address()

    def get_target_temperature(self):
        """
        Returns the temperature
        """
        return self._hm_read_address()[18]['value']
