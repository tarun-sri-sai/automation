from abc import ABC, abstractmethod


class Repos(ABC):
    @staticmethod
    @abstractmethod
    def get():
        pass
