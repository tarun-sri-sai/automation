from abc import ABC, abstractmethod


class Repos(ABC):
    @abstractmethod
    def get(self):
        pass
