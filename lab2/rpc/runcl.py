import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

def process_response(self, data):
        print("Processing response: {}".format(data),  flush=True)
        if data is not None:
            return data[1]

base_list = rpc.DBList({'foo'})
result_list = cl.append('bar', base_list, process_response)
result_list = cl.append('goo', base_list, process_response)
result_list = cl.append('haa', base_list, process_response)


#print("Result: {}".format(result_list.value))
