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
    except serial.SerialException as e:
        s = "%s : Could not open serial port %s: %s\n" % (localtime, serport.portstr, e)
        sys.stderr.write(s)
    serport.close()
    return serport



