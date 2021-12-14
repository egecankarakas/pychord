from abc import ABC, abstractmethod
class BaseNode(ABC):
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
        # join to chord network
        pass

    # @abstractmethod
    # def init_finger_table(self, arbitrary_node):
    #     # initialize finger table of this node with an arbitrary node
    #     pass

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