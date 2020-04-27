"""Product custom field value object module"""
from dataclasses import dataclass
from typing import Iterable

from src.ser.common.itf.custom_fields import CustomFields
from src.ser.common.value_object.custom_field import CustomField


@dataclass
class BlackfireCustomFields(CustomFields):
    """Blackfire custom field value object."""
    release_date: CustomField
    dead_line: CustomField

    def __iter__(self) -> Iterable[CustomField]:
        return iter((self.release_date, self.dead_line))
