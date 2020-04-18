import os.path
import sys
from typing import Optional

from aiologger import Logger as AioLogger
from aiologger.filters import StdoutFilter
from aiologger.formatters.base import Formatter
from aiologger.handlers.files import AsyncFileHandler
from aiologger.handlers.streams import AsyncStreamHandler
from aiologger.levels import NAME_TO_LEVEL, LogLevel

from src.inf.logger.handler.async_smtp_handler import AsyncSMTPHandler
from src.inf.logger.itf.logger_interface import LoggerInterface


class Logger(AioLogger, LoggerInterface):
    LOG_FILENAME = 'file.log'

    @staticmethod
    def _get_formatter(handler_configuration: dict) -> Optional[Formatter]:
        formatter = None
        if 'formatter' in handler_configuration:
            formatter = Formatter(**handler_configuration['formatter'])
        return formatter

    @classmethod
    def get_logger(cls, configuration: dict, name: str, path: str, level: str = 'NOTSET'):
        logger = cls(name=name, level=level)
        if 'stream' in configuration:
            configuration_handler = configuration['stream']
            level = NAME_TO_LEVEL[configuration_handler['level']]
            formatter = cls._get_formatter(handler_configuration=configuration_handler)

            logger.add_handler(
                AsyncStreamHandler(
                    stream=sys.stdout,
                    level=level,
                    formatter=formatter,
                    filter=StdoutFilter(),
                ))
            logger.add_handler(
                AsyncStreamHandler(
                    stream=sys.stderr,
                    level=max(LogLevel.WARNING, level),
                    formatter=formatter,
                ))
        if 'file' in configuration:
            logger.add_handler(AsyncFileHandler(filename=os.path.join(path, cls.LOG_FILENAME)))
        if 'smtp' in configuration:
            configuration_handler = configuration['smtp']
            logger.add_handler(
                AsyncSMTPHandler(
                    level=configuration_handler['level'],
                    sender=configuration_handler['sender'],
                    recipients=configuration_handler['recipients'],
                    subject=configuration_handler['subject'],
                    username=configuration_handler['username'],
                    password=configuration_handler['password'],
                    hostname=configuration_handler['hostname'],
                    port=configuration_handler['port'],
                    use_tls=configuration_handler['use_tls'],
                ))
        return logger
