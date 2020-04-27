"""BlackfirePublication Module"""
from dataclasses import dataclass
from typing import Optional

from src.ser.blackfire.data.blackfire_custom_fields import BlackfireCustomFields
from src.ser.common.itf.publication import Publication


@dataclass
class BlackfirePublication(Publication):
    """Dataclass that expand a Publication."""
    custom_fields: Optional[BlackfireCustomFields] = None
