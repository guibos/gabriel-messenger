"""ReceiverConfig Module."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class ReceiverConfig(ABC):
    """Interface that store all config of a Receiver."""
    wait_time: int

    @property
    def instance_name(self):
        """Unique name of a instance of a module."""
        return None