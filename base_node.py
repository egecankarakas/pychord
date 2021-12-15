from abc import ABC, abstractmethod
from hashlib import sha1
import settings

class Finger():
    def __init__(self) -> None:
        self.node = None
        self.start = None
        self.end = None

class BaseNode(ABC):
    def __init__(self, ip) -> None:
        super().__init__()
        self.ip = ip
        self.port = settings.CHORD_PORT
        self.fingers = [Finger() for f in range(settings.NETWORK_SIZE)]
        self.hash = sha1()
        self.hash.update(ip.encode())
        self.hash.update(self.port.to_bytes(3, "big"))
        self.nid = int.from_bytes(
            self.hash.digest(), "big"
        )  % (1 << settings.NETWORK_SIZE)# SHA-1 result is casted to nid (node id)
        self.fingers[0] = self
        self.routes={self.nid: self.ip}
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
