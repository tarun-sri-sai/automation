from abc import ABC, abstractmethod


class BranchProtections(ABC):
    @staticmethod
    @abstractmethod
    def verify():
        pass
