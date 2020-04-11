"""Blackfire service module. This is a receiver service."""
import logging
import re
import urllib.parse
from asyncio import Queue
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag

from src.ser.blackfire.data.blackfire_publication import BlackfirePublication
from src.ser.blackfire.data.config import Config
from src.ser.blackfire.data.custom_fields import CustomFields
from src.ser.blackfire.models.identifier import Identifier, METADATA
from src.ser.common.data.weiss_schwarz_barcelona_data import BrigadaSOSData
from src.ser.common.enums.format_data import FormatData
from src.ser.common.queue_manager import QueueManager
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.custom_field import CustomField
from src.ser.common.value_object.transacation_data import TransactionData


class BlackfireService(ReceiverMixin, BrigadaSOSData):
    """Blackfire service. This is a receiver service. With a string parameter allows module filter product of
    all products of ADC Blackfire."""
    MODULE = 'Blackfire'
    MODELS = (Identifier, )
    MODEL_IDENTIFIER = Identifier
    MODELS_METADATA = METADATA

    _DATE_FORMAT = r'[0-9]{2}.[0-9]{2}.[0-9]{4}'
    _PRODUCTS_URL = 'https://www.blackfire.eu/list.php?ppp=60&sort=age&query={}'
    _PRODUCT_URL = 'https://www.blackfire.eu/product.php?id={}'
    _BLACKFIRE_BASE_URL = 'https://www.blackfire.eu/{}'
    _PUBLIC_URL = True
    _FORMAT_DATA = FormatData.HTML

    def __init__(self, *, files_directory: str, instance_name: str, queue_manager: QueueManager, search_parameters: str,
                 download_files: bool, wait_time: int, logging_level: str, state_change_queue: Queue, colour: int):
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
        self._search_parameters = search_parameters

    async def _load_publications(self) -> None:
        html = await self._get_site_content(url=self._PRODUCTS_URL.format(self._search_parameters))
        html = html.decode('utf-8')
        beautiful_soup = BeautifulSoup(html, 'html.parser')
        products_bs = beautiful_soup.find('div', class_='product-list')
        if not products_bs:
            return

        products_ids = await self._get_new_product_ids(products_bs=products_bs)

        publications = []
        for product_id in products_ids:
            publications.append(await self._get_product(product_id=product_id))

        publications.sort(key=lambda product_item: product_item.title.to_format(format_data=FormatData.PLAIN))
        self._logger.debug("Loaded all products")

        for publication in publications:
            transaction_data = TransactionData(transaction_id=publication.publication_id, publications=[publication])
            await self._put_in_queue(transaction_data=transaction_data)

    async def _get_new_product_ids(self, products_bs: List[Tag]):
        products_ids = []
        for product_bs in products_bs:
            product_id = int(product_bs.find('a').attrs['href'].split('=')[1])
            if product_id not in self._cache:
                products_ids.append(product_id)

        return products_ids

    async def _get_product(self, product_id: int) -> BlackfirePublication:
        product_url = self._PRODUCT_URL.format(product_id)
        html = await self._get_site_content(url=product_url)
        beautiful_soup = BeautifulSoup(html, 'html.parser')
        product_name = beautiful_soup.find('h1')
        product_name_text = product_name.text
        product_name_rich = str(product_name)
        product_description_rich = str(beautiful_soup.find(id='tab-description'))
        product_image_url = self._BLACKFIRE_BASE_URL.format(beautiful_soup.find(id='image').attrs['src'])
        file = await self._get_file_value_object(url=product_image_url,
                                                 public_url=self._PUBLIC_URL,
                                                 pretty_name=product_name_text)
        beautiful_soup_description = beautiful_soup.find(class_="description").text.split('\n')
        product_custom_fields_value_object = CustomFields(
            release_date=self._get_release_date(beautiful_soup_description=beautiful_soup_description),
            dead_line=self._get_dead_line(beautiful_soup_description=beautiful_soup_description),
        )
        product_value_object = BlackfirePublication(publication_id=product_id,
                                                    title=RichText(data=product_name_rich, format_data=self._FORMAT_DATA),
                                                    description=RichText(data=product_description_rich, format_data=self._FORMAT_DATA),
                                                    url=product_url,
                                                    timestamp=datetime.utcnow(),
                                                    color=self._colour,
                                                    images=[file],
                                                    author=self._AUTHOR,
                                                    custom_fields=product_custom_fields_value_object)
        return product_value_object

    def _get_release_date(self, *, beautiful_soup_description: str) -> Optional[CustomField]:
        release_date = None
        for line in beautiful_soup_description:
            if 'Release Date' in line:
                date_text = self._clean_text(line=line)
                release_date = CustomField(name='Fecha de Lanzamiento', value=date_text)
        return release_date

    def _get_dead_line(self, *, beautiful_soup_description: str) -> Optional[CustomField]:
        dead_line = None
        for line in beautiful_soup_description:
            if 'Order Deadline' in line:
                date_text = self._clean_text(line=line)
                dead_line = CustomField(name='Fecha límite', value=date_text)
        return dead_line

    def _clean_text(self, line):
        date_text = line.split(' ', 2)[2]
        if re.findall(self._DATE_FORMAT, line):
            date_text = date_text.replace('.', '/')
        return date_text

    @classmethod
    def _get_custom_configuration(cls, *, configuration, senders):
        configurations = []
        for search_text, sender_config in configuration['search'].items():
            configurations.append(
                Config(
                    search_parameters=urllib.parse.quote(search_text),
                    instance_name=cls._get_instance_name(search_text),
                    queue_manager=cls._get_queue_manager(config=sender_config, senders=senders),
                ))
        return configurations
