"""Receiver Images Mixin Module."""

from abc import abstractmethod
from asyncio import Queue
from datetime import datetime
from logging import Logger
from typing import List, Optional

from bs4.element import Tag

from src.ser.common.abstract.attribute import AbstractAttribute
from src.ser.common.itf.publication import Publication
from src.ser.common.queue_manager import QueueManager
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.rich_text import RichText
from src.ser.common.value_object.author import Author


class ReceiverImagesMixin(ReceiverMixin):
    """Mixin to process to parse all services that his publication is a img html tag."""

    _TITLE: str = AbstractAttribute()
    _FILENAME_UNIQUE: bool = AbstractAttribute()
    _PUBLIC_URL: bool = AbstractAttribute()

    # pylint: disable=too-many-arguments
    def __init__(self, queue_manager: QueueManager, download_files: bool, files_directory: str, colour: int,
                 author: Author, logger: Logger, wait_time: int, state_change_queue: Queue):
        super().__init__(logger=logger,
                         wait_time=wait_time,
                         state_change_queue=state_change_queue,
                         queue_manager=queue_manager,
                         files_directory=files_directory,
                         download_files=download_files)
        self._cache: List[str] = []
        self._download_files = download_files
        self._files_directory = files_directory
        self._colour = colour
        self._author = author

    @abstractmethod
    async def _load_publications(self) -> None:
        raise NotImplementedError

    async def _create_publication_from_img(
            self,
            img: Tag,
            url: Optional[str] = None,
            rich_title: Optional[RichText] = None,
            check_cache: Optional = True,
    ) -> Optional[Publication]:
        file_name = await self._get_filename_from_url(url=img.attrs['src'])
        if file_name not in self._cache or not check_cache:
            url = url or img.attrs['src']
            file = await self._get_file_value_object(url=img.attrs['src'],
                                                     pretty_name=rich_title,
                                                     filename_unique=self._FILENAME_UNIQUE,
                                                     public_url=self._PUBLIC_URL)

            return Publication(
                publication_id=file_name,
                title=rich_title,
                url=url,
                timestamp=datetime.utcnow(),
                color=self._colour,
                images=[file],
                author=self._author,
            )
