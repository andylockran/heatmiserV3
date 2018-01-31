"""This module is effectively a singleton for serial comms"""
import sys
import serial
from . import constants


def hmserial(ipaddress, port):
    """Imported as a module so that it's only ever created once."""
    serport = serial.serial_for_url("socket://" + ipaddress + ":" + port)
    serport.close()
    serport.baudrate = constants.COM_BAUD
    serport.bytesize = constants.COM_SIZE
    serport.parity = constants.COM_PARITY
    serport.stopbits = constants.COM_STOP
    serport.timeout = constants.COM_TIMEOUT
    try:
        serport.open()
    except serial.SerialException as e_message:
        s_message = "Could not open serial port %s: %s\n" % (
            serport.portstr,
            e_message
        )
        sys.stderr.write(s_message)
    serport.close()
    return serport
