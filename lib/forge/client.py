from abc import ABC, abstractmethod


class Client(ABC):
    @abstractmethod
    def is_authenticated(self):
        pass

    @abstractmethod
    def make_request(self, method, endpoint, **kwargs):
        pass
