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

    def __init__(self, ipaddress=None, port=None, dev=None):
        if dev is not None:
            if ipaddress is not None or port is not None:
                raise ValueError("Specify either dev or both ipaddress and port")
            if not isinstance(dev, str) or not dev.strip():
                raise ValueError("dev must be a non-empty serial device path")
            self._serial_url = dev
            self.ipaddress = None
            self.port = None
            self.dev = dev
        else:
            if not isinstance(ipaddress, str) or not ipaddress.strip():
                raise ValueError(
                    "ipaddress must be provided when dev is not specified"
                )
            if (
                port is None
                or (isinstance(port, str) and not port.strip())
                or not isinstance(port, (str, int))
            ):
                raise ValueError(
                    "port must be provided when dev is not specified"
                )
            self.ipaddress = ipaddress
            self.port = str(port)
            self.dev = None
            self._serial_url = f"socket://{self.ipaddress}:{self.port}"

        self.thermostats = {}
        self._serport = self._new_serial_port()
        self.status = False
        self._open()

    def _new_serial_port(self):
        serport = serial.serial_for_url(self._serial_url)
        # Ensures that the serial port has not
        # been left hanging around by a previous process.
        serport_response = serport.close()
        logger.info("SerialPortResponse: %s", serport_response)
        serport.baudrate = constants.COM_BAUD
        serport.bytesize = constants.COM_SIZE
        serport.parity = constants.COM_PARITY
        serport.stopbits = constants.COM_STOP
        serport.timeout = constants.COM_TIMEOUT
        return serport

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
            self._serport = self._new_serial_port()
            self._serport.open()
            self.status = True
            for thermostat in self.thermostats.values():
                thermostat.conn = self._serport
            return self.status
        else:
            logger.error("Cannot open serial port")
            return None

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
