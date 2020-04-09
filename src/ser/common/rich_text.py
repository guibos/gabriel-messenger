import pypandoc

from src.ser.common.enums.format_data import FormatData


class NotAllowedFormatError(Exception):
    """Non allowed format error."""


class RichText:
    _STORAGE_FORMAT = FormatData.HTML

    def __init__(self, data: str, format_data: FormatData):
        self._data: str = pypandoc.convert_text(data, self._STORAGE_FORMAT.value, format=format_data.value)

    def to_format(self, *, format_data: FormatData) -> str:
        if format_data == self._STORAGE_FORMAT:
            return self._data
        return pypandoc.convert_text(self._data, format_data.value, format=self._STORAGE_FORMAT.value).strip()
