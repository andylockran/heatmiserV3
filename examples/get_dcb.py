from heatmiserV3 import heatmiser

IP_ADDRESS="192.168.1.57"
PORT="100"

con = heatmiser.HeatmiserSerialConnection(IP_ADDRESS, PORT).conn.port

andy = heatmiser.hmReadAddress(1,'raw',con)

print(andy)

con.close()