import asyncio
import math
from hashlib import sha1
import logging
import pickle

log=logging.getLogger()

class NodeCannotJoin(Exception):
    pass

class Client():
    def __init__(self) -> None:
        self.connections={}

    async def send(self,ip,port,message):
#        if isinstance(message,)
        if (ip,port) in self.connections:
            reader, writer = self.connections[(ip,port)]
        else:
            reader, writer = await self.connect()

        log.debug(f'Sending: {message}')
        timeouts=0
        while True:
            try:
                writer.write(pickle.dumps(message))
                break
            except asyncio.TimeoutError:
                del self.connections[(ip,port)]
                raise Exception("Timeout while client writes!")
            except Exception as e: # TODO find the exception thrown
                log.debug(e)
                break
                

        data = await reader.read()
        log.debug(f'Received: {pickle.loads(data)}')
        return data
        

    async def connect(self,ip,port):
        reader, writer = await asyncio.open_connection(ip, port)
        self.connections[(ip,port)]=(reader,writer)
        return reader, writer