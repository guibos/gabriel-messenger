"""Weiß Schwarz - English Edition - Monthly Shop Tournament Card service Module."""

import logging
from asyncio import Queue

from bs4 import BeautifulSoup

from src.ser.common.data.weiss_schwarz_barcelona_data import BrigadaSOSData
from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.custom_config import CustomConfig
from src.ser.common.queue_manager import QueueManager
from src.ser.common.receiver_images_mixin import ReceiverImagesMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.ws_tournament_en.models.identifier import Identifier, METADATA


class WSTournamentEn(ReceiverImagesMixin, BrigadaSOSData):
    """Weiß Schwarz - English Edition - Monthly Shop Tournament Card service. This is a receiver service.
    Get all English Edition - Monthly Shop Tournament Cards."""

    MODULE = "Weiß Schwarz - English Tournament"
    MODEL_IDENTIFIER = Identifier
    MODELS = (Identifier, )
    MODELS_METADATA = METADATA

    _EN_URL = 'https://en.ws-tcg.com/events/'

    _PUBLIC_URL = True

    def __init__(self, *, files_directory: str, instance_name: str, queue_manager: QueueManager, download_files: bool,
                 wait_time: int, logging_level: str, state_change_queue: Queue, colour: int):
        self._instance_name = instance_name
        logger = logging.getLogger(self._instance_name)
        logger.setLevel(logging_level)
        super().__init__(queue_manager=queue_manager,
                         download_files=download_files,
                         files_directory=files_directory,
                         colour=colour,
                         author=self._AUTHOR,
                         logger=logger,
                         wait_time=wait_time,
                         state_change_queue=state_change_queue)

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

    @classmethod
    def _get_custom_configuration(cls, *, configuration, senders):
        configurations = [
            CustomConfig(
                instance_name=cls._get_instance_name(),
                queue_manager=cls._get_queue_manager(config=configuration['send'], senders=senders),
            )
        ]
        return configurations
