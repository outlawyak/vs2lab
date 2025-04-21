import constRPC
import threading
import time

from context import lab_channel


class DBList:
    def __init__(self, basic_list):
        self.value = list(basic_list)

    def append(self, data):
        self.value = self.value + [data]
        return self


class Client:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.client = self.chan.join('client')
        self.server = None

    def run(self):
        self.chan.bind(self.client)
        self.server = self.chan.subgroup('server')

    def stop(self):
        self.chan.leave('client')

    def append(self, data, db_list, callback):
        print("Append called with data: {}".format(data))
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server

        ackrcv = self.chan.receive_from(self.server)  # wait for ACK
        print("Data recieved: {}".format(ackrcv))
        if ackrcv == "ACK":
            print("ACK recognized, waiting Thread started: {}",  flush=True)
            background = waitForResponse(self.server, callback)
            background.start()

            while background.is_alive():
                print("Waiting for thread to finish...",  flush=True)
                time.sleep(0.1)

            print("Thread finished, exiting loop.",  flush=True)
            self.stop()

class Server:
    def __init__(self):
        self.chan = lab_channel.Channel()
        self.server = self.chan.join('server')
        self.timeout = 3

    @staticmethod
    def append(data, db_list):
        assert isinstance(db_list, DBList)  # - Make sure we have a list
        return db_list.append(data)

    def run(self):
        self.chan.bind(self.server)
        while True:
            msgreq = self.chan.receive_from_any(self.timeout)  # wait for any request
            if msgreq is not None:
                client = msgreq[0]  # see who is the caller

                # send ACK to Caller
                self.chan.send_to({client}, "ACK")
                # pause server for 10 seconds
                time.sleep(10)

                msgrpc = msgreq[1]  # fetch call & parameters
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, result)  # return response
                else:
                    pass  # unsupported request, simply ignore


class waitForResponse(threading.Thread):
    def __init__(self, chan, server, callback):
        threading.Thread.__init__(self)
        self.chan = chan
        self.server = server
        self.callback = callback

    def run(self):
        print("---------------- asynchronus Thread is waiting..",  flush=True)
        msgrcv = self.chan.receive_from(self.server)
        print("---------------- asynchronus Thread receveid Data: {}".format(msgrcv),  flush=True)
        if self.callback:
            self.callback(msgrcv)
        return msgrcv[1]
