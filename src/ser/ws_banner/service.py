"""Weiss Schwarz Banner service Module."""
import orm
from bs4 import BeautifulSoup

from src.ser.common.enums.format_data import FormatData
from src.ser.common.enums.language import Language
from src.ser.common.models.identifier_factory import identifier_factory
from src.ser.common.receiver_images_mixin import ReceiverImagesMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.receiver_common_config import ReceiverCommonConfig
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.ws_banner.data.ws_banner_service_config import WSBannerReceiverConfig


class WSBannerService(ReceiverImagesMixin):
    """Weiss Schwarz Banner service. This is a receiver service. Get all Banners os Weiss Schwarz."""
    MODULE = 'Weiß Schwarz - Banner'
    _EN_URL = 'https://en.ws-tcg.com'
    _JP_URL = 'https://ws-tcg.com'
    _TITLE = "{} Edition - Banner"
    _CONFIG = WSBannerReceiverConfig

    MODELS_METADATA, MODEL_IDENTIFIER, MODELS = identifier_factory(orm.Text(primary_key=True))

    _PUBLIC_URL = True

    def __init__(self, receiver_common_config: ReceiverCommonConfig):
        title = self._TITLE.format(receiver_common_config.receiver_config.language.value)
        title = self._add_html_tag(string=title, tag=self._TITLE_HTML_TAG)
        self._title = RichText(data=title, format_data=FormatData.HTML)
        if receiver_common_config.receiver_config.language == Language.ENGLISH:
            self._url = self._EN_URL
        elif receiver_common_config.receiver_config.language == Language.JAPANESE:
            self._url = self._JP_URL
        else:
            raise NotImplementedError

        super().__init__(receiver_common_config=receiver_common_config)

    async def _load_publications(self):
        html = await self._get_site_content(url=self._url)
        beautiful_soap = BeautifulSoup(html, 'html5lib')
        banners = beautiful_soap.findAll('div', class_='slide-banner')[0].findAll('img')

        for banner in banners:
            publication = await self._create_publication_from_img(img=banner, url=self._url, rich_title=self._title)
            if publication:
                transaction_data = TransactionData(transaction_id=publication.publication_id,
                                                   publications=[publication])
                await self._put_in_queue(transaction_data=transaction_data)
