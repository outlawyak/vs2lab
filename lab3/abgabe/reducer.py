import pickle
import re
import sys
import time

import zmq

import constPipe

context = zmq.Context()    
me = str(sys.argv[1])

if(me =='1'):
    address = "tcp://127.0.0.1:50012"  #mapper task source
else:
    address = "tcp://127.0.0.1:50013"

pull_socket = context.socket(zmq.PULL)  # create a pull socket
pull_socket.bind(address)  # connect to splitter

time.sleep(1) 

print("Reducer {} started".format(me))
wordscount = 0
while True:
    word = pickle.loads(pull_socket.recv())  # receive work mapper
    wordscount +=1
    print(word, ":", wordscount)