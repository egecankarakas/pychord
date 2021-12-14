import asyncio
import math
from hashlib import sha1
import logging
import pickle

log = logging.getLogger()


class NodeCannotJoin(Exception):
    pass


class Client():
    def __init__(self) -> None:
        self.connections = {}

    async def send(self, ip, port, message):
        reader, writer = await asyncio.open_connection(ip, port)
        log.debug(f'Sending: {message}')
        writer.write(pickle.dumps(message))
        log.debug(f'Sent!')
        data = await reader.read()
        log.debug(f'Received: {pickle.loads(data)}')
        return data
