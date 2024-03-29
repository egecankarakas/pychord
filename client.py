import asyncio
import logging
import math
import pickle
from hashlib import sha1

import settings
import utils

log = logging.getLogger()


class NodeConnectionError(Exception):
    pass


MESSAGE_SEPERATOR = b'#'


class ClientProtocol(asyncio.Protocol):
    def __init__(self, message, result, on_conn_lost):
        self.message = message
        self.result = result
        self.on_conn_lost = on_conn_lost
        self.transport = None

    def connection_made(self, transport):
        log.debug('Connection made!')
        # print(f'About to send {self.message}')
        transport.write(pickle.dumps(self.message))
        # print(f'Data sent: {self.message}')

    def data_received(self, data):
        self.result.set_result(pickle.loads(data))

    def connection_lost(self, exc):
        log.debug('The server closed the connection')
        log.debug('Stop the event loop')
        log.debug(exc)
        self.on_conn_lost.set_result(True)
        # self.loop.stop()

class Client():
    __instance = None

    @staticmethod
    def getInstance(bootstrap=None, bootstrap_id=-1):
        if Client.__instance == None:
            # raise Exception("Client should be initialized properly before")
            Client(bootstrap, bootstrap_id)  # This should not be called first
        return Client.__instance

    def __init__(self, bootstrap, bootstrap_id) -> None:
        if Client.__instance != None:
            raise Exception("This class is a singleton")
        else:
            self.connections = {}
            self.bootstrap = bootstrap
            self.routes = {bootstrap_id: bootstrap}
            self.loop = asyncio.get_event_loop()
            Client.__instance = self

    async def send(self, message, ip=None, port=settings.CHORD_PORT, destination=None):
        log
        # Provide either ip and port or destination
        if(ip and port):
            self.routes[utils.get_node_id(ip)] = ip
        else:
            if destination in self.routes:
                ip = self.routes[destination]
            else:
                # May cause problems but a way to guarantee sending requests to networks
                ip = self.bootstrap
        log.debug(f'Sending: {message}')
        loop = asyncio.get_event_loop()
        result = loop.create_future()
        on_con_lost = loop.create_future()

        coro = loop.create_connection(lambda: ClientProtocol(
            message, result, on_con_lost), ip, port)

        # Wait until the protocol signals that the connection
        # is lost and close the transport.
        try:
            await coro
            result = await result
            await on_con_lost
        except Exception as e:
            log.debug(e)
            raise(NodeConnectionError)
        finally:
            # transport.close()
            pass

        #result = asyncio.gather(loop.create_task(loop.create_connection(lambda: ClientProtocol(pickle.dumps(message), loop),ip,settings.CHORD_PORT)))
        log.debug(f'Received: {result}')
        return result
