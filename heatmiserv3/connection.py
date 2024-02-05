"""This module is effectively a singleton for serial comms"""
import logging
logging.basicConfig(level=logging.INFO)


class HeatmiserUH1(object):
    """
    Represents the UH1 interface that holds the serial
    connection, and can manage up to 32 devices.
    """

    def __init__(self, serialport):
        
        self.serialport = serialport
        # Ensures that the serial port has not
        # been left hanging around by a previous process.
        self.serialport.close()
        self._open()

    def _open(self):
        if not self.serialport.is_open:
            logging.info("Opening serial port.")
            self.serialport.open()
        else:
            logging.info("Attempting to access already open port")
        
    def reopen(self):
        self.serialport.open()

    def __del__(self):
        logging.info("Closing serial port.")
        self.serialport.close()
