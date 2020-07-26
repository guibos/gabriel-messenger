"""Weiß Schwarz - Japanese Edition - Tournament Module"""
import orm
from bs4 import BeautifulSoup

from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.models.identifier_factory import identifier_factory
from src.ser.common.receiver_images_mixin import ReceiverImagesMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.receiver_common_config import ReceiverCommonConfig
from src.ser.common.value_object.transacation_data import TransactionData


class WSTournamentJp(ReceiverImagesMixin):
    """Weiß Schwarz - Japanese Edition - Tournament. This is a receiver service.
    Get data of Japanese - Monthly Shop Tournament Cards."""

    MODULE = "Weiß Schwarz - Japanese Tournament"
    MODELS_METADATA, MODEL_IDENTIFIER, MODELS = identifier_factory(orm.Integer(primary_key=True))

    _FILENAME_UNIQUE = True
    _PUBLIC_URL = True
    _JP_URL = 'https://ws-tcg.com/events/list/battle_{}'
    _TITLE = "Japanese Edition - Monthly Shop Tournament Card"
    _CONFIG = ReceiverConfig

    def __init__(self, receiver_common_config: ReceiverCommonConfig):

        self._title = RichText(data=self._add_html_tag(self._TITLE, tag=self._TITLE_HTML_TAG),
                               format_data=FormatData.HTML)
        super().__init__(receiver_common_config=receiver_common_config)

    async def _load_publications(self):
        if not self._cache:
            self._cache = [850]
        while True:
            ws_id = max(self._cache) + 1
            url = self._JP_URL.format(ws_id)
            html = await self._get_site_content(url=url)
            beautiful_soap = BeautifulSoup(html, 'html5lib')
            main = beautiful_soap.find('div', class_='contents-box-main')

            if not main:
                self._logger.debug("No more entries.")
                return
            images = main.find_all('img')

            publications = []
            for image in images:
                publications.append(await self._create_publication_from_img(img=image,
                                                                            url=url,
                                                                            check_cache=False,
                                                                            rich_title=self._title))
            transaction_data = TransactionData(transaction_id=ws_id, publications=publications)
            await self._put_in_queue(transaction_data=transaction_data)
