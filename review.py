import heatmiserV3

serport = heatmiserV3.connection.connection('192.168.1.155','916')

serport.open()

heatmiserV3.heatmiser.hmReadAddress(5,'tm1',serport)
