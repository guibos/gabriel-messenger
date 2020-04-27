"""RichText Module."""
from dataclasses import dataclass

import pypandoc
from bs4 import BeautifulSoup

from src.ser.common.enums.format_data import FormatData


@dataclass
class RichText:  # pylint: disable=too-few-public-methods
    """RichText class. This class save internally data that after convert to another format through pandoc. Example
    HTML to Markdown."""
    data: str
    format_data: FormatData

    def to_format(self, *, format_data: FormatData) -> str:
        """Convert or return data to specific format."""
        if format_data == self.format_data:
            return self.data
        if format_data == FormatData.WHATS_APP:
            return self._convert_to_whats_app_text()
        return pypandoc.convert_text(self.data, format_data.value, format=self.format_data.value).strip()

    def _convert_to_whats_app_text(self):
        data = pypandoc.convert_text(self.data, FormatData.HTML.value, format=self.format_data.value).strip()
        soup = BeautifulSoup(data, 'html5lib')
        titles = soup.find_all([f"h{n}" for n in range(0, 10)])
        for title in titles:
            title.name = 'strong'
        for tag in soup.findAll(['strong']):
            tag.replaceWith(BeautifulSoup('*' + tag.renderContents().decode().strip() + '*', "html.parser"))

        return pypandoc.convert_text(str(soup), 'plain', format='html', extra_args=['--wrap', 'none']).strip()
