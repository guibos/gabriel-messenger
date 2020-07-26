from asyncio import AbstractEventLoop, Queue
from dataclasses import dataclass

from src.inf.logger.itf.logger_interface import LoggerInterface


@dataclass
class SenderCommonConfig:
    """Config that is passed all Sender Intances."""
    loop: AbstractEventLoop
    publication_queue: Queue
    state_change_queue: Queue
    logger: LoggerInterface
    failed_publication_directory: str
