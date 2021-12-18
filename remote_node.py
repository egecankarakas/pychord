import asyncio
import logging
import os
import pickle
import socket
import time
from hashlib import sha1

import operations as op
import settings
import utils
from base_node import BaseNode, Finger
from client import Client
from utils import arc_contains


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


class RemoteNode(BaseNode):
    def __init__(self, ip) -> None:
        super().__init__(ip)
        if not Client.getInstance(bootstrap=ip, bootstrap_id=utils.get_node_id(ip)):
            Client(bootstrap=ip, bootstrap_id=utils.get_node_id(ip))

    @staticmethod
    def from_bag(bag):
        log.debug(f'Bag: {bag}')
        node = RemoteNode(bag['ip'])
        if 'finger_table' in bag:
            for i, f in enumerate(bag['finger_table']):
                finger_node = RemoteNode(
                    f['node']['ip']) if f['node'] else None
                node.fingers[i] = Finger(
                    node=finger_node, start=f['start'], end=f['end'])
        return node

    # async def init_finger_table(self, arbitrary_node):
    #     message={'op':op.INIT_FINGER_TABLE,}
    #     if not self.client:
    #         self.client = Client()
    #     self.client.send(self.bootstrap_server,self.port,)

    async def init_finger_table(self, arbitrary_node):
        log.warn('init_finger_table is not implemented for remote node!')
        # message={'op':op.INIT_FINGER_TABLE,}
        # if not self.client:
        #     self.client = Client()
        # self.client.send(self.bootstrap_server,self.port,)

    async def find_successor(self, bag):
        result = None
        try:
            log.debug(
                f"Requesting Node {self.nid} to find successor of {bag['node_id']}")
            result = await Client.getInstance().send({**bag, **{'op': op.FIND_SUCCESSOR}}, self.ip, self.port)
        except Exception as e:
            log.debug(e)
        return result

    async def find_predecessor(self, node_id):  # TODO implement correctly
        log.debug(
            f'Requesting Node {self.nid} to find Predecessor of {node_id}')
        raise NotImplementedError
        # node_prime = self
        # while not arc_contains(node_prime.nid, node_prime.successor.nid, node_id, end_included=True):
        #     node_prime = node_prime.closest_preceding_finger(node_id)
        # return node_prime

    # TODO implement correctly
    async def closest_preceding_finger(self, node_id):
        log.debug(
            f'Requesting Node {self.nid} to find Closest preceding finger of {node_id}')
        raise NotImplementedError
        # for i in range(settings.NETWORK_SIZE-1, -1, -1):
        #     if arc_contains(self.nid, node_id, self.fingers[i].nid):
        #         return self.fingers[i]
        # return self

    async def join(self):
        log.warn("Cannot Join over remote node")

    async def init_finger_table(self):
        log.warn("Do not Initialize over remote node, make call to self!")

    async def update_finger_table(self, bag):
        try:
            log.debug(f"Updating finger table of Node {self.nid}")
            return await Client.getInstance().send({**bag, **{'op': op.UPDATE_FINGER_TABLE}}, self.ip, self.port)
        except Exception as e:
            log.debug(e)
        return None

    async def notify(self, bag):
        try:
            log.debug(
                f"Notifying {self.nid} that {bag['nid']} can be its predecessor")
            return await Client.getInstance().send({**bag, **{'op': op.NOTIFY}}, self.ip, self.port)
        except Exception as e:
            log.debug(e)
        return None
