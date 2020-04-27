"""Weiß Schwarz - News Module."""

import re
import urllib.parse
from datetime import datetime
from typing import Optional

import orm
from bs4 import BeautifulSoup, element

from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.publication import Publication
from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.models.identifier_factory import identifier_factory
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.transacation_data import TransactionData


class WSNews(ReceiverMixin):
    """Weiß Schwarz - News. This is a receiver service. Get news."""

    MODULE = "Weiß Schwarz - News"
    _URL = 'https://en.ws-tcg.com/information/'
    _DOMAIN = 'https://en.ws-tcg.com/'
    _NETLOC = 'en.ws-tcg.com'
    _PUBLIC_URL = True
    _FILENAME_UNIQUE = True
    MODELS_METADATA, MODEL_IDENTIFIER, MODELS = identifier_factory(orm.Text(primary_key=True))
    _BANNED_ALT = ("FB_icon", "IG_icon", "Twitter_icon")
    _RECEIVER_CONFIG = ReceiverConfig

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
                images = await self._get_images(data=data, title=title_str, max_images=5)

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
            images=images,
        )

    async def _get_images(self, data: element, title: str, max_images: Optional[int] = None) -> element:
        images = []
        img_urls = []
        img_tags = data.find_all('img')
        if max_images:
            img_tags = img_tags[:max_images]
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

    @staticmethod
    async def _remove_non_text_tags(data: element) -> element:
        for script in data.find_all('script'):
            script.decompose()
        return data

    @staticmethod
    async def _clean_text(text):
        text = text.strip()
        text = re.sub(r'\n +', r'\n', text)
        text = re.sub(r'\n{2,}', r'\n\n', text)
        return text
