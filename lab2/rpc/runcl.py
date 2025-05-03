import time
import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})

def result_callback(result):
    print("Ergebnis empfangen: {}".format(result.value))

cl.append('bar', base_list, result_callback)

for x in range (11):
    print("Client schreibt etwas", x)
    time.sleep(1)


#time.sleep(12)
cl.stop()
