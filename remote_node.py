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
from hashlib import sha1
from utils import arc_contains

class HostnameFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = HostnameFilter.hostname
        return True

handler = logging.StreamHandler()
handler.addFilter(HostnameFilter())
handler.setFormatter(logging.Formatter('%(asctime)s %(hostname)s: %(message)s', datefmt='%b %d %H:%M:%S'))
log=logging.getLogger('Chord')
log.addHandler(handler)


class RemoteNode(BaseNode):
    def __init__(self, ip) -> None:
        super().__init__(ip)
        self.client=Client()

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

    async def find_successor(self,node_id):
        log.debug(f'Requesting Node {self.nid} to find successor of {node_id}')
        node = self.client.send(self.ip,self.port,{'op':op.FIND_SUCCESSOR,'node_id':node_id})
        return node
    
    async def find_predecessor(self,node_id):
        log.debug(f'Requesting Node {self.nid} to find Predecessor of {node_id}')
        node_prime = self
        while not arc_contains(node_prime.nid,node_prime.successor.nid,node_id,end_included=True):
            node_prime = node_prime.closest_preceding_finger(node_id)
        return node_prime

    async def closest_preceding_finger(self,node_id):
        log.debug(f'Requesting Node {self.nid} to find Closest preceding finger of {node_id}')
        for i in range(settings.NETWORK_SIZE-1,-1,-1):
            if arc_contains(self.nid,node_id,self.fingers[i].nid):
                return self.fingers[i]
        return self

    async def join(self):
        log.warn("Cannot Join over remote node")

    async def init_finger_table(self):
        log.warn("Do not Initialize over remote node, make call to self!")
