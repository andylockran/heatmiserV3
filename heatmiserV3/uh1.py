import threading
from queue import Queue
import time, random
from heatmiserV3 import connection
from heatmiserV3 import heatmiser

WORKERS = 4

class Worker(threading.Thread):

    def __init__(self, q1):
        self.__q1 = q1
        threading.Thread.__init__(self)
        self.__serport = connection.connection('192.168.1.57','916')

    def run(self):
        while 1:
            item = self.__q1.get()
            if item is None:
                break # reached end of queue

            # pretend we're doing something that takes 10-100 ms
            #time.sleep(random.randint(10, 100) / 1000.0)
            if item['rw'] == 'r':
              self.__serport.open()
              dcb = heatmiser.hmReadAddress(item['thermid'],item['type'],self.__serport)
              print(dcb)
              self.__serport.close()
            print("task", item['i'], "finished")

#
# try it

q1 = Queue()

for i in range(WORKERS):
    Worker(q1).start() # start a worker

for i in range(4):
    thermid = i+1
    rw = 'r'
    type = 'prt'
    item = {'i':i,'thermid': thermid,'rw': rw,'type':'type'}
    q1.put(item)

for i in range(WORKERS):
    q1.put(None) # add end-of-queue markers
