from abc import ABC, abstractmethod


class Client(ABC):
    @staticmethod
    @abstractmethod
    def get_host():
        pass

    @staticmethod
    @abstractmethod
    def make_request(*args, **kwargs):
        pass
