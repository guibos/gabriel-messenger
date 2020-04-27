"""Blackfire Custom Config Module."""

from dataclasses import dataclass

from dataclasses_json import dataclass_json

from src.ser.common.itf.receiver_config import ReceiverConfig


@dataclass_json
@dataclass
class BlackfireReceiverConfig(ReceiverConfig):
    """Blackfire custom config."""
    search_parameters: str

    @property
    def instance_name(self):
        return self.search_parameters
