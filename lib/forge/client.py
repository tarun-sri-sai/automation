from abc import ABC, abstractmethod


class Client(ABC):
    @abstractmethod
    def is_authenticated(self):
        pass

    @abstractmethod
    def build_url(self, endpoint):
        pass

    @abstractmethod
    def make_request(self, method, endpoint=None, full_url=None, **kwargs):
        pass
