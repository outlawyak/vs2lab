import pickle
import random
import sys
import time

import random
import zmq

import constPipe

subjects = ["Die Katze", "Ein Hund", "Der Lehrer"]
verbs = ["läuft", "schläft", "programmierte"]
objects = ["im Park", "ein Sandwich", "Python"]

def generate_sentence():
    subject = random.choice(subjects)
    verb = random.choice(verbs)
    obj = random.choice(objects)
    return f"{subject} {verb} {obj}."

context = zmq.Context()
push_socket = context.socket(zmq.PUSH)  # create a push socket

address = "tcp://127.0.0.1:50011" # how and where to connect
push_socket.bind(address)  # bind socket to address

time.sleep(1) # wait to allow all clients to connect

for i in range(20):  # generate 100 workloads
    sentence = generate_sentence()
    print(sentence)
    push_socket.send(pickle.dumps(sentence))  # send workload to worker
    push_socket.send(pickle.dumps("-------------------------------------------------------"))