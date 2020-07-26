"""SenderConfig Module."""
from abc import ABC
from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class SenderConfig(ABC):
    """Interface that store all config of a Sender."""
    pass
