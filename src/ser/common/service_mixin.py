"""Common Repository Mixin Module."""
import os
from abc import abstractmethod
from typing import Optional

import appdirs

from src.ser.common.enums.environment import Environment
from src.ser.common.rich_text import RichText


class ServiceMixin:
    """Common Service Mixin. This class includes methods that required by senders services and receivers services."""
    MODULE = NotImplementedError  # type: str
    _DATABASE_FILE = "db.sqlite"
    _WAIT_TIME = 5

    @classmethod
    def _get_instance_name(cls, *args):
        if args:
            return f"{cls.MODULE} [{' '.join(args)}]"
        return f"{cls.MODULE}"

    @abstractmethod
    async def run(self):
        """Run instance method."""
        raise NotImplementedError

    @staticmethod
    async def _get_format_data(data: Optional[RichText], format_data) -> Optional[str]:
        if data:
            return data.to_format(format_data=format_data)
        return data

    @classmethod
    def _get_repository_directory(cls, *, app_name: str, environment: Environment) -> str:
        repository_directory = os.path.join(appdirs.user_data_dir(app_name), environment.value, cls.MODULE)
        os.makedirs(repository_directory, exist_ok=True)
        return repository_directory
