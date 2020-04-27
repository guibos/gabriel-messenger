"""Custom Field Module."""

from abc import abstractmethod, ABC
from dataclasses import dataclass


@dataclass
class CustomFields(ABC):
    """Custom Field Interface. This dataclass will save all custom field of each receiver service. See CustomField for
    more information."""
    @abstractmethod
    def __iter__(self):
        raise NotImplementedError
