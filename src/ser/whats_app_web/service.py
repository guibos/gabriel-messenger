import asyncio
import copy
import re
from asyncio import Queue, Task
from typing import List, Optional

import pyppeteer
import pyppeteer.browser
import pyppeteer.errors
from pyppeteer.page import Page

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.ser.common.enums.format_data import FormatData
from src.ser.common.itf.publication import Publication
from src.ser.common.sender_mixin import SenderMixin
from src.ser.common.value_object.file_value_object import FileValueObject
from src.ser.common.value_object.queue_data import QueueData


class WhatsAppWebService(SenderMixin):
    """WhatsApp Web Client."""
    MODULE = 'WhatsApp Web'
    _URL = 'https://web.whatsapp.com/'
    _HANDLE_SIGINT = False
    _MAX_TEXT_LENGTH = 65536
    _LOAD_PAGE_TIMEOUT_MS = 300000  # 5 minute
    _MAX_RETRIES = 5
    _FORMAT_DATA = FormatData.WHATS_APP

    def __init__(self, *, publication_queue: Queue, state_change_queue: Queue, logger: LoggerInterface,
                 failed_publication_directory: str):
        SenderMixin.__init__(self,
                             state_change_queue=state_change_queue,
                             publication_queue=publication_queue,
                             logger=logger,
                             failed_publication_directory=failed_publication_directory)
        self._browser: Optional[pyppeteer.browser.Browser] = None
        self._page: Optional[Page] = None
        self._publication_queue = publication_queue
        self._last_channel = None

    async def run(self, data_directory: str, headless: bool):
        """Run service"""
        self._logger.info("Instance is working")
        self._browser = await pyppeteer.launch(headless=headless, userDataDir=data_directory, handleSIGINT=False)
        self._page = await self._browser.newPage()
        await self._page.goto(self._URL)
        await self._manager()

    @classmethod
    def _create_task_from_configuration_custom(cls, instance_configuration: dict, instance_name: str,
                                               loop: asyncio.AbstractEventLoop, publication_queue: Queue,
                                               state_change_queue: Queue, failed_publication_directory,
                                               logger: LoggerInterface, **kwargs) -> Task:
        whats_app_instance = cls(
            publication_queue=publication_queue,
            state_change_queue=state_change_queue,
            failed_publication_directory=failed_publication_directory,
            logger=logger,
        )
        data_directory = cls._get_sub_directory(directory=kwargs['directory_files'], sub_directory=cls._DATA_DIRECTORY)
        return loop.create_task(whats_app_instance.run(
            headless=kwargs['configuration']['headless'],
            data_directory=data_directory,
        ),
                                name=instance_name)

    async def _load_publication(self, *, queue_data: QueueData) -> None:
        queue_data_copy = copy.deepcopy(queue_data)
        for _ in range(0, self._MAX_RETRIES):
            try:
                return await self._load_publication_web(queue_data_copy)
            except pyppeteer.errors.TimeoutError:
                a = 1

    async def _load_publication_web(self, queue_data: QueueData) -> None:
        await self._set_channel(queue_data.channel)
        await self._send_images(queue_data.publication.images[1:])
        await asyncio.sleep(1)
        await self._send_main_message(queue_data.publication)
        await self._send_files(queue_data.publication.files)

    async def _set_channel(self, channel_name: str) -> None:
        if self._last_channel != channel_name:
            await self._search_channel(channel_name=channel_name)
            await self._click_channel(channel_name=channel_name)

    async def _search_channel(self, channel_name: str) -> None:
        search = await self._page.waitForSelector('[data-icon="search"]',
                                                  options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await search.click()  # remove text on search bar
        await self._page.type('[data-tab="3"]', channel_name)

    async def _click_channel(self, channel_name: str) -> None:
        channel = await self._page.waitForSelector(f'[title="{channel_name}"]',
                                                   options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await asyncio.sleep(1)  # Javascript Rules
        await channel.click()

    async def _send_main_message(self, publication: Publication) -> None:
        text = publication.to_format(format_data=self._FORMAT_DATA)
        text_chunks = await self._get_text_chunks(text, max_length=self._MAX_TEXT_LENGTH)
        first_iteration = True
        for text_chunk in text_chunks:
            # Is required evaluate each iteration if message box is available. Because if image is sent this could be
            #  not available.
            message_box = await self._page.waitForSelector(f'[data-tab="1"]',
                                                           options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
            await message_box.click()
            for paragraph_lf in re.split(r'(\n)', text_chunk):
                if paragraph_lf == '\n':
                    await self._page.keyboard.down('Shift')
                    await self._page.keyboard.down('Enter')
                    await self._page.keyboard.up('Shift')
                    await self._page.keyboard.up('Enter')
                else:
                    await message_box.type(paragraph_lf)
            if first_iteration and publication.images:
                await asyncio.sleep(1)  # Javascript Rules
                await self._attach_click()
                await self._attach_image(publication.images[0])
                await asyncio.sleep(1)
                first_iteration = False
                await self._send_image()
            elif text_chunk:
                await self._send_text()

    async def _send_images(self, images: List[FileValueObject]) -> None:
        for file in images:
            await self._attach_click()
            await self._attach_image(file)
            await asyncio.sleep(1)
            await self._send_image()

    async def _send_files(self, files: List[FileValueObject]) -> None:
        for file in files:
            await self._attach_click()
            await self._attach_file(file)
            await self._send_image()

    async def _attach_image(self, image: FileValueObject) -> None:
        input_image = await self._page.waitForSelector('[accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
                                                       options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await input_image.uploadFile(image.path)

    async def _attach_file(self, file: FileValueObject) -> None:
        input_image = await self._page.waitForSelector('[accept="*"]', options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await input_image.uploadFile(file.path)

    async def _attach_click(self) -> None:
        attach_icon = await self._page.waitForSelector(f'[data-icon="clip"]',
                                                       options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await attach_icon.click()

    async def _send_image(self) -> None:
        send_icon = await self._page.waitForSelector(f'[data-icon="send-light"]',
                                                     options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await send_icon.click()

    async def _send_text(self) -> None:
        send_icon = await self._page.waitForSelector(f'[data-icon="send"]',
                                                     options={'timeout': self._LOAD_PAGE_TIMEOUT_MS})
        await send_icon.click()

    async def _close(self) -> None:
        await self._browser.close()