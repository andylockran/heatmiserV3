"""This module is effectively a singleton for serial comms"""
import logging
import serial
from . import constants
from heatmiserv3 import heatmiser

logger = logging.getLogger(__name__)


class HeatmiserUH1:
    """
    Represents the UH1 interface that holds the serial
    connection, and can have multiple thermostats
    """

    def __init__(self, ipaddress, port):
        self.ipaddress = ipaddress
        self.port = str(port)
        self.thermostats = {}
        self._serport = serial.serial_for_url("socket://" + self.ipaddress + ":" + self.port)
        # Ensures that the serial port has not
        # been left hanging around by a previous process.
        serport_response = self._serport.close()
        logger.info("SerialPortResponse: %s", serport_response)
        self._serport.baudrate = constants.COM_BAUD
        self._serport.bytesize = constants.COM_SIZE
        self._serport.parity = constants.COM_PARITY
        self._serport.stopbits = constants.COM_STOP
        self._serport.timeout = constants.COM_TIMEOUT
        self.status = False
        self._open()

    def _open(self):
        if not self.status:
            logger.info("Opening serial port.")
            self._serport.open()
            self.status = True
            return True
        else:
            logger.info("Attempting to access already open port")
            return False

    def reopen(self, force=False):
        if not self.status or force:
            serport = getattr(self, "_serport", None)
            if serport is not None:
                try:
                    serport.close()
                except Exception:
                    pass
            self._serport = serial.serial_for_url("socket://" + self.ipaddress + ":" + self.port)
            self._serport.open()
            self.status = True
            return self.status
        else:
            logger.error("Cannot open serial port")

    def __del__(self):
        logger.info("Closing serial port.")
        serport = getattr(self, "_serport", None)
        if serport is not None:
            try:
                serport.close()
            except Exception:
                pass

    def registerThermostat(self, thermostat):
        """Registers a thermostat with the UH1"""
        try:
            if not isinstance(thermostat, heatmiser.HeatmiserThermostat):
                raise TypeError("You're not adding a HeatmiserThermostat Object")
            if thermostat.address in self.thermostats:
                raise ValueError("Key already present")
            else:
                self.thermostats[thermostat.address] = thermostat
        except ValueError:
            pass
        except Exception as e:
            logger.info("You're not adding a HeatmiserThermostat Object")
            logger.info("%s", e)
        return self._serport

    def listThermostats(self):
        if self.thermostats:
            return self.thermostats
        else:
            return None
