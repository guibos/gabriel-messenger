from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Record:
    model: Any
    record_data: Dict[str, Any]
