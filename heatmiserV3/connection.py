import serial
from .constants import Constants
from .protocol import HeatmiserV3Protocol

class HeatmiserConnection(object):

    def __init__(self):
        self.host = None
        self.pin = None
        self.socket = None
        self.port = None
        self.connection = None
        self.protocol = None

    @classmethod
    def serial(cls, ipaddress, port):
        heatmiser = SerialConnection()
        heatmiser.host = host
        heatmiser.port = port
        heatmiser.protocol = HeatmiserV3Protocol(Constants.CONNECTION_TYPES[0])
        return heatmiser

    @classmethod
    def tcp(cls, host=Constants.DEFAULT_TCP_OPTIONS['host'], pin=Constants.DEFAULT_TCP_OPTIONS['pin']):
        heatmiser = TCPConnection()
        heatmiser.host = host
        heatmiser.port = Constants.DEFAULT_TCP_OPTIONS['port']
        heatmiser.protocol = HeatmiserV3Protocol(Constants.CONNECTION_TYPES[1])
        return heatmiser

    def open(self):
        pass

    def close(self):
        self.connection.close()
        self.connection = None

    def get_response(self):
        pass

    def get_status(self):
        pass

    def update_status(self, dcb):
        pass

class SerialConnection(HeatmiserConnection):

    def open(self):
        if self.connection is not None:
            return
        serport = serial.serial_for_url("socket://" + self.host + ":" + self.port)
        serport.close()
        #serport.port = constants.COM_PORT
        serport.baudrate = Constants.COM_BAUD
        serport.bytesize = Constants.COM_SIZE
        serport.parity = Constants.COM_PARITY
        serport.stopbits = Constants.COM_STOP
        serport.timeout = Constants.COM_TIMEOUT
        try:
            serport.open()
        except serial.SerialException as e:
                s= "%s : Could not open serial port %s: %s\n" % (localtime, serport.portstr, e)
                sys.stderr.write(s)
                problem += 1
        serport.close()
        self.connection = serport

    def update_status(self, dcb):
        self.status = self.protocol.dcb_to_status(dcb)

    def get_response(self):
        try:
            return self.connection.read(100)
            # NB max return is 75 in 5/2 mode or 159 in 7day mode
        except Exception as ex:
            self.close()
            raise HeatmiserException('No response from thermostat: %s' % str(ex))

    def get_status(self):
        # Ensure serial connection is open
        try:
            self.open()
        except Exception as ex:
            raise HeatmiserException(str(ex))

        cmd = self.protocol.read_dcb_serial()

        # Send the command to the thermostat
        try:
            self.connection.write(cmd)
        except Exception as ex:
            self.close()
            raise HeatmiserException('Failed to send command to thermostat: %s' % str(ex))

        status = self.protocol.parse_serial_response(self.get_response(), Constants.FUNC_READ)
        self.update_status(status)


class TCPConnection(HeatmiserConnection):

    def open(self):
        if self.connection is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.connection = s

    def get_response(self):
        try:
            return self.connection.recv(0x10000)
        except Exception as ex:
            self.close()
            raise HeatmiserException('No response from thermostat: %s' % str(ex))

    def update_status(self, dcb):
        self.status = self.protocol.dcb_to_status(dcb)

    def get_status(self):
        # Ensure socket is open
        try:
            self.open()
        except Exception as ex:
            raise HeatmiserException(str(ex))

        cmd = self.protocol.read_dcb_tcp()

        # Send the command to the thermostat
        try:
            self.connection.send(cmd)
        except Exception as ex:
            self.close()
            raise HeatmiserException('Failed to send command to thermostat: %s' % str(ex))

        status = self.protocol.parse_tcp_response(self.get_response())
        self.update_status(status)
