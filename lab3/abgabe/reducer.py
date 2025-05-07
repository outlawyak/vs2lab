import pickle
import re
import sys
import time

import zmq

import constPipe

def getSrc():
    if(me == '1'):
        return constPipe.SRC2
    else:
        return constPipe.SRC3
    
def getPort():
    if(me == '1'):
        return constPipe.PORT2
    else:
        return constPipe.PORT3
    
me = str(sys.argv[1])

src=getSrc()
prt=getPort()
address = "tcp://" + src + ":" + prt #mapper task source

context = zmq.Context()
pull_socket = context.socket(zmq.PULL)  # create a pull socket

pull_socket.bind(address)  # connect to splitter

time.sleep(1) 

print("Reducer {} started".format(me))
wordscount = 0
while True:
    word = pickle.loads(pull_socket.recv())  # receive work mapper
    wordscount +=1
    print(word, ":", wordscount)