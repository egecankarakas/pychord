from abc import ABC, abstractmethod
class BaseNode(ABC):
    @abstractmethod
    find_successor(self, id):
        pass
    