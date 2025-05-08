""" 
Chord Application
- defines a DummyChordClient implementation
- sets up a ring of chord_node instances
- Starts up a DummyChordClient
- nodes and client run in separate processes
- multiprocessing should work on unix and windows
"""

import logging
import sys
import multiprocessing as mp
import time

import chordnode as chord_node
import constChord
from context import lab_channel, lab_logging

import random
from random import randint

lab_logging.setup(stream_level=logging.INFO)


class DummyChordClient:
    """A dummy client template with the channel boilerplate"""

    def __init__(self, channel):
        self.channel = channel
        self.node_id = channel.join('client')

    def enter(self):
        self.channel.bind(self.node_id)

    def run(self):
          	
        # Randomly select a node from the channel and a random key to lookup
        rand_node = random.choice([node.decode() for node in list(self.channel.channel.smembers('node'))])
        rand_key = randint(0, self.channel.MAXPROC)
        time.sleep(1)  # wait for a while to let the nodes join the channel
        
        ## Print the selected node and key
        print("\n###### INITIAL REQUEST: NODE " + self.node_id + " SENTS REQ TO NODE " + str(rand_node) +  " FOR KEY " + str(rand_key) + "\n")
        self.sendRequest(rand_node, rand_key)

        # Wait for a response and print the responsible node
        responsible_node = self.channel.receive_from([rand_node])[1][1]
        print("\n###### NODE " + str(responsible_node) + " IS RESPONSIBLE FOR KEY " + str(rand_key))

        self.channel.send_to(  # a final multicast
            {node.decode() for node in list(self.channel.channel.smembers('node'))},
            constChord.STOP)
        
    def sendRequest(self, node_id, key):
        self.channel.send_to([node_id], (constChord.LOOKUP_REQ, key, self.node_id))


def create_and_run(num_bits, node_class, enter_bar, run_bar):
    """
    Create and run a node (server or client role)
    :param num_bits: address range of the channel
    :param node_class: class of node
    :param enter_bar: barrier syncing channel population 
    :param run_bar: barrier syncing node creation
    """
    chan = lab_channel.Channel(n_bits=num_bits)
    node = node_class(chan)
    enter_bar.wait()  # wait for all nodes to join the channel
    node.enter()  # do what is needed to enter the ring
    run_bar.wait()  # wait for all nodes to finish entering
    node.run()  # start operating the node


if __name__ == "__main__":  # if script is started from command line
    m = 6  # Number of bits for linear names
    n = 8  # Number of nodes in the chord ring

    # Check for command line parameters m, n.
    if len(sys.argv) > 2:
        m = int(sys.argv[1])
        n = int(sys.argv[2])

    # Flush communication channel
    chan = lab_channel.Channel()
    chan.channel.flushall()

    # we need to spawn processes for support of windows
    mp.set_start_method('spawn')

    # create barriers to synchronize bootstrapping
    bar1 = mp.Barrier(n+1)  # Wait for channel population to complete
    bar2 = mp.Barrier(n+1)  # Wait for ring construction to complete

    # start n chord nodes in separate processes
    children = []
    for i in range(n):
        nodeproc = mp.Process(
            target=create_and_run,
            name="ChordNode-" + str(i),
            args=(m, chord_node.ChordNode, bar1, bar2))
        children.append(nodeproc)
        nodeproc.start()

    # spawn client proc and wait for it to finish
    clientproc = mp.Process(
        target=create_and_run,
        name="ChordClient",
        args=(m, DummyChordClient, bar1, bar2))
    clientproc.start()
    clientproc.join()

    # wait for node processes to finish
    for nodeproc in children:
        nodeproc.join()