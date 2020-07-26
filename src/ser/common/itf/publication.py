"""Publication Interface module."""

from abc import ABC
from dataclasses import field, dataclass
from datetime import datetime
from typing import List, Optional, Union

from dataclasses_json import dataclass_json

from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.custom_fields import CustomFields
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.author import Author
from src.ser.common.value_object.custom_field import CustomField
from src.ser.common.value_object.file_value_object import FileValueObject


@dataclass_json
@dataclass
class Publication(ABC):
    """Publication Interface. Is the base to create another dataclass that will be used to share publications between
    services."""
    publication_id: Optional[Union[str, int]] = None
    title: Optional[RichText] = None
    description: Optional[RichText] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    url: Optional[str] = None
    files: List[FileValueObject] = field(default_factory=list)
    author: Optional[Author] = None
    custom_fields: List[CustomField] = field(default_factory=list)

    def to_format(self, *, format_data: FormatData):
        """Output all publication to specific format."""
        rich_items = [
            self.title,
            self.description,
        ]

        non_rich_item = {
            'URL': self.url,
            'Inicio': self.start_at,
            'Finalización': self.end_at,
        }

        to_print = [rich_text.to_format(format_data=format_data) for rich_text in rich_items if rich_text]

        to_print.extend([self._kv_to_print(key, value, format_data) for key, value in non_rich_item.items() if value])

        if self.custom_fields:
            to_print.extend([self._field_to_print(c_field, format_data) for c_field in self.custom_fields if c_field])

        rich_text = RichText('<p>error<br/>error</p>', format_data=FormatData.HTML)
        line_feed = rich_text.to_format(format_data=format_data).replace('error', '')

        return line_feed.join(to_print)

    @staticmethod
    def _field_to_print(c_field, format_data: FormatData):
        return RichText(f'***{c_field.name}:*** {c_field.value}',
                        format_data=FormatData.MARKDOWN).to_format(format_data=format_data)

    @staticmethod
    def _kv_to_print(key: str, value, format_data: FormatData):
        return RichText(f'***{key}:*** {value}', format_data=FormatData.MARKDOWN).to_format(format_data=format_data)
