import pickle
import re
import sys
import time

import zmq

import constPipe

me = str(sys.argv[1])
context = zmq.Context()

#Socket to receive messages on
address ="tcp://127.0.0.1:50011"  # splitter task src
pull_socket = context.socket(zmq.PULL)  # create a pull socket
pull_socket.connect(address)  # connect to splitter

# Socket to send messages to
address1 ="tcp://127.0.0.1:50012"
address2 ="tcp://127.0.0.1:50013"

push_socket1 = context.socket(zmq.PUSH)  # create a push socket
push_socket2 = context.socket(zmq.PUSH)  # create a push socket

push_socket1.connect(address1)  # bind socket to reducer 1
push_socket2.connect(address2)  # bind socket to reducer 2

time.sleep(1) 

print("Mapper {} started".format(me))

while True:
    sentence = pickle.loads(pull_socket.recv())  # receive work from a source
    print(sentence)
    words = re.findall(r'\b\w+\b', sentence)
    for w in words:
        if "e" in w:
            push_socket1.send(pickle.dumps(w))
        else:
            push_socket2.send(pickle.dumps(w))

