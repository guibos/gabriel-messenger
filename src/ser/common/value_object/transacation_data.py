"""Transaction Data Module."""

from dataclasses import dataclass
from typing import Union, List

from src.ser.common.itf.publication import Publication
from src.ser.common.value_object.record import Record


@dataclass
class TransactionData:
    """All required data, to create a transaction. A transaction in these case is to know if a sender send a block of
    publications to all queues configured. Records are all related to persist anything on database."""
    publications: List[Publication]
    records: List[Record]
