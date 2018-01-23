from heatmiserV3 import heatmiser, connection

IP_ADDRESS="192.168.1.57"
PORT="100"

con = connection.connection(IP_ADDRESS, PORT)

con.open()

andy = heatmiser.hmReadAddress(1,'prt',con)

print(andy)

con.close()