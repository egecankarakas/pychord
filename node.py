import os
import asyncio
import pickle
import settings
import logging
import socket
import time

from base_node import BaseNode
from client import Client
import operations as op
from remote_node import RemoteNode
from utils import arc_contains, get_node_id


class HostnameFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True

MESSAGE_SEPERATOR = b'#'

handler = logging.StreamHandler()
handler.addFilter(HostnameFilter())
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
log = logging.getLogger('Chord')
log.addHandler(handler)


class Node(BaseNode):
    def __init__(self, ip, bootstrap_server=None) -> None:
        super().__init__(ip)
        self.task_update_periodically = None
        self.bootstrap_server = bootstrap_server
        self.joined = False
        self.op_func_map = {
            op.FIND_SUCCESSOR: self.find_successor,
        }
        self.predecessor = None
        self.successor = None
        self.loop = None
        self.is_first_node = True

    async def run(self, loop):
        self._server = await asyncio.start_server(self.handle, self.ip, settings.CHORD_PORT, loop=loop)
        self.loop=loop
        while True:
            self.task_update_periodically = loop.create_task(
                self.update_periodically())
            await self.task_update_periodically

    async def update_periodically(self):
        log.info('Started Updating Periodically!')
        if not self.joined:
            if self.bootstrap_server:
                log.info('Joining Chord Ring!')
                await self.join()
                self.joined=True
                Client(bootstrap=self.bootstrap_server,bootstrap_id=get_node_id(self.bootstrap_server))
            else:
                self.successor = self
                self.predecessor = self
                self.fingers = [self]*settings.NETWORK_SIZE
                log.info('Waiting for others to join the ring!')
                time.sleep(1)
        log.debug('Stabilizing')
        time.sleep(1)
        # pass
    


    async def stop(self):
        if self.task_update_periodically:
            self.task_update_periodically.close()

    @asyncio.coroutine
    def handle(self, stream_reader, stream_writer):
        log.debug(f'Handle is called')
        msg = yield from stream_reader.readuntil(MESSAGE_SEPERATOR)
        log.debug(f'Message is {msg[:-1]}')
        msg = pickle.loads(msg[:-1])
        op_code = msg.pop('op')
        try:
            result = yield from self.op_func_map[op_code](**msg)
        except KeyError as e:
            log.debug(e)
        stream_writer.write(pickle.dumps(result)+MESSAGE_SEPERATOR)
        yield from stream_writer.drain()

        log.debug('Closing the client socket!')
        stream_writer.close()

    async def join(self):
        if(self.bootstrap_server):  # There are other nodes, should join
            bootstrap_node = RemoteNode(self.bootstrap_server)
            await self.init_finger_table(bootstrap_node)
            await self.update_others()
            # Move keys here if necesary
        else:
            self.fingers[0] = self

    async def init_finger_table(self, node: RemoteNode):
        self.successor = await node.find_successor(self.fingers[0].nid)
        log.debug(f'Successor:{self.successor}')
        self.fingers[0] = self.successor
        self.predecessor = None

    async def update_others():
        pass

    async def notify(self, bag):
        # node_id thinks that is my predecessor
        if not self.predecessor or arc_contains(self.predecessor.nid,self.nid,bag['node_id']):
            log.debug(bag)
            self.predecessor = bag['node'] # TODO: Control it

    async def find_successor(self, node_id):
        log.debug(f'Finding Successor of {node_id}')
        node = await self.find_predecessor(node_id)
        log.debug(f'Successor of {node_id} is {node.successor}')
        if not node.successor:
            return self.to_dict()
        else:
            return node.successor.to_dict()

    async def find_predecessor(self, node_id):
        log.debug(f'Finding Predecessor of {node_id}')
        node_prime = self
        while not arc_contains(node_prime.nid, node_prime.successor.nid, node_id, end_included=True):
            node_prime = await node_prime.closest_preceding_finger(node_id)
        return node_prime

    async def closest_preceding_finger(self, node_id):
        log.debug(
            f'Node({self.nid}) Finding Closest preceding finger of {node_id}')
        for i in range(settings.NETWORK_SIZE-1, -1, -1):
            if arc_contains(self.nid, node_id, self.fingers[i].nid):
                return self.fingers[i]
        return self


# class RemoteNode(BaseNode):
#     def __init__(self, ip) -> None:
#         super().__init__(ip)
#         self.client=None

#     # async def init_finger_table(self, arbitrary_node):
#     #     message={'op':op.INIT_FINGER_TABLE,}
#     #     if not self.client:
#     #         self.client = Client()
#     #     self.client.send(self.bootstrap_server,self.port,)

#     async def get_client(self):
#         if self.client:
#             return self.client
#         else:
#             self.client = Client()

#     async def find_successor(self,node_id):
#         log.debug(f'Requesting Node {self.nid} to find successor of {node_id}')
#         node = self.get_client().send(self.ip,self.port,{'op':op.FIND_SUCCESSOR,'node_id':node_id})
#         return node

#     async def find_predecessor(self,node_id):
#         log.debug(f'Requesting Node {self.nid} to find Predecessor of {node_id}')
#         node_prime = self
#         while not arc_contains(node_prime.nid,node_prime.successor.nid,node_id,end_included=True):
#             node_prime = node_prime.closest_preceding_finger(node_id)
#         return node_prime

#     async def closest_preceding_finger(self,node_id):
#         log.debug(f'Requesting Node {self.nid} to find Closest preceding finger of {node_id}')
#         for i in range(settings.NETWORK_SIZE-1,-1,-1):
#             if arc_contains(self.nid,node_id,self.fingers[i].nid):
#                 return self.fingers[i]
#         return self
