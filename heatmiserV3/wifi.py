import datetime
import socket

__author__ = 'Robin Elvin'


"""
    Class to handle Heatmiser WiFi thermostats that use the
    modified V3 protocol
"""
class HeatmiserWiFi(object):
    DEFAULT_OPTIONS = {
        'host': 'heatmiser',
        'port': 8068,
        'pin': 0000
    }

    def __init__(self, host=DEFAULT_OPTIONS['host'], pin=DEFAULT_OPTIONS['pin']):
        self.host = host
        self.pin = pin
        self.socket = None
        self.port = HeatmiserWiFi.DEFAULT_OPTIONS['port']

    @staticmethod
    def w2b(word):
        return [word & 0xff, word >> 8]

    @staticmethod
    def b2w(lsb, msb):
        return lsb + (msb << 8)

    @staticmethod
    def crc16(octets):
        def crc16_4bits(crc, nibble):
            lookup = (0x0000, 0x1021, 0x2042, 0x3063,
                        0x4084, 0x50A5, 0x60C6, 0x70E7,
                        0x8108, 0x9129, 0xA14A, 0xB16B,
                        0xC18C, 0xD1AD, 0xE1CE, 0xF1EF)
            return ((crc << 4) & 0xffff) ^ lookup[(crc >> 12) ^ nibble]

        crc = 0xffff
        for octet in octets:
            crc = crc16_4bits(crc, octet >> 4)
            crc = crc16_4bits(crc, octet & 0x0f)

        return crc

    def open(self):
        if self.socket is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.socket = s

    def close(self):
        self.socket.close()
        self.socket = None

    """ Construct an arbitrary thermostat command """
    def command(self, op, data):
        # Ensure socket is open
        try:
            self.open()
        except Exception as ex:
            raise HeatmiserException(str(ex))

        # Construct the command
        length = 7 + len(data)
        cmd = [op, ]
        cmd.extend(self.w2b(length))
        cmd.extend(self.w2b(self.pin))
        cmd.extend(data)
        cmd.extend(self.w2b(self.crc16(cmd)))

        # Convert the command to binary
        cmd = bytes(cmd)

        # Send the command to the thermostat
        try:
            self.socket.send(cmd)
        except Exception as ex:
            self.close()
            raise HeatmiserException('Failed to send command to thermostat: %s' % str(ex))

    """ Deconstruct an arbitrary thermostat response """
    def response(self):
        # Receive a response from the thermostat
        try:
            rsp = self.socket.recv(0x10000)
        except Exception as ex:
            self.close()
            raise HeatmiserException('No response from thermostat: %s' % str(ex))

        # Split the response into octets
        rsp = list(rsp)

        # Extract interesting fields
        op = rsp[0]
        length = self.b2w(rsp[1], rsp[2])
        data = rsp[3:-2]
        crc = self.b2w(rsp[-2], rsp[-1])

        # Error checking
        if length != len(rsp):
            raise HeatmiserException("Length field mismatch in thermostat response")
        crc_actual = self.crc16(rsp[:-2])
        if crc != crc_actual:
            raise HeatmiserException("CRC incorrect in thermostat response")

        return op, data

    def read_dcb(self, start=0x0000, octets=0xffff):
        # Construct and issue the inquiry command
        data = HeatmiserWiFi.w2b(start)
        data.extend(HeatmiserWiFi.w2b(octets))
        self.command(0x93, data)

        # Read the response
        op, data = self.response()

        #  Perform some basic sanity checks on the response
        if op != 0x94:
            raise HeatmiserException("Unexpected opcode in thermostat response")
        if self.b2w(data[0], data[1]) != start:
            raise HeatmiserException("Start address mismatch in thermostat response")
        length = self.b2w(data[2], data[3])
        if length == 0x0000:
            raise HeatmiserException("Incorrect PIN used")
        if len(data) != length + 4:
            raise HeatmiserException("Incorrect length of thermostat response")

        # Return the DCB portion of the response
        return data[4:]

    def write_dcb(self, items):
        itemdata = [len(items) & 0xff] # Total number of writing items
        for item in items:
            itemdata.extend(HeatmiserWiFi.w2b(item[0])) # Item address
            itemdata.extend(bytes([len(item[1])])) # Number of bytes to be written
            itemdata.extend(item[1]) # Content bytes

        try:
            self.command(0xa3, bytes(itemdata))
        except:
            raise

        op, data = self.response()

        #  Perform some basic sanity checks on the response
        if op != 0x94:
            raise HeatmiserException("Unexpected opcode in thermostat response")
        if self.b2w(data[0], data[1]) != 0:
            raise HeatmiserException("Start address not zero in thermostat response")
        length = self.b2w(data[2], data[3])
        if length == 0x0000:
            raise HeatmiserException("Incorrect PIN used")
        if len(data) != length + 4:
            raise HeatmiserException("Incorrect length of thermostat response")

        # Return the DCB portion of the response
        return data[4:]

    def dcb_to_status(self, dcb):
        # Sanity check the DCB length field
        status = {}
        status['dcblength'] = self.b2w(dcb[0], dcb[1])
        if len(dcb) != status['dcblength']:
            raise HeatmiserException("DCB length mismatch")

        # Device type and version
        lookup = lambda value, names: names.get(value, value)
        status['product'] = {
            'vendor': lookup(dcb[2], {0: 'Heatmiser', 1: 'OEM'}),
            'version': float(dcb[3] & 0x7f) / 10,
            'model': lookup(dcb[4], {0: 'DT', 1: 'DT-E', 2: 'PRT', 3: 'PRT-E', 4: 'PRTHW', 5: 'TM1'})
        }

        # Current date and time
        timebase = 41
        if status['product']['model'] in ('PRTHW', 'TM1'):
            timebase = 44

        status['time'] = datetime.datetime(2000 + dcb[timebase], dcb[timebase+1], dcb[timebase+2], dcb[timebase+4], dcb[timebase+5], dcb[timebase+6])

        # General operating status
        status['enabled'] = dcb[21]
        status['keylock'] = dcb[22]

        # Holiday mode
        holiday = dcb[25:30+1]
        status['holiday'] = {
            'time': datetime.datetime(2000 + holiday[0], holiday[1], holiday[2], holiday[3], holiday[4]),
            'enabled': holiday[5]
        }

        # Fields that only apply to models with thermometers
        if status['product']['model'] != 'TM1':
            # Temperature configuration
            status['config'] = {
                'units': lookup(dcb[5], {0: 'C', 1: 'F'}),
                'switchdiff': dcb[6] / 2,
                'caloffset': self.b2w(dcb[8], dcb[9]),
                'outputdelay': dcb[10],
                'locklimit': dcb[12],
                'sensor': lookup(dcb[13], {0: 'internal', 1: 'remote', 2: 'floor', 3: 'internal + floor', 4: 'remote + floor'}),
                'optimumstart': dcb[14]
            }

        # Run mode
        status['runmode'] = lookup(dcb[23], {0: 'heating', 1: 'frost'})

        # Frost protection
        status['frostprotect'] = {
            'enabled': dcb[7],
            'target': dcb[17]
        }

        # Floor limit
        if status['product']['model'].endswith('-E'):
            status['floorlimit'] = {
                'limiting': dcb[3] >> 7,
                'floormax': dcb[20]
            }

        # Current temperature(s)
        temps = dcb[33:38+1]
        temperature = lambda ts: None if self.b2w(ts[0], ts[1]) == 0xffff else float(self.b2w(ts[0], ts[1])) / 10
        status['temperature'] = {
            'remote': temperature(temps[0:1+1]),
            'floor': temperature(temps[2:3+1]),
            'internal': temperature(temps[4:5+1])
        }

        # Status of heating
        status['heating'] = {
            'on': dcb[40],
            'target': dcb[18],
            'hold': self.b2w(dcb[31], dcb[32])
        }

        # Learnt rate of temperature rise
        status['rateofchange'] = dcb[15]

        # Error code
        status['errorcode'] = lookup(dcb[39], {0: None, 0xe0: 'internal', 0xe1: 'floor', 0xe2: 'remote'})

        # Fields that only apply to models with hot water control
        if status['product']['model'] in ('PRTHW', 'TM1'):
            # Status of hot water
            status['hotwater'] = {
                'on': dcb[43],
                'boost': self.b2w(dcb[31], dcb[32])
            }
            # Away mode
            status['awaymode'] = lookup(dcb[16], {0: 'home', 1: 'away'})

        # Program mode
        status['config']['progmode'] = lookup(dcb[16], {0: '5/2', 1: '7'})

        # Program entries - does not apply to non-programmable thermostats
        if not 'DT' in status['product']['model']:
            # Find the start of the program data
            # Weekday/Weekend or Mon/Tue/Wed/Thu/Fri/Sat/Sun
            days = 2 if status['config']['progmode'] == '5/2' else 7
            progbase = 51 if status['product']['model'] in ('PRTHW', 'TM1') else 48
            if days == 7:
                if 'PRT' in status['product']['model']:
                    progbase += 24
                if status['product']['model'] in ('PRTHW', 'TM1'):
                    progbase += 32

            # Heating comfort levels program
            prog = dcb[progbase:]
            if status['product']['model'].startswith('PRT'):
                status['comfort'] = []
                for day in range(0, days):
                    daydata = []
                    for entry in range(0, 4):
                        if prog[0] < 24:
                            daydata.append({'time': datetime.time(prog[0], prog[1]), 'target': prog[2]})
                        prog = prog[3:]
                    status['comfort'].append(daydata)

            # Hot water control program
            if status['product']['model'].startswith('TM1') or status['product']['model'].startswith('PRTHW'):
                status['timer'] = []
                for day in range(0, days):
                    daydata = []
                    for entry in range(0, 4):
                        if prog[0] < 24:
                            daydata.append({'on': datetime.time(prog[0], prog[1]), 'off': datetime.time(prog[2], prog[3])})
                        prog = prog[4:]
                    status['timer'].append(daydata)

        # TODO rest of dcb

        # Return the decoded status
        return status

    def status_to_text(self, status):
        # Device type and version
        text = []
        text.append("{vendor} {model} version {version}".format(**status['product']))

        # General operating status
        text.append("Thermostat is {state}".format(state='ON' if status['enabled'] else 'OFF'))
        if status['keylock']:
            text.append("Keylock active")
        text.append("Time: {time}".format(time=status['time']))

        # Holiday mode
        if status['holiday']['enabled']:
            text.append("Holiday until {time}".format(time=status['holiday']['time']))

        # Current temperature(s)
        units = "deg {units}".format(units=status['config']['units'])
        temperatures = ["{temp} {units} ({sensor})".format(temp=status['temperature'][_sensor], units=units, sensor=_sensor) for _sensor in ('internal', 'floor', 'remote') if status['temperature'][_sensor] is not None]
        if len(temperatures) > 0:
            text.append("Temperature " + ', '.join(temperatures))
        if status.get('floorlimit', {}).get('limiting', False):
            text.append("(floor limit active")
        if status['config']['caloffset']:
            text.append("Calibration offset {caloffset}".format(caloffset=status['config']['caloffset']))
        if status['errorcode']:
            text.append("Error with {errorcode} sensor".format(caloffset=status['errorcode']))

        # Status of heating
        line = ''
        if status['heating']['target']:
            line = "Target {target} {units}".format(target=status['heating']['target'], units=units)
        if status['heating']['hold']:
            line += " hold for {minutes} minutes".format(minutes=status['heating']['hold'])
        text.append(line)
        line = ''
        if status['heating']['on'] is not None:
            line = "Heating is {heating}".format(heating='ON' if status['heating']['on'] else 'OFF')
        if status['runmode']:
            line += " ({runmode} mode)".format(runmode=status['runmode'])
        text.append(line)

        # Status of hot water
        line = ''
        if status.get('hotwater', {}).get('on', None) is not None:
            line = "Hot water is {water}".format(water='ON' if status['hotwater'] else 'OFF')
        if status.get('hotwater', {}).get('boost', False):
            line += " boost for {boost} minutes".format(boost=status['hotwater']['boost'])
        if status.get('enabled', False) and status.get('awaymode', False):
            line += " ({awaymode} mode)".format(awaymode=status['awaymode'])
        text.append(line)

        # Feature table
        features = [
            # Features 01 to 05 apply to all models
            ['Temperature format', status['config']['units']],
            ['Switching differential', status['config']['switchdiff'], units],
            ['Frost protect', status['frostprotect']['enabled']],
            ['Frost temperature', status['frostprotect']['target'], units],
            ['Output delay', status['config']['outputdelay'], 'minutes'],
            # Feature 06 on non-RF models or 06 to 10 on RF models
            ['Comms #', 'n/a'],
            # Feature 07 on non-RF models or 11 on RF models
            ['Temperature limit', status['config']['locklimit'], units]
        ]
        if status.get('comfort', False) or status.get('timer', False):
            features.extend(
                [
                    # Features 08 to 12 on non RF or 12 to 16 on RF models, excludes DT-TS
                    ['Sensor selection', status['config']['sensor']],
                    ['Floor limit', status.get('floorlimit', {'floormax': None})['floormax'], units],
                    ['Optimum start', status['config'].get('optimumstart', 'disabled'), 'hours'],
                    ['Rate of change', status['rateofchange'], 'minutes / deg C'],
                    ['Program mode', status['config']['progmode'], 'day'],
                ]
            )

        index = 1
        index2 = 1
        for feature in features:
            if index == 6:
                index2 += 4
            desc = feature[0]
            value = feature[1]
            if len(feature) == 2:
                _units = ''
            elif len(feature) == 3:
                _units = feature[2]
            if value is None:
                value = "n/a"
                _units = ''
            text.append("Feature {:02d} ({:02d}): {:<23} {:>3} {}".format(index, index2, desc, value, _units))
            index += 1
            index2 += 2

        # Program entries
        days = ('Weekday', 'Weekend') if status['config']['progmode'] == '5/2' else ('Monday', 'Tuesday', 'Wednesday',
                                                                                     'Thursday', 'Friday', 'Saturday',
                                                                                     'Sunday')
        hhmm = lambda tm: "{:%H:%M}".format(tm)
        for index in range(len(days)):
            comfort = map(lambda c: "{} {} {}".format(hhmm(c['time']), c['target'], units), status['comfort'][index])
            timer = map(lambda c: "{}-{}".format(hhmm(c['on']), hhmm(c['off'])), status['timer'][index] if status.get('timer', False) else [])

            entry = 1
            for c in comfort:
                _timer = timer[entry-1] if len(timer) >= entry else ''
                text.append("{:<9} {}: {:<14}  {}".format('' if entry > 1 else days[index], entry, c, _timer))
                entry += 1

        return '\n'.join(text)
