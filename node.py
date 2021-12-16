import os
import asyncio
import pickle
import settings
import logging
import socket
import time
import random

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

# handler = logging.StreamHandler()
# # handler.addFilter(HostnameFilter())
# handler.setFormatter(logging.Formatter(
#     '%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
log = logging.getLogger('Chord')
# log.addHandler(handler)


class Node(BaseNode):
    def __init__(self, ip, bootstrap_server=None) -> None:
        super().__init__(ip)
        self.task_update_periodically = None
        self.bootstrap_server = bootstrap_server
        self.joined = False
        self.op_func_map = {
            op.FIND_SUCCESSOR: self.find_successor,
            op.UPDATE_FINGER_TABLE: self.update_finger_table,
            op.NOTIFY: self.notify,
            # op.IS_ALIVE: self.is_alive
        }
        self.predecessor = None
        self.successor = None
        self.loop = None
        self.is_first_node = True

    async def run(self, loop):
        self._server = await asyncio.start_server(self.handle, self.ip, settings.CHORD_PORT, loop=loop)
        self.loop = loop
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
                self.joined = True
                # Client(bootstrap=self.bootstrap_server,bootstrap_id=get_node_id(self.bootstrap_server))
            else:
                # When you are all alone in the network
                self.successor = self
                self.predecessor = self
                # self.fingers = [self]*settings.NETWORK_SIZE
                log.info('Waiting for others to join the ring!')
                time.sleep(1)
        log.debug('Stabilizing')
        await self.stabilize()
        await self.fix_fingers()
        time.sleep(1)
        # pass
        log.debug(f'Logging Node {self.nid}: ')
        log.debug(self.to_bag())

    async def fix_fingers(self):
        # This will eventually fix fingers, and so predecessors and successors
        i = random.randint(1, settings.NETWORK_SIZE-1)
        if self.successor:
            successor_bag = await self.successor.find_successor({'node_id': self.fingers[i].start})
        else:
            bootstrap_node = RemoteNode(self.bootstrap_server)
            successor_bag = bootstrap_node.find_successor(
                {'node_id': self.fingers[i].start})
        self.fingers[i].node = RemoteNode.from_bag(successor_bag)

    async def stabilize(self):  # -->
        if self.successor:
            x = self.successor.predecessor
            if x and x.nid != self.nid and arc_contains(self.nid, self.successor.nid, x.nid, start_included=True, end_included=True):
                self.successor = x
            if self.successor.nid != self.nid:
                response = await self.successor.notify(self.to_bag())
                log.debug(f"Response: {response}")

    async def stop(self):
        if self.task_update_periodically:
            self.task_update_periodically.close()

    @asyncio.coroutine
    def handle(self, stream_reader, stream_writer):
        log.debug(f'Handle is called')
        msg = yield from stream_reader.readuntil(MESSAGE_SEPERATOR)
        msg = pickle.loads(msg[:-1])
        log.debug(f'Message is {msg}')
        op_code = msg.pop('op')
        response_func = self.op_func_map[op_code]
        try:
            result = yield from asyncio.wait_for(response_func(msg), settings.SERVER_TIMEOUT)
            log.debug(f"response: {result}")
            stream_writer.write(pickle.dumps(result)+MESSAGE_SEPERATOR)
            yield from stream_writer.drain()
        except KeyError as e:
            log.debug(e)
        except asyncio.TimeoutError as e:
            log.debug(f'Timeout Error occurred!')
            log.debug(e)
        finally:
            log.debug('Closing the client socket!')
            if stream_writer:
                stream_writer.close()

    async def join(self):  # -->
        if(self.bootstrap_server):  # There are other nodes, should join
            bootstrap_node = RemoteNode(self.bootstrap_server)
            await self.init_finger_table(bootstrap_node)
            await self.update_others()
            self.joined = True
            # Move keys here if necesary
        else:
            self.fingers[0] = self

    async def init_finger_table(self, node: RemoteNode):  # -->
        successor_bag = await node.find_successor({'node_id': self.fingers[0].start})
        self.successor = RemoteNode.from_bag(successor_bag)
        log.debug(f'Successor:{self.successor}')
        self.fingers[0].node = self.successor
        self.predecessor = self.successor.predecessor if self.successor else None
        for i in range(0, settings.NETWORK_SIZE-1):
            if self.fingers[i].node and arc_contains(self.nid, self.fingers[i].node.nid, self.fingers[i+1].start):
                self.fingers[i+1].node = self.fingers[i].node
            else:
                successor_bag = await node.find_successor({'node_id': self.fingers[i+1].start})
                self.fingers[i+1].node = RemoteNode.from_bag(successor_bag)

    async def update_others(self):  # -->
        # Update all nodes whose finger tables should refer to n
        updated = []
        for i in range(settings.NETWORK_SIZE):
            p = await self.find_predecessor((self.nid - (1 << i)) % (settings.MAX_NODES))
            if p.nid != self.nid and p.nid not in updated:
                await p.update_finger_table({'s': self.nid, 'i': i})
                updated.append(p.nid)

    async def update_finger_table(self, bag):  # <--
        # If s is the i'th finger of n, update n's finger table with s
        i = bag['i']
        s = bag['s']
        ith_finger = self.fingers[i].node
        if arc_contains(start=self.nid, stop=ith_finger.nid, element=s):
            self.fingers[i].node = s
            p = self.predecessor
            if p:
                await p.update_finger_table({'s': s, 'i': i})

    async def notify(self, bag):  # <--
        # node_id thinks that is my predecessor
        self.joined = True
        log.debug(
            f"Node {bag['nid']} thinks that it might be predecessor of {self.nid}")
        if not self.predecessor or arc_contains(self.predecessor.nid, self.nid, bag['nid'], start_included=True, end_included=True):
            log.debug(bag)
            self.predecessor = RemoteNode.from_bag(bag)  # TODO: Control it
            return {'RESPONSE': op.OK_RESPONSE}
        return {'RESPONSE': op.FAIL_RESPONSE}

    async def find_successor(self, bag):  # <--
        node_id = bag['node_id']
        log.debug(f"Finding Successor of {node_id}")
        node = await self.find_predecessor(node_id)
        log.debug(f'Successor of {node_id} is {node.successor.to_bag()}')
        if not node.successor:
            return self.to_bag()
        else:
            return node.successor.to_bag()

    async def find_predecessor(self, node_id):  # <--
        log.debug(f'Finding Predecessor of {node_id}')
        node_prime = self
        while node_prime.successor and not arc_contains(node_prime.nid, node_prime.successor.nid, node_id, end_included=True):
            res_finger = await node_prime.closest_preceding_finger(node_id)
            if res_finger:  # Nodes can be None at the beginning, we check it
                node_prime = res_finger.node
                log.debug(f'New Node Prime: {node_prime.nid}')
        return node_prime

    async def closest_preceding_finger(self, node_id):  # <--
        log.debug(
            f'Node({self.nid}) Finding Closest preceding finger of {node_id}')
        for i in range(settings.NETWORK_SIZE-1, -1, -1):
            if self.fingers[i].node and arc_contains(self.nid, node_id, self.fingers[i].node.nid):
                return self.fingers[i]
        return None


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
