#
# Neil Trimboy 2011
# Assume Pyhton 2.7.x
#

import serial
#
# from struct import pack
# import time
import sys
#
# import os
# import shutil
# from datetime import datetime
from . import constants

#
# Believe this is known as CCITT (0xFFFF)
# This is the CRC function converted directly from the Heatmiser C code
# provided in their API


class crc16:
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

    def Update4Bits(self, val):
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

    def CRC16_Update(self, val):
        self.Update4Bits(val >> 4)    # High nibble first
        self.Update4Bits(val & 0x0f)   # Low nibble

    def run(self, message):
        """Calculates a CRC"""
        for value in message:
            self.CRC16_Update(value)
        return [self.low, self.high]


def hmFormMsg(
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
            payloadLength = 0
            length_low = (constants.RW_LENGTH_ALL & constants.BYTEMASK)
            length_high = (constants.RW_LENGTH_ALL >> 8) & constants.BYTEMASK
        else:
            payloadLength = len(payload)
            length_low = (payloadLength & constants.BYTEMASK)
            length_high = (payloadLength >> 8) & constants.BYTEMASK
        msg = [
            destination,
            10+payloadLength,
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


def hmFormMsgCRC(
        destination,
        protocol,
        source,
        function,
        start,
        payload
        ):
    """Forms a message payload, including CRC"""
    data = hmFormMsg(destination, protocol, source, function, start, payload)
    crc = crc16()
    data = data + crc.run(data)
    return data


def hmVerifyMsgCRCOK(
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
        checksum = datal[len(datal)-2:]
        rxmsg = datal[:len(datal)-2]
        crc = crc16()   # Initialises the CRC
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

        if (dest_addr != destination):
            print("dest_addr is INCORRECT")
            serror = "Incorrect Dest Addr: %s\n" % (dest_addr)
            sys.stderr.write(serror)
            badresponse += 1

        if (source_addr < 1 or source_addr > 32):
            print("source_addr is ILLEGAL")
            serror = "Illegal Src Addr: %s\n" % (source_addr)
            sys.stderr.write(serror)
            badresponse += 1

        if (source_addr != source):
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

        if (func_code != expectedFunction):
            print("Func Code is UNEXPECTED")
            serror = "Unexpected Func Code: %s\n" % (func_code)
            sys.stderr.write(serror)
            badresponse += 1

        if (func_code == constants.FUNC_WRITE and frame_len != 7):
            # Reply to Write is always 7 long
            print("response length is INCORRECT")
            serror = "%Incorrect length: %s\n" % (frame_len)
            sys.stderr.write(serror)
            badresponse += 1

        if (len(datal) != frame_len):
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


def hmSendMsg(serport, message):
    # TODO avoid passing serport, make port an object?
    try:
        serialmessage = message
        serport.write(serialmessage)   # Write a string
    except serial.SerialTimeoutException:
        serror = "Write timeout error: \n"
        sys.stderr.write(serror)
    # Now wait for reply
    byteread = serport.read(100)
    # NB max return is 75 in 5/2 mode or 159 in 7day mode
    datal = list(byteread)
    return datal


def hmSendAddress(
        destination,
        address,
        state,
        rw,
        serport,
        ):
    protocol = constants.HMV3_ID
    if protocol == constants.HMV3_ID:
        payload = [state]
        msg = hmFormMsgCRC(
            destination,
            protocol,
            constants.MY_MASTER_ADDR,
            rw,
            address,
            payload
            )
    else:
        "Un-supported protocol found %s" % protocol
        assert 0, "Un-supported protocol found %s" % protocol
    string = bytes(msg)
    datal = hmSendMsg(serport, string)
    pro = protocol
    if rw == 1:
        verification = hmVerifyMsgCRCOK(0x81, pro, destination, rw, 1, datal)
        if verification is False:
            print("OH DEAR BAD RESPONSE")
        return datal
    else:
        verification = hmVerifyMsgCRCOK(0x81, pro, destination, rw, 75, datal)
        if verification is False:
            print("OH DEAR BAD RESPONSE")
        return datal


def hmReadAddress(
        destination,
        type,
        serport
        ):
    datal = hmSendAddress(destination, 0, 0, 0, serport)
    DATAOFFSET = 9
    if type == 'prt':
        response = {
            'vendor': datal[2 + DATAOFFSET],
            'version': datal[3 + DATAOFFSET] & 0x7f,
            'floorlimiting': datal[3 + DATAOFFSET] >> 7,
            'model': datal[4 + DATAOFFSET],
            'tempfmt': datal[5 + DATAOFFSET],
            'switchdiff': datal[6 + DATAOFFSET],
            'frostprot': datal[7 + DATAOFFSET],
            'cal_h': datal[8 + DATAOFFSET],
            'cal_l': datal[9 + DATAOFFSET],
            # 'caloffset': (cal_h*256 + cal_l),
            'opdelay': datal[10 + DATAOFFSET],
            'address': datal[11 + DATAOFFSET],
            'updwnlimit': datal[12 + DATAOFFSET],
            'thissensormode': datal[13 + DATAOFFSET],
            'optimstart': datal[14 + DATAOFFSET],
            'rateofchange': datal[15 + DATAOFFSET],
            'progmode': datal[16 + DATAOFFSET],
            'frosttemp': datal[17 + DATAOFFSET],
            'roomset': datal[18 + DATAOFFSET],
            'floorlimit': datal[19 + DATAOFFSET],
            'floormaxenable': datal[20 + DATAOFFSET],
            'onoff': datal[21 + DATAOFFSET],
            'keylock': datal[22 + DATAOFFSET],
            'runmode': datal[23 + DATAOFFSET],
            'holidayhourshigh': datal[24 + DATAOFFSET],
            'holidayhourslow': datal[25 + DATAOFFSET],
            # 'holidayhours': (holidayhourshigh*256 + holidayhourslow),
            'tempholdminshigh': datal[26 + DATAOFFSET],
            'tempholdminslow': datal[27 + DATAOFFSET],
            # 'tempholdmins': (tempholdminshigh*256 + tempholdminslow),
            'remoteairtemphigh': datal[28 + DATAOFFSET],
            'remoteairtemplow ': datal[29 + DATAOFFSET],
            # 'remoteairtemp': (remoteairtemphigh*256 + remoteairtemplow)/10.0,
            'floortemphigh': datal[30 + DATAOFFSET],
            'floortemplow ': datal[31 + DATAOFFSET],
            # 'floortemp': (floortemphigh*256 + floortemplow)/10.0,
            'intairtemphigh': datal[32 + DATAOFFSET],
            'intairtemplow ': datal[33 + DATAOFFSET],
            # 'intairtemp': (intairtemphigh*256 + intairtemplow)/10.0,
            'errcode': datal[34 + DATAOFFSET],
            'thisdemand': datal[35 + DATAOFFSET],
            'currentday': datal[36 + DATAOFFSET],
            'currenthour': datal[37 + DATAOFFSET],
            'currentmin': datal[38 + DATAOFFSET],
            'currentsec': datal[39 + DATAOFFSET],
            'wday_t1_hour': datal[40 + DATAOFFSET],
            'wday_t1_mins': datal[41 + DATAOFFSET],
            'wday_t1_temp': datal[42 + DATAOFFSET],
            'wday_t2_hour': datal[43 + DATAOFFSET],
            'wday_t2_mins': datal[44 + DATAOFFSET],
            'wday_t2_temp': datal[45 + DATAOFFSET],
            'wday_t3_hour': datal[46 + DATAOFFSET],
            'wday_t3_mins': datal[47 + DATAOFFSET],
            'wday_t3_temp': datal[48 + DATAOFFSET],
            'day_t4_hour': datal[49 + DATAOFFSET],
            'wday_t4_mins': datal[50 + DATAOFFSET],
            'wday_t4_temp': datal[51 + DATAOFFSET],
            'wend_t1_hour': datal[52 + DATAOFFSET],
            'wend_t1_mins': datal[53 + DATAOFFSET],
            'wend_t1_temp': datal[54 + DATAOFFSET],
            'wend_t2_hour': datal[55 + DATAOFFSET],
            'wend_t2_mins': datal[56 + DATAOFFSET],
            'wend_t2_temp': datal[57 + DATAOFFSET],
            'wend_t3_hour': datal[58 + DATAOFFSET],
            'wend_t3_mins': datal[59 + DATAOFFSET],
            'wend_t3_temp': datal[60 + DATAOFFSET],
            'wend_t4_hour': datal[61 + DATAOFFSET],
            'wend_t4_mins': datal[62 + DATAOFFSET],
            'wend_t4_temp': datal[63 + DATAOFFSET],
        }
    elif type == 'tm1':
        response = {
            '0': datal[0 + DATAOFFSET],
            '1': datal[1 + DATAOFFSET],
            '2': datal[2 + DATAOFFSET],
            '3': datal[3 + DATAOFFSET],
            '4': datal[4 + DATAOFFSET],
            '5': datal[5 + DATAOFFSET],
            '6': datal[6 + DATAOFFSET],
            '7': datal[7 + DATAOFFSET],
            '8': datal[8 + DATAOFFSET],
            '9': datal[9 + DATAOFFSET],
            '10': datal[10 + DATAOFFSET],
            '11': datal[11 + DATAOFFSET],
            '12': datal[12 + DATAOFFSET],
            '13': datal[13 + DATAOFFSET],
            '14': datal[14 + DATAOFFSET],
            '15': datal[15 + DATAOFFSET],
            '16': datal[16 + DATAOFFSET],
            '17': datal[17 + DATAOFFSET],
            '18': datal[18 + DATAOFFSET],
            '19': datal[19 + DATAOFFSET],
            '20': datal[20 + DATAOFFSET],
            '21': datal[21 + DATAOFFSET],
            '22': datal[22 + DATAOFFSET],
            '23': datal[23 + DATAOFFSET],
            '24': datal[24 + DATAOFFSET],
            '25': datal[25 + DATAOFFSET],
            '26': datal[26 + DATAOFFSET],
            '27': datal[27 + DATAOFFSET],
            '28': datal[28 + DATAOFFSET],
            '29': datal[29 + DATAOFFSET],
            '30': datal[30 + DATAOFFSET],
            '31': datal[31 + DATAOFFSET],
            '32': datal[32 + DATAOFFSET],
            '33': datal[33 + DATAOFFSET],
            '34': datal[34 + DATAOFFSET],
            '35': datal[35 + DATAOFFSET],
            '36': datal[36 + DATAOFFSET],
            '37': datal[37 + DATAOFFSET],
            '38': datal[38 + DATAOFFSET],
            '39': datal[39 + DATAOFFSET],
            '40': datal[40 + DATAOFFSET],
            '41': datal[41 + DATAOFFSET],
            '42': datal[42 + DATAOFFSET],
            '43': datal[43 + DATAOFFSET],
            '44': datal[44 + DATAOFFSET],
            '45': datal[45 + DATAOFFSET],
            '46': datal[46 + DATAOFFSET],
            '47': datal[47 + DATAOFFSET],
            '48': datal[48 + DATAOFFSET],
            '49': datal[49 + DATAOFFSET],
            '50': datal[50 + DATAOFFSET],
            '51': datal[51 + DATAOFFSET],
            '52': datal[52 + DATAOFFSET],
            '53': datal[53 + DATAOFFSET],
            '54': datal[54 + DATAOFFSET],
            '55': datal[55 + DATAOFFSET],
            '56': datal[56 + DATAOFFSET],
            '57': datal[57 + DATAOFFSET],
            '58': datal[58 + DATAOFFSET],
            '59': datal[59 + DATAOFFSET],
            '60': datal[60 + DATAOFFSET],
            '61': datal[61 + DATAOFFSET],
            '62': datal[62 + DATAOFFSET]
        }

    return response
