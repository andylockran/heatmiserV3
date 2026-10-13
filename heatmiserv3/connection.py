"""This module is effectively a singleton for serial comms"""
import logging
import threading
import time
import serial
from . import constants
from heatmiserv3 import heatmiser

logger = logging.getLogger(__name__)


class HeatmiserUH1:
    """
    Represents the UH1 interface that holds the serial
    connection, and can have multiple thermostats
    """

    def __init__(
        self,
        ipaddress=None,
        port=None,
        dev=None,
        inter_command_delay=None,
        recovery_pause=None,
    ):
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

        self.inter_command_delay = (
            float(inter_command_delay)
            if inter_command_delay is not None
            else constants.BUS_INTER_COMMAND_DELAY
        )
        self.recovery_pause = (
            float(recovery_pause)
            if recovery_pause is not None
            else constants.BUS_RECOVERY_PAUSE
        )
        self._bus_lock = threading.Lock()
        self._last_bus_activity = 0.0

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

    def bus_recovery(self):
        """Flushes serial buffers and observes bus quiet period after a communication failure."""
        logger.warning(
            "Performing RS485 bus recovery pause (%.3fs)", self.recovery_pause
        )
        serport = getattr(self, "_serport", None)
        if serport is not None:
            try:
                if hasattr(serport, "reset_input_buffer"):
                    serport.reset_input_buffer()
                if hasattr(serport, "reset_output_buffer"):
                    serport.reset_output_buffer()
            except Exception as e:
                logger.debug("Error while resetting serial buffers: %s", e)
        if self.recovery_pause > 0:
            time.sleep(self.recovery_pause)
        self._last_bus_activity = time.monotonic()

    def transact(self, message, read_length=159):
        """
        Thread-safe RS485 bus transaction executor.
        Acquires the bus lock, enforces inter-transaction turnaround quiet time,
        transmits the frame, reads the reply, and executes bus recovery on failure.
        """
        with self._bus_lock:
            # Enforce RS485 half-duplex turnaround time
            now = time.monotonic()
            elapsed = now - self._last_bus_activity
            if elapsed < self.inter_command_delay:
                time.sleep(self.inter_command_delay - elapsed)

            serport = getattr(self, "_serport", None)
            if serport is None:
                raise serial.serialutil.SerialException("Serial port is not initialized")

            # Transmit frame
            try:
                serport.write(message)
            except serial.SerialTimeoutException as e:
                logger.error("Serial write timeout error: %s", e)
                self.bus_recovery()
                return []
            except Exception as e:
                logger.error("Serial write error: %s", e)
                self.bus_recovery()
                raise

            # Read reply
            byteread = b""
            try:
                byteread = serport.read(read_length)
            except (serial.serialutil.SerialException, AttributeError) as e:
                logger.error("Connection failed during read: %s, attempting reconnect", e)
                self.bus_recovery()
                self.reopen(force=True)
                return []
            except Exception as e:
                logger.error("Unexpected read exception: %s", e)
                self.bus_recovery()
                raise
            finally:
                self._last_bus_activity = time.monotonic()

            datal = list(byteread) if byteread else []
            if not datal:
                self.bus_recovery()
            return datal

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
                thermostat.uh1 = self
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
