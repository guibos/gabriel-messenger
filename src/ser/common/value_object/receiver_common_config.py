"""ReceiverFullConfig module."""

from asyncio import Queue
from dataclasses import dataclass

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.queue_manager import QueueManager


@dataclass
class ReceiverCommonConfig:
    """Config that is passed all Receiver Intances."""
    logger: LoggerInterface
    state_change_queue: Queue
    queue_manager: QueueManager
    data_directory: str
    download_files: bool
