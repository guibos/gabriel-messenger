"""Weiss Schwarz today's card service Module"""

import os
import urllib.parse
from datetime import datetime
from typing import Optional

import orm
from bs4 import BeautifulSoup
from bs4.element import Tag

from src.ser.common.enums.format_data import FormatData
from src.ser.common.enums.language import Language
from src.ser.common.itf.publication import Publication
from src.ser.common.models.identifier_factory import identifier_factory
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.receiver_common_config import ReceiverCommonConfig
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.ws_today_card.data.ws_banner_service_config import WSTodayCardReceiverConfig


class WSTodayCard(ReceiverMixin):
    """Weiss Schwarz today's card service. This is a receiver service. Get all today's card of Weiss Schwarz."""
    MODULE = "Weiß Schwarz - Today's card"
    _EN_URL = 'https://en.ws-tcg.com/products/ws_today'
    _JP_URL = 'https://ws-tcg.com/todays-card/'
    _JP_DOMAIN = 'https://ws-tcg.com/'
    _EN_DOMAIN = 'https://en.ws-tcg.com'
    MODELS_METADATA, MODEL_IDENTIFIER, MODELS = identifier_factory(orm.Text(primary_key=True))
    _TITLE = "{} Edition - Today's Card"
    _CONFIG = WSTodayCardReceiverConfig

    def __init__(self, receiver_common_config: ReceiverCommonConfig):
        self._title = self._TITLE.format(receiver_common_config.receiver_config.language.value)
        if receiver_common_config.receiver_config.language == Language.ENGLISH:
            self._url = self._EN_URL
            self._domain = self._EN_DOMAIN
        elif receiver_common_config.receiver_config.language == Language.JAPANESE:
            self._url = self._JP_URL
            self._domain = self._JP_DOMAIN
        else:
            raise NotImplementedError

        super().__init__(receiver_common_config)

    async def _load_publications(self):
        html = await self._get_site_content(url=self._url)
        beautiful_soap = BeautifulSoup(html, 'html5lib')
        cards = beautiful_soap.find('div', class_='entry-content').findAll('img')

        for card in cards:
            publication = await self._get_new_cards(card=card)
            if publication:
                transaction_data = TransactionData(transaction_id=publication.publication_id,
                                                   publications=[publication])
                await self._put_in_queue(transaction_data=transaction_data)

    async def _get_new_cards(self, card: Tag) -> Optional[Publication]:
        file_name = os.path.basename(card.attrs['src'])
        file_name: str = file_name.split('?')[0]
        file = None

        if 'ws_today_' in file_name:
            file = await self._get_file_value_object(url=card.attrs['src'],
                                                     pretty_name=self._title,
                                                     filename_unique=False,
                                                     public_url=False)

            file_name = file.filename

        if file_name in self._cache:
            return None

        if file is None:
            file = await self._get_file_value_object(url=urllib.parse.urljoin(self._domain, card.attrs['src']),
                                                     pretty_name=self._title,
                                                     public_url=True)
        rich_title = RichText(data=self._add_html_tag(self._title, self._TITLE_HTML_TAG), format_data=FormatData.HTML)
        return Publication(
            publication_id=file_name,
            title=rich_title,
            url=self._url,
            timestamp=datetime.utcnow(),
            images=[file],
        )
