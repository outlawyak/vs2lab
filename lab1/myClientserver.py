"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

    def serve(self):
        """ Serve echo """

        phoneNmbers = {
            "mustermann": 71743,
            "musterfrau": 12345,
            "lustig": 55467,
            "traurig": 11987,
            "mueller": 22387,
            "fischer": 23454
        }


        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    data = data.decode('ascii')
            
                    if not data:
                        break  # stop if client stopped

                    if data == "1":
                        self._logger.info("GET ALL called")
                        byte_data = str(phoneNmbers).encode("ascii") #send all numbers dictionary

                    else:
                        self._logger.info("GET called")
                        normalized_data = data.lower() #make input to lower 
                        byte_data = phoneNmbers[normalized_data].to_bytes(4, byteorder='big') #request data and prepare for send
                        
                    connection.send(byte_data)  # return send number for name in data
                    self._logger.info("Data sent")

                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call_search(self, msg_in):
        """ Search for name- call server """
        self.logger.info("GET called")
        self.sock.send(msg_in.encode('ascii'))  # send encoded string

        data = self.sock.recv(1024)  # receive the response
        msg_out = int.from_bytes(data, byteorder='big')
        print("Number for " + msg_in + ": ")  # print the result
        print(msg_out)
        return msg_out

    def call_all(self, msg_in="1"):
        """ get all numbers- call server """
        self.logger.info("GET ALL called")
        self.sock.send(msg_in.encode('ascii'))  # send a 1 as sign for all 

        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        print(msg_out)  # print the result
        return msg_out

    def close(self):
        """ Close socket """
        self.sock.close()
        self.logger.info("Client down.")
