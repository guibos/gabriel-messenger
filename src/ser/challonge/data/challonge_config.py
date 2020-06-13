from dataclasses import dataclass

from dataclasses_json import dataclass_json

from src.ser.common.itf.receiver_config import ReceiverConfig


@dataclass_json
@dataclass
class ChallongeConfig(ReceiverConfig):
    api_key: str

