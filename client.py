import asyncio
import math
from hashlib import sha1
import logging
import pickle
import utils
import settings

log = logging.getLogger()


class NodeCannotJoin(Exception):
    pass

MESSAGE_SEPERATOR = b'#'

class Client():
    __instance = None

    @staticmethod
    def getInstance(bootstrap=None, bootstrap_id=-1):
        if Client.__instance == None:
            # raise Exception("Client should be initialized properly before")
           Client(bootstrap, bootstrap_id) # This should not be called first
        return Client.__instance

    def __init__(self, bootstrap, bootstrap_id) -> None:
        if Client.__instance != None:
            raise Exception("This class is a singleton")
        else:
            self.connections = {}
            self.bootstrap=bootstrap
            self.routes = {bootstrap_id: bootstrap}
            Client.__instance = self

    @asyncio.coroutine
    def send(self, message, ip=None, port=settings.CHORD_PORT, destination=None): 
        # Provide either ip and port or destination
        if(ip and port):
            self.routes[utils.get_node_id(ip)] = ip
        else:
            if destination in self.routes:
                ip=self.routes[destination]
            else:
                # May cause problems but a way to guarantee sending requests to networks
                ip=self.bootstrap
        reader, writer = yield from asyncio.open_connection(ip, port)
        log.debug(f'Sending: {message}')
        writer.write(pickle.dumps(message) + MESSAGE_SEPERATOR)
        yield from writer.drain()
        log.debug(f'Sent!')
        data = yield from reader.readuntil(MESSAGE_SEPERATOR)
        writer.close()
        data=pickle.loads(data[:-1])
        log.debug(f'Received: {data}')
        return data

