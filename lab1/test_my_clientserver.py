"""
Simple client server unit test
"""

import logging
import threading
import unittest

import myClientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = myClientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)  # define thread for running server

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = myClientserver.Client()  # create new client for each test

    def test_srv_get_mustermann(self):
        msg = self.client.call_search("mustermann")
        self.assertEqual(msg, 71743)

    def test_srv_get_fischer(self):  # each test_* function is a test
       msg = self.client.call_search("FiScher")
       self.assertEqual(msg, 23454)

    def test_srv_get_all(self):
        msg = self.client.call_all()
        self.assertEqual(msg, "{'mustermann': 71743, 'musterfrau': 12345, 'lustig': 55467, 'traurig': 11987, 'müller': 22387, 'fischer': 23454}")

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
