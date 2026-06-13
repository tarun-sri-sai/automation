from abc import ABC, abstractmethod


class BranchProtections(ABC):
    @abstractmethod
    def verify(self):
        pass
