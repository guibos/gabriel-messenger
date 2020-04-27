"""Queue Context Value Object Module."""

from asyncio import Queue
from dataclasses import dataclass
from typing import Union, Any, Dict


@dataclass
class QueueContext:
    """Queue Context Value Object. This will be passed to receivers services to know a what queues will need to send
    data."""
    publication_queue: Queue
    channel: Union[str, int]
    publication_data: Dict[str, Any]
