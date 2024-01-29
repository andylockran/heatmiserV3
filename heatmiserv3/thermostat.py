
from heatmiserv3.heatmiser import CRC16
from mock_serial import MockSerial
import logging        
from . import constants

MockSerialThermostat = MockSerial()

def calculate_crc_in_bytearray(received_bytes):
    response = bytearray(80)
    crc = CRC16()
    crcresult = crc.run(received_bytes)
    logging.debug("CRC result: %s", crcresult)
    logging.debug(type(response))
    response[0] = 1 ## Thermostat Address
    response[1] = 0 ## Low 8 bit
    response[2] = 0 ## High 8 bit
    response[3] = 1 ## Source address
    response[4] = 0 ## Function Code (00 read, 01 write)
    response[5] = 0 ## Start Address (low 8 bit)
    response[6] = 6 ## Start Address (high 8 bit)
    response[7] = 0 ## Action number of bytes read (low 8 bit)
    response[8] = 0 ## Action number of bytes read (high 8 bit)
    logging.debug("Bytearray response is: %s", response)
    response[9:73] = bytearray(64) ## Contents
    data = list(response)
    data = data + crc.run(data)
    logging.debug("Bytearray response is: %s", response)
    return response

MockSerialThermostat.stub(
    receive_bytes=b'\x01\n\x81\x00\x00\x00\xff\xff,\t',
    send_bytes=calculate_crc_in_bytearray(b'\x01\n\x81\x00\x00\x00\xff\xff,\t')
)