"""Weiss Schwarz today card Config Module."""

from dataclasses import dataclass

from dataclasses_json import dataclass_json

from src.ser.common.enums.language import Language
from src.ser.common.itf.receiver_config import ReceiverConfig


@dataclass_json
@dataclass
class WSTodayCardReceiverConfig(ReceiverConfig):
    """Weiss Schwarz today card Config Module."""
    language: Language

    @property
    def instance_name(self):
        return self.language.value
