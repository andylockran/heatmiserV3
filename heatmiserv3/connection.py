"""This module is effectively a singleton for serial comms"""
import serial
import logging
from . import constants
from heatmiserv3 import heatmiser
from heatmiserv3.thermostat import MockSerialThermostat
logging.basicConfig(level=logging.INFO)


class HeatmiserUH1(object):
    """
    Represents the UH1 interface that holds the serial
    connection, and can have multiple thermostats
    """

    def __init__(self, ipaddress, port):
        self.thermostats = {}
        if ipaddress == "mock":
            device = MockSerialThermostat
            self.serialport = serial.Serial(device.port)
        else:
            self.serialport = serial.serial_for_url("socket://" + ipaddress + ":" + port)
        # Ensures that the serial port has not
        # been left hanging around by a previous process.
        self.serialport.close()
        
        ### Serial Connection Settings
        self.serialport.baudrate = constants.COM_BAUD
        self.serialport.bytesize = constants.COM_SIZE
        self.serialport.parity = constants.COM_PARITY
        self.serialport.stopbits = constants.COM_STOP
        self.serialport.timeout = constants.COM_TIMEOUT
        self._open()

    def _open(self):
        if not self.serialport.is_open:
            logging.info("Opening serial port.")
            self.serialport.open()
            self.status = True
        else:
            logging.info("Attempting to access already open port")

    def __del__(self):
        logging.info("Closing serial port.")
        self.serialport.close()
