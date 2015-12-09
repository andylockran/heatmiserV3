import serial

def connection(ipaddress,port):
	serport = serial.serial_for_url("socket://"+ipaddress+":"+port+"/logging=debug")
	serport.close()
	#serport.port = heatmiserV3.constants.COM_PORT
	serport.baudrate = heatmiserV3.constants.COM_BAUD
	serport.bytesize = heatmiserV3.constants.COM_SIZE
	serport.parity = heatmiserV3.constants.COM_PARITY
	serport.stopbits = heatmiserV3.constants.COM_STOP
	serport.timeout = heatmiserV3.constants.COM_TIMEOUT
	try:
	    serport.open()
	except serial.SerialException as e:
	        s= "%s : Could not open serial port %s: %s\n" % (localtime, serport.portstr, e)
	        sys.stderr.write(s)
	        problem += 1
	serport.close()
	return serport
