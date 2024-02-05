
from heatmiserv3 import crc16, constants, connection, heatmiser
import serial
from mock_serial import MockSerial
from mock import patch
import logging, sys        


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s - %(message)s"
)

class MockHeatmiserPRT(heatmiser.HeatmiserThermostatPRT):
    def __init__(self, address, uh1):
        super(MockHeatmiserPRT, self).__init__(address, uh1)
        self.dcb = bytearray([0,64,0,15,2,0,2,1,0,0,0,1,0,0,0,20,0,15,21,28,1,1,0,0,0,0,0,0,255,255,255,255,0,201,0,0,4,16,22,18,24,0,19,24,0,5,24,0,19,24,0,5,5,30,23,22,0,20,24,0,16,24,0,16])
    
    def read_dcb(self):
        return self.dcb
    
    def generate_response(self, message):
        """ 
        Calculates the CRC of the response 
        """
        logging.info("Processing mock response.")
        crc = crc16.CRC16()
        logging.debug(f"Generating response to {message}")
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
        response[9:73] = self.dcb
        data = list(response)
        data = data + crc.run(data)
        checksum = data[len(data) - 2:]
        logging.info(f"Checksum value is: {checksum}")
        rxmsg = data[: len(data) - 2]
        logging.info(f"RXmsg value is: {rxmsg}")
        logging.debug("Final response is: %s", data )
        logging.debug("Bytearray response is: %s", data)
        return bytearray(data)
    
    def generate_reply(self, message):
        logging.debug(f"Attempting to write {message}")
        crc = crc16.CRC16()
        logging.debug("Testing logging")
        response = bytearray(5)
        response[0] = list(message)[2] # Destination address
        response[1] = 7 if list(message)[1] > 10 else 75  ## Low 8 bit 
        response[2] = 0 ## High 8 bit
        response[3] = list(message)[0] ## Source address
        response[4] = 1 ## Write
        logging.debug(f"Printing response {response}")
        data = list(response)
        data = data + crc.run(data) 
        logging.debug(f"Writing response to write request {data}")
        return bytearray(data)

    def process_message(self, message):
        logging.info("Processing mock message.")
        logging.debug(f"Processing {message}")
        data = list(message)
        if data[3] == 1:
            logging.debug("Processing write message")
            return self.generate_reply(message)
        elif data[3] == 0:
            logging.debug("Processing read messages")
            return self.generate_response(message)
        else:
            logging.debug(data[3])
            logging.error("Cannot process message")
            raise Exception("Invalid functionCode, must be 1 or 0 for write or read.")


MockSerialPort = MockSerial()
MockSerialPort.open()
device = MockSerialPort
serialport = serial.Serial(device.port)
# self.serialport = serial.serial_for_url("socket://" + ipaddress + ":" + port)
### Serial Connection Settings
serialport.baudrate = constants.COM_BAUD
serialport.bytesize = constants.COM_SIZE
serialport.parity = constants.COM_PARITY
serialport.stopbits = constants.COM_STOP
serialport.timeout = constants.COM_TIMEOUT


MockUH1 = connection.HeatmiserUH1(serialport)
thermo1 = MockHeatmiserPRT(1, MockUH1)
thermo2 = MockHeatmiserPRT(2, MockUH1)
thermo3 = MockHeatmiserPRT(3, MockUH1)


## Mock Thermostat 1
MockSerialPort.stub(
    receive_bytes=b'\x01\n\x81\x00\x00\x00\xff\xff,\t',
    send_bytes=thermo1.process_message(b'\x01\n\x81\x00\x00\x00\xff\xff,\t')
    # send_bytes=calculate_crc_in_bytearray(b'\x01\n\x81\x00\x00\x00\xff\xff,\t')
)

## Mock Thermostat 2
MockSerialPort.stub(
    receive_bytes=b'\x02\n\x81\x00\x00\x00\xff\xffY\xc1',
    send_bytes=thermo2.process_message(b'\x02\n\x81\x00\x00\x00\xff\xffY\xc1')
)

# Mock Thermostat 3
MockSerialPort.stub(
    receive_bytes=b'\x03\n\x81\x00\x00\x00\xff\xff\x8a\x86',
    send_bytes=thermo3.process_message(b'\x03\n\x81\x00\x00\x00\xff\xff,\t,\xd4\x8d')
)

MockSerialPort.stub(
    receive_bytes=b'\x01\x0b\x81\x01\x12\x00\x01\x00\x16\xd8v',
    send_bytes=thermo1.process_message(b'\x01\x0b\x81\x01\x12\x00\x01\x00\x16\xd8v')
)