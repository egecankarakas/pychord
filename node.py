import asyncio
import json
import logging
import os
import pickle
import random
import socket
import time
from ctypes import resize

import operations as op
import settings
from base_node import BaseNode
from client import Client
from remote_node import RemoteNode
from utils import arc_contains, get_node_id


class HostnameFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True


handler = logging.StreamHandler()
handler.addFilter(HostnameFilter())
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
log = logging.getLogger('Chord')
log.addHandler(handler)


class EchoServerClientProtocol(asyncio.Protocol):
    _node = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        log.debug('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        try:
            log.debug('Data received in server')
            log.debug(data)
            self.data = pickle.loads(data)
            log.debug(f'Data is:{self.data}')
            msg = self.data
            op_code = msg.pop('op')
            log.debug(f'Message is {msg}')
            loop = asyncio.get_event_loop()
            log.debug(f'Running function')
            result = loop.run_until_complete(
                EchoServerClientProtocol._node.op_func_map[op_code](msg))
            self.transport.write(pickle.dumps(result))
        except Exception as e:
            log.debug(e)
        finally:
            if self.transport:
                log.debug('Close the client socket')
                self.transport.close()

    def eof_received(self) -> None:
        log.debug('eof received')


class Node(BaseNode):
    incoming_ip = None

    def __init__(self, ip, bootstrap_server=None) -> None:
        super().__init__(ip)
        self.task_update_periodically = None
        self.bootstrap_server = bootstrap_server
        self.joined = False
        self.op_func_map = {
            op.FIND_SUCCESSOR: self.find_successor,
            op.UPDATE_FINGER_TABLE: self.update_finger_table,
            op.NOTIFY: self.notify,
            op.IS_ALIVE: self.is_alive
        }
        self.predecessor = None
        self.successor = None
        self.loop = None
        self.is_first_node = True
        self._server = None
        self.dead_fingers=[]

    async def run(self, loop: asyncio.BaseEventLoop):
        EchoServerClientProtocol._node = self
        self._server = await loop.create_server(EchoServerClientProtocol, self.ip, settings.CHORD_PORT)
        self.alive = True
        self.update_task = loop.create_task(self.update_periodically())
        loop.run_until_complete(self.update_task)

    async def update_periodically(self):
        while True:
            try:
                log.info('Started Updating Periodically!')
                if not self.joined:
                    if self.bootstrap_server:
                        log.info(f'Node {self.nid} Joining Chord Ring!')
                        await self.join()
                        self.joined = True
                        await asyncio.sleep(1)
                    else:
                        # When you are all alone in the network
                        self.successor = self
                        self.predecessor = self
                        log.info('Waiting for others to join the ring!')
                        await asyncio.sleep(1)
                log.debug('Stabilizing')
                await self.stabilize()
                await self.fix_fingers()
                # await self.check_fingers()
                await asyncio.sleep(1)
                # log.debug(f'Logging Node {self.nid}: ')
                # log.debug(self.to_bag())
                with open(f'{HostnameFilter.hostname}_{self.nid}.json', 'a') as f:
                    json.dump(self.to_bag(), f)
            except Exception as e:
                log.debug(e)

    async def check_fingers(self): # Find dead fingers and make them null
        nodes = set([f.node for f in self.fingers])
        self.dead_fingers=[]
        for node in nodes:
            if node and not node.is_alive():
                self.dead_fingers.append(node.nid)
        for f in self.fingers:
            if f.node and f.node.nid in self.dead_fingers:
                f.node = None
        if self.successor and self.successor.nid in self.dead_fingers:
            bootstrap_node = RemoteNode(self.bootstrap_server)
            successor_bag = await bootstrap_node.find_successor(
                {'node_id': self.nid})
            self.successor = RemoteNode.from_bag(successor_bag)


    async def fix_fingers(self):
        # This will eventually fix fingers, and so predecessors and successors
        i = random.randint(1, settings.NETWORK_SIZE-1)
        if self.successor and self.successor.nid != self.nid:
            successor_bag = await self.successor.find_successor({'node_id': self.fingers[i].start})
        elif self.bootstrap_server and self.bootstrap_server != self.ip:
            bootstrap_node = RemoteNode(self.bootstrap_server)
            successor_bag = await bootstrap_node.find_successor(
                {'node_id': self.fingers[i].start})
        else:
            return
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
                await p.update_finger_table({'s': self.to_bag(), 'i': i})
                updated.append(p.nid)

    async def update_finger_table(self, bag):  # <--
        # If s is the i'th finger of n, update n's finger table with s
        i = bag['i']
        s = bag['s']
        ith_finger = self.fingers[i].node
        if s['nid'] != self.nid and arc_contains(start=self.nid, stop=ith_finger.nid, element=s['nid']):
            self.fingers[i].node = RemoteNode.from_bag(s)
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
        if not node.successor:
            log.debug(f'Successor of {node_id} is This node - {self.nid}')
            return self.to_bag()
        else:
            log.debug(f'Successor of {node_id} is {node.successor.to_bag()}')
            return node.successor.to_bag()

    async def find_predecessor(self, node_id):  # <--
        log.debug(f'Finding Predecessor of {node_id}')
        node_prime = self
        while node_prime.successor and not arc_contains(node_prime.nid, node_prime.successor.nid, node_id, end_included=True):
            res_finger = await node_prime.closest_preceding_finger(node_id)
            # Nodes can be None at the beginning, we check it
            if res_finger and res_finger.node and res_finger.node.nid != self.nid:
                node_prime = res_finger.node
                log.debug(f'New Node Prime: {node_prime.nid}')
            else:
                break
        return node_prime

    async def closest_preceding_finger(self, node_id):  # <--
        asyncio.sleep(0.01)
        log.debug(
            f'Node({self.nid}) Finding Closest preceding finger of {node_id}')
        for i in range(settings.NETWORK_SIZE-1, -1, -1):
            if self.fingers[i].node and arc_contains(self.nid, node_id, self.fingers[i].node.nid):
                return self.fingers[i]
        return None
