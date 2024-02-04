
from heatmiserv3 import crc16
from mock_serial import MockSerial
import logging, sys        


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)

MockSerialThermostat = MockSerial()
MockSerialThermostat.open()



def interpret_message_generate_response(message):
    """ 
    Calculates the CRC of the message 
    """
    logging.info("Processing mock message.")
    crc = crc16.CRC16()
    logging.debug(f"Generating response to ${message}")
    response=bytearray(73)
    logging.debug(type(response))
    response[0] = list(message)[2] # Destination address
    response[1] = 7 if list(message)[1] > 10 else 75  ## Low 8 bit 
    response[2] = 0 ## High 8 bit
    response[3] = list(message)[0] ## Source address
    response[4] = 0 ## Function Code (00 read, 01 write)
    response[5] = list(message)[5] ## Start Address (low 8 bit)
    response[6] = list(message)[6] ## Start Address (high 8 bit)
    response[7] = 64 ## Action number of bytes read (low 8 bit)
    response[8] = 0 ## Action number of bytes read (high 8 bit)
    logging.debug("Bytearray response is: %s", response)
    response[9:73] = bytearray([0,64,0,15,2,0,2,1,0,0,0,1,0,0,0,20,0,15,21,28,1,1,0,0,0,0,0,0,255,255,255,255,0,201,0,0,4,16,22,18,24,0,19,24,0,5,24,0,19,24,0,5,5,30,23,22,0,20,24,0,16,24,0,16]) ## Contents
    data = list(response)
    data = data + crc.run(data)
    checksum = data[len(data) - 2:]
    logging.info(f"Checksum value is: {checksum}")
    rxmsg = data[: len(data) - 2]
    logging.info(f"RXmsg value is: {rxmsg}")
    logging.debug("Final response is: %s", data )
    logging.debug("Bytearray response is: %s", data)
    return bytearray(data)


## Mock Thermostat 1
MockSerialThermostat.stub(
    receive_bytes=b'\x01\n\x81\x00\x00\x00\xff\xff,\t',
    send_bytes=interpret_message_generate_response(b'\x01\n\x81\x00\x00\x00\xff\xff,\t')
    # send_bytes=calculate_crc_in_bytearray(b'\x01\n\x81\x00\x00\x00\xff\xff,\t')
)

## Mock Thermostat 2
MockSerialThermostat.stub(
    receive_bytes=b'\x02\n\x81\x00\x00\x00\xff\xffY\xc1',
    send_bytes=interpret_message_generate_response(b'\x02\n\x81\x00\x00\x00\xff\xffY\xc1')
)

# Mock Thermostat 3
MockSerialThermostat.stub(
    receive_bytes=b'\x03\n\x81\x00\x00\x00\xff\xff\x8a\x86',
    send_bytes=interpret_message_generate_response(b'\x03\n\x81\x00\x00\x00\xff\xff,\t,\xd4\x8d')
)