"""Publication Interface module."""

from abc import ABC
from dataclasses import field, dataclass
from datetime import datetime
from typing import List, Optional, Union, Any

from src.ser.common.rich_text import RichText
from src.ser.common.value_object.author import Author
from src.ser.common.value_object.file_value_object import FileValueObject


# pylint: disable=too-many-instance-attributes
@dataclass
class Publication(ABC):
    """Publication Interface. Is the base to create another dataclass that will be used to share publications between
    services."""
    publication_id: Union[str, int]
    title: Optional[RichText] = None
    description: Optional[RichText] = None
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    color: Optional[int] = None
    images: List[FileValueObject] = field(default_factory=list)
    files: List[FileValueObject] = field(default_factory=list)
    author: Optional[Author] = None
    custom_fields: Optional[Any] = None

    @property
    def markdown(self):
        """Markdown output."""
        return f"*{self.title}*\n"

    @property
    def text(self):
        """Plain text output."""
        return "{self.title}*\n"
