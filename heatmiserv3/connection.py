"""This module is effectively a singleton for serial comms"""
import serial
import logging
from . import constants
from heatmiserv3 import heatmiser

logging.basicConfig(level=logging.INFO)


class HeatmiserUH1(object):
    """
    Represents the UH1 interface that holds the serial
    connection, and can have multiple thermostats
    """

    def __init__(self, ipaddress=None, port=None, dev=None):
        if dev is not None:
            if ipaddress is not None or port is not None:
                raise ValueError("Specify either dev or both ipaddress and port")
            if not isinstance(dev, str) or not dev:
                raise ValueError("dev must be a non-empty serial device path")
            self._serial_url = dev
        else:
            if not isinstance(ipaddress, str) or not ipaddress:
                raise ValueError("ipaddress must be provided when dev is not specified")
            if not isinstance(port, str) or not port:
                raise ValueError("port must be provided when dev is not specified")
            self._serial_url = "socket://" + ipaddress + ":" + port

        self.ipaddress = ipaddress
        self.port = port
        self.dev = dev
        self.thermostats = {}
        self._serport = self._new_serial_port()
        self.status = False
        self._open()

    def _new_serial_port(self):
        serport = serial.serial_for_url(self._serial_url)
        # Ensures that the serial port has not
        # been left hanging around by a previous process.
        serport_response = serport.close()
        logging.info("SerialPortResponse: %s", serport_response)
        serport.baudrate = constants.COM_BAUD
        serport.bytesize = constants.COM_SIZE
        serport.parity = constants.COM_PARITY
        serport.stopbits = constants.COM_STOP
        serport.timeout = constants.COM_TIMEOUT
        return serport

    def _open(self):
        if not self.status:
            logging.info("Opening serial port.")
            self._serport.open()
            self.status = True
            return True
        else:
            logging.info("Attempting to access already open port")
            return False

    def reopen(self, force=False):
        if not self.status or force:
            self._serport = self._new_serial_port()
            self._serport.open()
            self.status = True
            return self.status
        else:
            logging.error("Cannot open serial port")

    def __del__(self):
        logging.info("Closing serial port.")
        if hasattr(self, "_serport"):
            self._serport.close()

    def registerThermostat(self, thermostat):
        """Registers a thermostat with the UH1"""
        try:
            if not isinstance(thermostat, heatmiser.HeatmiserThermostat):
                raise TypeError("You're not adding a HeatmiserThermostat Object")
            if thermostat.address in self.thermostats.keys():
                raise ValueError("Key already present")
            else:
                self.thermostats[thermostat.address] = thermostat
        except ValueError:
            pass
        except Exception as e:
            logging.info("You're not adding a HeatmiiserThermostat Object")
            logging.info(e.message)
        return self._serport

    def listThermostats(self):
        if self.thermostats:
            return self.thermostats
        else:
            return None
