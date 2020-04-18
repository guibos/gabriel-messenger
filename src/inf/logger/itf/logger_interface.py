from abc import abstractmethod, ABC
from asyncio import Task


class LoggerInterface(ABC):
    @abstractmethod
    def debug(self, message, *args, **kwargs) -> Task:
        raise NotImplementedError

    @abstractmethod
    def info(self, message, *args, **kwargs) -> Task:
        raise NotImplementedError

    @abstractmethod
    def warning(self, message, *args, **kwargs) -> Task:
        raise NotImplementedError

    @abstractmethod
    def error(self, message, *args, **kwargs) -> Task:
        raise NotImplementedError

    @abstractmethod
    def critical(self, message, *args, **kwargs) -> Task:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_logger(cls, configuration: dict, name: str, level: str):
        raise NotImplementedError
