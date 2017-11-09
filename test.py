from heatmiserV3 import heatmiser, connection

con = connection.HeatmiserConnection(address="192.168.1.57", port="102")

i = 1
while i < 5:
    result = heatmiser.hmReadAddress(i, 'prt', con.serport) 
    print(result['address'])
    i = i + 1

print(result)
    

con.close()
