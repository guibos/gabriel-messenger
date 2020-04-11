"""Weiß Schwarz - News Module."""

import logging
import re
import urllib.parse
from asyncio import Queue
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup, element

from src.ser.common.data.weiss_schwarz_barcelona_data import BrigadaSOSData
from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.custom_config import CustomConfig
from src.ser.common.itf.publication import Publication
from src.ser.common.queue_manager import QueueManager
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.transacation_data import TransactionData
from src.ser.ws_news.models.identifier import Identifier, METADATA


class WSNews(ReceiverMixin, BrigadaSOSData):
    """Weiß Schwarz - News. This is a receiver service. Get news."""

    MODULE = "Weiß Schwarz - News"
    _URL = 'https://en.ws-tcg.com/information/'
    _DOMAIN = 'https://en.ws-tcg.com/'
    _NETLOC = 'en.ws-tcg.com'
    _PUBLIC_URL = True
    _FILENAME_UNIQUE = True
    MODEL_IDENTIFIER = Identifier
    MODELS = (Identifier, )
    MODELS_METADATA = METADATA
    _BANNED_ALT = (
        "FB_icon",
        "IG_icon",
        "Twitter_icon"
    )

    def __init__(self, *, files_directory: str, instance_name: str, queue_manager: QueueManager, download_files: bool,
                 wait_time: int, logging_level: str, state_change_queue: Queue, colour: int):
        self._instance_name = instance_name
        logger = logging.getLogger(self._instance_name)
        logger.setLevel(logging_level)
        super().__init__(logger=logger,
                         wait_time=wait_time,
                         state_change_queue=state_change_queue,
                         queue_manager=queue_manager,
                         files_directory=files_directory,
                         download_files=download_files)
        self._colour = colour
        self._queue_manager = queue_manager
        self._download_files = download_files
        self._files_directory = files_directory
        self._cache: List[int] = []

    async def _load_publications(self):

        html = await self._get_site_content(url=self._URL)
        beautiful_soap = BeautifulSoup(html, 'html5lib')
        news = beautiful_soap.find('ul', class_='info-list').find_all('li')

        for new in news:
            publication = await self._get_new_new(new=new)
            if publication:
                transaction_data = TransactionData(transaction_id=publication.publication_id,
                                                   publications=[publication])
                await self._put_in_queue(transaction_data=transaction_data)

    async def _get_new_new(self, new: element.Tag) -> Optional[Publication]:
        url: str = new.find('a').attrs['href']
        parsed_url = urllib.parse.urlparse(url)
        images = []
        files = []
        if not parsed_url.netloc:
            url = urllib.parse.urljoin(self._DOMAIN, url)
            parsed_url = urllib.parse.urlparse(url)

        if url in self._cache:
            return

        title_str = new.find(class_='title').text.strip()
        title_rich = RichText(data=self._add_html_tag(string=str(title_str), tag=self._TITLE_HTML_TAG),
                              format_data=FormatData.HTML)
        description = None
        if self._NETLOC == parsed_url.netloc:
            headers = await self._get_site_head(url=url)
            if headers.content_type == 'text/html':
                beautiful_soap = BeautifulSoup(await self._get_site_content(url=url), 'html5lib')
                data = beautiful_soap.find(class_='entry-content')
                description = await self._get_description(data=data)
                images = await self._get_images(data=data, title=title_str)

            else:
                file = await self._get_file_value_object(url=url,
                                                         pretty_name=title_str,
                                                         filename_unique=self._FILENAME_UNIQUE,
                                                         public_url=self._PUBLIC_URL)
                files.append(file)

        else:
            file = await self._get_file_value_object(url=new.find('img').attrs['src'].split('?')[0],
                                                     pretty_name=title_str,
                                                     filename_unique=self._FILENAME_UNIQUE,
                                                     public_url=self._PUBLIC_URL)
            images.append(file)

        return Publication(
            publication_id=url,
            title=title_rich,
            description=description,
            url=url,
            files=files,
            timestamp=datetime.utcnow(),
            color=self._colour,
            images=images,
            author=self._AUTHOR,
        )

    async def _get_images(self, data: element, title: str) -> element:
        images = []
        img_urls = []
        img_tags = data.find_all('img')
        for img_tag in img_tags:
            if 'alt' in img_tag.attrs:
                if img_tag.attrs['alt'] in self._BANNED_ALT:
                    continue
            img_url = img_tag.attrs['src'].split('?')[0]
            if img_url in img_urls:
                continue
            img_urls.append(img_url)
            if not urllib.parse.urlparse(img_url).netloc:
                img_url = urllib.parse.urljoin(self._DOMAIN, img_url)
            image = await self._get_file_value_object(url=img_url,
                                                      pretty_name=title,
                                                      filename_unique=self._FILENAME_UNIQUE,
                                                      public_url=self._PUBLIC_URL)
            images.append(image)
        return images

    async def _get_description(self, data: element) -> RichText:
        data = RichText(data=str(await self._remove_non_text_tags(data=data)), format_data=FormatData.HTML)
        return data

    async def _remove_non_text_tags(self, data: element) -> element:
        for script in data.find_all('script'):
            script.decompose()
        return data

    async def _clean_text(self, text):
        text = text.strip()
        text = re.sub(r'\n +', r'\n', text)
        text = re.sub(r'\n{2,}', r'\n\n', text)
        return text

    @classmethod
    def _get_custom_configuration(cls, *, configuration, senders):
        configurations = [
            CustomConfig(
                instance_name=cls._get_instance_name(),
                queue_manager=cls._get_queue_manager(config=configuration['send'], senders=senders),
            )
        ]
        return configurations
