"""Weiß Schwarz - Japanese Edition - Tournament Module"""

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
from src.ser.ws_tournament_jp.models.identifier import Identifier, METADATA


class WSTournamentJp(ReceiverImagesMixin, BrigadaSOSData):
    """Weiß Schwarz - Japanese Edition - Tournament. This is a receiver service.
    Get data of Japanese - Monthly Shop Tournament Cards."""

    MODULE = "Weiß Schwarz - Japanese Tournament"
    MODEL_IDENTIFIER = Identifier
    MODELS = (Identifier, )
    MODELS_METADATA = METADATA

    _FILENAME_UNIQUE = True
    _PUBLIC_URL = True
    _JP_URL = 'https://ws-tcg.com/events/list/battle_{}'
    _TITLE = "Japanese Edition - Monthly Shop Tournament Card"

    def __init__(self, *, files_directory: str, instance_name: str, queue_manager: QueueManager, download_files: bool,
                 wait_time: int, logging_level: str, state_change_queue: Queue, colour: int):
        self._instance_name = instance_name
        logger = logging.getLogger(self._instance_name)
        logger.setLevel(logging_level)
        self._title = RichText(data=self._add_html_tag(self._TITLE, tag=self._TITLE_HTML_TAG), format_data=FormatData.HTML)
        super().__init__(download_files=download_files,
                         files_directory=files_directory,
                         colour=colour,
                         author=self._AUTHOR,
                         logger=logger,
                         wait_time=wait_time,
                         state_change_queue=state_change_queue,
                         queue_manager=queue_manager)

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
                publications.append(await self._create_publication_from_img(img=image, url=url, check_cache=False, rich_title= self._title))
            transaction_data = TransactionData(transaction_id=ws_id, publications=publications)
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
