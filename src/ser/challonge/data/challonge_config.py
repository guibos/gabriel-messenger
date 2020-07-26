from dataclasses import dataclass

from dataclasses_json import dataclass_json

from src.ser.common.itf.receiver_config import ReceiverConfig


@dataclass_json
@dataclass
class ChallongeConfig(ReceiverConfig):
    api_key: str
    sub_domain: str
    time_to_live: int

    @property
    def instance_name(self):
        """Unique name of a instance of a module."""
        return self.sub_domain

