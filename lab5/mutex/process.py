import logging
import random
import time

from constMutex import *
from functools import cmp_to_key

class Process:
    """
    Implements access management to a critical section (CS) via fully
    distributed mutual exclusion (MUTEX).

    Processes broadcast messages (ENTER, ALLOW, RELEASE) timestamped with
    logical (lamport) clocks. All messages are stored in local queues sorted by
    logical clock time.

    Processes follow different behavioral patterns. An ACTIVE process competes 
    with others for accessing the critical section. A PASSIVE process will never 
    request to enter the critical section itself but will allow others to do so.

    A process broadcasts an ENTER request if it wants to enter the CS. 
    - A process that doesn't want to ENTER replies with an ALLOW broadcast. 
    - A process that wants to ENTER and receives another ENTER request replies with an ALLOW broadcast (which is then later in time than its own ENTER request).

    A process enters the CS if 
    a) its ENTER message is first in the queue (it is the oldest pending message) AND 
    b) all other processes have sent messages that are younger (either ENTER or ALLOW). 
    
    RELEASE requests purge (delete) corresponding ENTER requests from the top of the local queues. (Take back request)

    Message Format:

    <Message>: (Timestamp, Process_ID, <Request_Type>)

    <Request Type>: ENTER | ALLOW  | RELEASE

    """
   

    def __init__(self, chan):
        self.channel = chan  # Create ref to actual channel
        self.process_id = self.channel.join('proc')  # Find out who you are
        self.all_processes: list = []  # All procs in the proc group
        self.other_processes: list = []  # Needed to multicast to others
        self.queue = []  # The request queue list
        self.clock = 0  # The current logical clock
        self.peer_name = 'unassigned'  # The original peer name
        self.peer_type = 'unassigned'  # A flag indicating behavior pattern
        self.logger = logging.getLogger("vs2lab.lab5.mutex.process.Process")
        self.timeout_counts = {} #counts the timeouts 


    def __mapid(self, id='-1'):
        # format channel member address
        if id == '-1':
            id = self.process_id
        return 'Proc-'+str(id)

    # sort the queue for timestamps after adding a new request  ---------------------------------------------------
    def __cleanup_queue(self):
        if len(self.queue) > 0:
            # self.queue.sort(key = lambda tup: tup[0])
            self.queue.sort()
            # There should never be old ALLOW messages at the head of the queue
            while self.queue[0][2] == ALLOW:
                del (self.queue[0])
                if len(self.queue) == 0:
                    break

    def __remove_peer_messages(self, crashed_peer_id):
        self.queue = [msg for msg in self.queue if msg[1] != crashed_peer_id]
        print(f"{self.__mapid()} removed messages from crashed peer {self.__mapid(crashed_peer_id)}.")

    # send request to enter ----------------------------------------------------------------------------------------
    def __request_to_enter(self):
        self.clock = self.clock + 1  # Increment clock value
        request_msg = (self.clock, self.process_id, ENTER)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

    # allow ENTER for another request ---------------------------------------------------------------------------------------------------------------
    def __allow_to_enter(self, requester):
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, ALLOW)
        self.channel.send_to([requester], msg)  # Permit other

    # when leaving the CS, remove entry from queue ---------------------------------------------------------------------------------------------------------------
    def __release(self):
        # need to be first in queue to issue a release
        assert self.queue[0][1] == self.process_id, 'State error: inconsistent local RELEASE'

        # construct new queue from later ENTER requests (removing all ALLOWS)
        tmp = [r for r in self.queue[1:] if r[2] == ENTER]
        self.queue = tmp  # and copy to new queue
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, self.process_id, RELEASE)
        # Multicast release notification
        self.channel.send_to(self.other_processes, msg)

    # removes request from a timeouted process at head and adds later -------------------------------------------------------------------------
    def __timeout_reintegrate_process(self, peer_to_release):
        # need to be first in queue to issue a release
        assert self.queue[0][1] == peer_to_release, 'State error: inconsistent local RELEASE'

        # construct new queue from later ENTER requests (removing all ALLOWS)
        tmp = [r for r in self.queue[1:] if r[2] == ENTER]
        self.queue = tmp  # and copy to new queue
        self.clock = self.clock + 1  # Increment clock value
        msg = (self.clock, peer_to_release, RELEASE)
        # Multicast release notification
        self.channel.send_to(self.other_processes, msg)

        self.clock = self.clock + 1  # Increment clock value
        request_msg = (self.clock, peer_to_release, ENTER)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

        print("Reintegrate {} later; Queue: {}".format(peer_to_release, self.queue))

    # received allow enter ---------------------------------------------------------------------------------------------------------------
    def __allowed_to_enter(self):
        
        if(len(self.queue) == 0):
            return True

        if self.queue[0][2] == TIMEOUT:
            del(self.queue[0])

        # See who has sent a message (the set will hold at most one element per sender)
        processes_with_later_message = set([req[1] for req in self.queue[1:]])
        # Access granted if this process is first in queue and all others have answered (logically) later
        first_in_queue = self.queue[0][1] == self.process_id
        all_have_answered = len(self.other_processes) == len(
            processes_with_later_message)
        
        return first_in_queue and all_have_answered

    # receive messages ---------------------------------------------------------------------------------------------------------------
    def __receive(self):
        # Pick up any message
        _receive = self.channel.receive_from(self.other_processes, 3)
        if _receive:
            msg = _receive[1]

            self.clock = max(self.clock, msg[0])  # Adjust clock value...
            self.clock = self.clock + 1  # ...and increment

            self.logger.debug("{} received {} from {}.".format(
                self.__mapid(),
                "ENTER" if msg[2] == ENTER
                else "ALLOW" if msg[2] == ALLOW
                else "RELEASE" if msg[2] == RELEASE
                else "TIMEOUT_STEP" if msg[2] == TIMEOUT_STEP
                else "TIMEOUT"
                , self.__mapid(msg[1])))

            # recieved enter request ---------------------------------------------------------------------------------------------------------------
            if msg[2] == ENTER:
                self.queue.append(msg)  # Append an ENTER request
                # and unconditionally allow (don't want to access CS oneself)
                self.__allow_to_enter(msg[1])
            
            # received allow enter critival section ---------------------------------------------------------------------------------------------------------------
            elif msg[2] == ALLOW:
                self.queue.append(msg)  # Append an ALLOW

            # received release request ---------------------------------------------------------------------------------------------------------------
            elif msg[2] == RELEASE:
                # assure release requester indeed has access (his ENTER is first in queue)
                assert self.queue[0][1] == msg[1] and self.queue[0][2] == ENTER, 'State error: inconsistent remote RELEASE'
                del (self.queue[0])  # Just remove first message

            #Timeout Notice received
            elif msg[2] == TIMEOUT_STEP:
                print("Peer {} received TimeoutStep".format(self.process_id))
                #update own timeout counter
                self.timeout_counts[msg[1]] = self.timeout_counts.get(msg[1], 0) + 1
                print("Timeout counts at peer {}: {}".format(self.process_id, self.timeout_counts))
                
                if self.timeout_counts[msg[1]] >= 3:
                     self.__delprocessFromGroup(msg[1])
                     self.__sendTimeoutNotice(msg[1])
                else:
                    #remove timeout-step and reintegrate request from timeouted process later
                    self.queue = [m for m in self.queue if not (m[1] == msg[1] and m[2] == TIMEOUT_STEP)]

                    #if timeouted process request at head of queue
                    if self.queue[0][1] == msg[2]:
                        self.__timeout_reintegrate_process(msg[2])


            elif msg[2] == TIMEOUT:
            
                self.queue = [m for m in self.queue if m[1] != msg[1]]
                #delete Timeouted Process from group
                self.__delprocessFromGroup(msg[1])

            self.__cleanup_queue()  # Finally sort and cleanup the queue
        else:
            
            self.logger.info("{} timed out on RECEIVE. Local queue: {}".
                             format(self.__mapid(),
                                    list(map(lambda msg: (
                                        'Clock '+str(msg[0]),
                                        self.__mapid(msg[1]),
                                        msg[2]), self.queue))))

            processes_with_later_message = set([req[1] for req in self.queue[1:]])

            for peer in self.other_processes:
                if peer not in processes_with_later_message:

                    timeouted_peer = peer
                    print("\nTimeouted Peer {} at peer {}".format(timeouted_peer, self.process_id))
                    
                    #UPDATE OWN TIMEOUT COUNTER
                    self.timeout_counts[timeouted_peer] = self.timeout_counts.get(timeouted_peer, 0) + 1
                    print("Timeout counts at peer {}: {}".format(self.process_id, self.timeout_counts))

                    # # if more than 3 timeouts -> crash (check if already removed)
                    if self.timeout_counts[timeouted_peer] == 3:
                        self.__sendTimeoutNotice(timeouted_peer)
                        self.__delprocessFromGroup(timeouted_peer)
                    elif self.timeout_counts[timeouted_peer] < 3:
                         self.__sendTimeoutStepNotice(timeouted_peer)
                    else:
                        continue

                    
    def __sendTimeoutStepNotice(self, timeouted_peer):
        request_msg = (1, timeouted_peer, TIMEOUT_STEP)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request

    def __sendTimeoutNotice(self, peer_to_delete):
        #send notice for process has to be removed
        request_msg = (0, peer_to_delete, TIMEOUT)
        self.queue.append(request_msg)  # Append request to queue
        self.__cleanup_queue()  # Sort the queue
        self.channel.send_to(self.other_processes, request_msg)  # Send request
    
    def __delprocessFromGroup(self, peer_to_delete):
        #check if already removed
        if peer_to_delete in self.other_processes and peer_to_delete in self.all_processes:
            self.logger.warning(f"Process {self.__mapid(peer_to_delete)} presumed crashed at {self.process_id}. Removing from coordination.")
            self.other_processes.remove(peer_to_delete)
            self.all_processes.remove(peer_to_delete)

        #remove old Timeout Step messages
        if len(self.queue) > 0:
                    while self.queue[0][2] == TIMEOUT_STEP or self.queue[0][2] == TIMEOUT:
                        del (self.queue[0])
                        if len(self.queue) == 0:
                            break
        #reset timeout counts
        self.timeout_counts = {}

    def init(self, peer_name, peer_type):
        self.channel.bind(self.process_id)

        self.all_processes = list(self.channel.subgroup('proc'))
        # sort string elements by numerical order
        self.all_processes.sort(key=lambda x: int(x))

        self.other_processes = list(self.channel.subgroup('proc'))
        self.other_processes.remove(self.process_id)

        self.peer_name = peer_name  # assign peer name
        self.peer_type = peer_type  # assign peer behavior

        self.logger.info("{} joined channel as {}.".format(
            peer_name, self.__mapid()))
    

    # run Process ---------------------------------------------------------------------------------------------------------------
    def run(self):
        while True:
            # Enter the critical section if
            # 1) there are more than one process left and
            # 2) this peer has active behavior and
            # 3) random is true
            if len(self.all_processes) > 1 and \
                    self.peer_type == ACTIVE and \
                    random.choice([True, False]):
                self.logger.debug("{} wants to ENTER Critical Section (CS) at CLOCK {}."
                                  .format(self.__mapid(), self.clock))

                self.__request_to_enter()

                while not self.__allowed_to_enter():
                    self.__receive()

                # recieved allow CS and first in queue ---------------------------------------------------------------------------------------------------------------
                # Stay in CS for some time ...
                sleep_time = random.randint(0, 2000)
                self.logger.debug("{} enters CS for {} milliseconds."
                                  .format(self.__mapid(), sleep_time))
                print(" CS <- {}".format(self.__mapid()))
                time.sleep(sleep_time/1000)

                # ... then leave CS
                print(" CS -> {}".format(self.__mapid()))
                self.__release()
                print("Local queue: {}".
                             format(list(map(lambda msg: (
                                        'Clock '+str(msg[0]),
                                        self.__mapid(msg[1]),
                                        msg[2]), self.queue))))
                continue

            # Occasionally serve requests to enter
            if random.choice([True, False]):
                self.__receive()
