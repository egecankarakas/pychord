from abc import ABC, abstractmethod
from hashlib import sha1
import settings
import time


class Finger():
    def __init__(self, node=None, start=None, end=None) -> None:
        self.node = node
        self.start = start
        self.end = end

    def to_bag(self):
        return {'node': {'nid': self.node.nid, 'ip': self.node.ip} if self.node else None, 'start': self.start, 'end': self.end}


class BaseNode(ABC):
    def __init__(self, ip) -> None:
        super().__init__()
        self.ip = ip
        self.port = settings.CHORD_PORT
        self.hash = sha1()
        self.hash.update(ip.encode())
        self.hash.update(self.port.to_bytes(3, "big"))
        self.nid = int.from_bytes(
            self.hash.digest(), "big"
        ) % (1 << settings.NETWORK_SIZE)  # SHA-1 result is casted to nid (node id)
        self.fingers = [Finger(start=self.nid+(1 << k), end=self.nid+(1 << k+1))
                        for k in range(settings.NETWORK_SIZE)]
        self.fingers[0].node = self
        self.routes = {self.nid: self.ip}
        self.successor = None
        self.predecessor = None
        self.alive = True
    # @abstractmethod
    # def find_successor(self, id):
    #     pass

    # @abstractmethod
    # def find_predecessor(self,id):
    #     pass

    # @abstractmethod
    # def closest_preceding_finger(self,id):
    #     pass

    @abstractmethod
    def join(self):
        # join to chord network, calls init finger table
        pass

    @abstractmethod
    def init_finger_table(self, ip):
        # initialize finger table of this node with an arbitrary node
        pass

    # @abstractmethod
    # def update_others(self):
    #     # PERIODICAL
    #     # update all nodes whose finger tables should refer to this node
    #     pass

    # @abstractmethod
    # def update_finger_table(self,s,i):
    #     # PERIODICAL
    #     # if s is i'th finger of n, update n's finger table with s
    #     pass

    # # STABILIZATION METHODS
    # @abstractmethod
    # def stabilize(self):
    #     # PERIODICAL
    #     # periodically verify n's immediate successor, and tell the successor about n
    #     pass

    # @abstractmethod
    # def notify(self,predecessor):
    #     # PERIODICAL
    #     # predecessor thinks it is this node's predecessor
    #     pass

    # @abstractmethod
    # def fix_fingers():
    #     # PERIODICAL
    #     # periodically refresh finger table entries
    #     pass
    def to_dict(self):
        return {'successor': self.successor.nid, 'predecessor': self.predecessor.nid, 'fingers': [f.nid for f in self.fingers]}

    def to_bag(self):
        reporttime = time.asctime(time.localtime(time.time()))
        # print(f'bagging {self.nid}')
        bag = {'ip': self.ip}
        bag['nid'] = self.nid
        finger_table = []
        for f in self.fingers:
            finger_table.append(f.to_bag())  # TODO fix the bag
        bag['finger_table'] = finger_table
        bag['successor'] = {'nid': self.successor.nid,
                            'ip': self.successor.ip} if self.successor else None
        bag['predecessor'] = {'nid': self.predecessor.nid,
                              'ip': self.predecessor.ip} if self.predecessor else None
        bag['time'] = {'local':reporttime }
        # print(f'bagged {self.nid}')
        return bag

    async def is_alive(self):
        return self.alive
