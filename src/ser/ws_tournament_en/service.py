"""Weiß Schwarz - English Edition - Monthly Shop Tournament Card service Module."""
import orm
from bs4 import BeautifulSoup

from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.models.identifier_factory import identifier_factory
from src.ser.common.receiver_images_mixin import ReceiverImagesMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.transacation_data import TransactionData


class WSTournamentEn(ReceiverImagesMixin):
    """Weiß Schwarz - English Edition - Monthly Shop Tournament Card service. This is a receiver service.
    Get all English Edition - Monthly Shop Tournament Cards."""

    MODULE = "Weiß Schwarz - English Tournament"
    MODELS_METADATA, MODEL_IDENTIFIER, MODELS = identifier_factory(orm.Text(primary_key=True))

    _EN_URL = 'https://en.ws-tcg.com/events/'

    _PUBLIC_URL = True

    _RECEIVER_CONFIG = ReceiverConfig

    async def _load_publications(self):
        html = await self._get_site_content(url=self._EN_URL)
        beautiful_soap = BeautifulSoup(html, 'html5lib')
        months = beautiful_soap.findAll('div', class_='monthWrap')

        for month in months:
            cards = month.findAll('img')
            title_str = self._add_html_tag(month.find('h4').text.strip(), tag=self._TITLE_HTML_TAG)
            title = RichText(data=title_str, format_data=FormatData.HTML)

            for card in cards:
                publication = await self._create_publication_from_img(img=card, rich_title=title)
                if publication:
                    transaction_data = TransactionData(transaction_id=publication.publication_id,
                                                       publications=[publication])
                    await self._put_in_queue(transaction_data=transaction_data)
