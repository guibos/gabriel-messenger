"""Common Repository Mixin Module."""
import os
from typing import Optional

import appdirs

from src.ser.common.enums.environment import Environment
from src.ser.common.rich_text import RichText


class ServiceMixin:  # pylint: disable=too-few-public-methods
    """Common Service Mixin. This class includes methods that required by senders services and receivers services."""
    MODULE = NotImplementedError  # type: str
    _DATA_DIRECTORY = 'data'
    _DATABASE_FILE = "db.sqlite"
    _DATABASE_TIMEOUT = 6000000
    _WAIT_TIME = 5

    @classmethod
    def _get_instance_name(cls, *args):
        if args:
            return f"{cls.MODULE} [{' '.join(args)}]"
        return f"{cls.MODULE}"

    @staticmethod
    async def _get_format_data(data: Optional[RichText], format_data) -> Optional[str]:
        if data:
            return data.to_format(format_data=format_data)
        return data

    @classmethod
    def _get_instance_directory(cls, *, app_name: str, environment: Environment, instance_name: str) -> str:
        instance_directory = os.path.join(appdirs.user_data_dir(app_name), environment.value, cls.MODULE, instance_name)
        os.makedirs(instance_directory, exist_ok=True)
        return instance_directory

    @classmethod
    def _get_sub_directory(cls, *, directory: str, sub_directory: str) -> str:
        new_directory = os.path.join(directory, sub_directory)
        os.makedirs(new_directory, exist_ok=True)
        return new_directory
