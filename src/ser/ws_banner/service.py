"""Weiss Schwarz Banner service Module."""

import logging
from asyncio import Queue

from bs4 import BeautifulSoup

from src.ser.common.data.weiss_schwarz_barcelona_data import WeissSchwarzBarcelonaData
from src.ser.common.enums.format_data import FormatData
from src.ser.common.enums.language import Language
from src.ser.common.queue_manager import QueueManager
from src.ser.common.receiver_images_mixin import ReceiverImagesMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.ws_banner.data.config import Config
from src.ser.ws_banner.models.identifier import METADATA, Identifier


class WSBannerService(ReceiverImagesMixin, WeissSchwarzBarcelonaData):
    """Weiss Schwarz Banner service. This is a receiver service. Get all Banners os Weiss Schwarz."""
    MODULE = 'Weiß Schwarz - Banner'
    _EN_URL = 'https://en.ws-tcg.com'
    _JP_URL = 'https://ws-tcg.com'
    _TITLE = "{} Edition - Banner"

    MODELS = (Identifier, )
    MODEL_IDENTIFIER = Identifier
    MODELS_METADATA = METADATA

    _PUBLIC_URL = True

    def __init__(self, *, files_directory: str, instance_name: str, queue_manager: QueueManager, language: Language,
                 download_files: bool, wait_time: int, logging_level: str, state_change_queue: Queue, colour: int):
        self._instance_name = instance_name
        logger = logging.getLogger(self._instance_name)
        logger.setLevel(logging_level)

        title = self._TITLE.format(language.value)
        title = self._add_html_tag(string=title, tag=self._TITLE_HTML_TAG)
        self._title = RichText(data=title, format_data=FormatData.HTML)
        if language == Language.ENGLISH:
            self._url = self._EN_URL
        elif language == Language.JAPANESE:
            self._url = self._JP_URL
        else:
            raise NotImplementedError

        super().__init__(
            queue_manager=queue_manager,
            download_files=download_files,
            files_directory=files_directory,
            colour=colour,
            author=self._AUTHOR,
            logger=logger,
            wait_time=wait_time,
            state_change_queue=state_change_queue,
        )

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

    @classmethod
    def _get_custom_configuration(cls, *, configuration, senders):
        configurations = []
        for language_text, sender_config in configuration['send'].items():
            language = Language(language_text)
            configurations.append(
                Config(
                    language=language,
                    instance_name=cls._get_instance_name(language_text),
                    queue_manager=cls._get_queue_manager(config=sender_config, senders=senders),
                ))
        return configurations
