import threading
import time
import constRPC

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
        assert isinstance(db_list, DBList)
        msglst = (constRPC.APPEND, data, db_list)  # message payload
        self.chan.send_to(self.server, msglst)  # send msg to server
        # bis hierhin gleich, nachricht wird versendet
        # auf Ack warten und zurückgeben
        ackrcv = self.chan.receive_from(self.server)  # wait for response (ACK)
        #print(ackrcv)
        if ackrcv[1] == 'ACK':
            print("Ack erhalten")
            background = WaitForResult(self.chan, self.server, callback)
            background.start()
            print("Warte auf Antwort")
            
            #background.join
            
        else:
            print("kein ACK erhalten")
           


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
                self.chan.send_to({client},"ACK")  # return ACK
                time.sleep(10)
                msgrpc = msgreq[1]  # fetch call & parameters
                
                if constRPC.APPEND == msgrpc[0]:  # check what is being requested
                    result = self.append(msgrpc[1], msgrpc[2])  # do local call
                    self.chan.send_to({client}, result)  # return response
                    print(result)
                else:
                    pass  # unsupported request, simply ignore

class WaitForResult(threading.Thread):
    def __init__(self,chan, server, callback):
        threading.Thread.__init__(self)
        self.server= server
        self.callback = callback 
        self.chan = chan            # Kanal, um Ergebnis zu empfangen

    def run(self):
        print("Client wartet auf Ergebnis")
        result_msg = self.chan.receive_from(self.server)
        self.callback(result_msg[1])