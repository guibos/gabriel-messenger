from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json

from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.itf.publication import Publication


@dataclass_json
@dataclass
class RecyclerConfig(ReceiverConfig):
    publications: List[Publication]
