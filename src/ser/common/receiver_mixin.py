"""Receiver Common Service Mixin Module."""

import asyncio
import os
import os.path
import time
import traceback
from abc import abstractmethod
from asyncio import Queue
from collections import OrderedDict
from typing import Dict, List, Any, Tuple

import aiofiles
import aiohttp
import databases
import orm
import sqlalchemy
from aiohttp import ClientResponse
from bs4 import BeautifulSoup
from orm import NoMatch
from orm.models import ModelMetaclass
from sqlalchemy import MetaData

from src.inf.logger.logger import Logger
from src.ser.common.abstract.attribute import AbstractAttribute
from src.ser.common.enums.format_data import FormatData
from src.ser.common.enums.state import State
from src.ser.common.itf.receiver_config import ReceiverConfig
from src.ser.common.queue_manager import QueueManager
from src.ser.common.service_mixin import ServiceMixin
from src.ser.common.value_object.file_value_object import FileValueObject
from src.ser.common.value_object.queue_context import QueueContext
from src.ser.common.value_object.receiver_common_config import ReceiverCommonConfig
from src.ser.common.value_object.task_value_object import TaskValueObject
from src.ser.common.value_object.transacation_data import TransactionData


class ReceiverMixin(ServiceMixin):
    """Receiver Common Service Mixin. This mixin include methods required by receivers services."""
    _PUBLIC_URL = AbstractAttribute()
    MODEL_IDENTIFIER: ModelMetaclass = AbstractAttribute()
    MODELS: List[ModelMetaclass] = AbstractAttribute()
    MODELS_METADATA: MetaData = AbstractAttribute()
    _CONFIG: ReceiverConfig = AbstractAttribute()
    _TITLE_HTML_TAG = 'h1'
    _MODEL_KEYS: Tuple[str] = 'id',
    _CACHE_MAX_ENTRIES = None
    _CLEAN_CACHE_FILTER = {}

    def __init__(self, receiver_common_config: ReceiverCommonConfig, receiver_custom_config: ReceiverConfig):
        self._cache: OrderedDict[Tuple[Any], orm.Model] = OrderedDict()

        self._logger = receiver_common_config.logger
        self._wait_time = receiver_custom_config.wait_time
        self._state_change_queue = receiver_common_config.state_change_queue
        self._queue_manager = receiver_common_config.queue_manager
        self._data_directory = receiver_common_config.data_directory
        self._download_files = receiver_common_config.download_files
        self._session = aiohttp.ClientSession()
        self._cache_filter_options = {}

    async def _close(self):
        await self._session.close()

    @classmethod
    def _get_queue_manager(cls, config: Dict[str, dict], senders: Dict[str, Dict[str, TaskValueObject]]):
        queue_context_list = []
        for sender_module_name, senders_configs in config.items():
            for sender_id, sender_config in senders_configs.items():
                for channel, channel_config in sender_config.items():
                    if not channel_config:
                        channel_config = {'publication_data': {}}
                    queue_context = QueueContext(
                        channel=channel,
                        publication_queue=senders[sender_module_name][sender_id].publication_queue,
                        **channel_config)
                    queue_context_list.append(queue_context)
        return QueueManager(queue_context_list=queue_context_list)

    @classmethod
    def _set_database(cls, *, instance_directory: str):
        if cls.MODELS:
            database_file = os.path.join(instance_directory, cls._DATABASE_FILE)
            database = databases.Database("sqlite:///" + database_file)

            for model in cls.MODELS:
                model.__database__ = database
            engine = sqlalchemy.create_engine(str(database.url), connect_args={'timeout': cls._DATABASE_TIMEOUT})
            cls.MODELS_METADATA.create_all(engine, checkfirst=True)

    async def _loop_manager(self, *, wait_time: int, state_change_queue: Queue) -> None:
        start = 0
        running = True
        while running:
            if (time.time() - start) > wait_time:
                try:
                    await self._load_publications()
                    await self._clean_cache()
                except:  # pylint: disable=bare-except
                    self._logger.error(traceback.format_exc())
                self._logger.debug(f"Waiting {wait_time} seconds", )
                start = time.time()
            else:
                await asyncio.sleep(self._WAIT_TIME)
                self._logger.debug(f"Remains {int(wait_time - (time.time() - start))} seconds, to execute the task.")

            if state_change_queue.empty():
                self._logger.debug("No new state.")
            else:
                new_state: State = state_change_queue.get_nowait()
                if new_state == State.STOP:
                    running = False
                else:
                    raise NotImplementedError
        await self._close()
        self._logger.info("Shutdown")

    async def _clean_cache(self):
        if self._CACHE_MAX_ENTRIES:
            to_remove = self._CACHE_MAX_ENTRIES - len(self._cache)
            if to_remove:
                for key in list(self._cache.keys())[:to_remove]:
                    del self._cache[key]

    @abstractmethod
    async def _load_publications(self) -> None:
        raise NotImplementedError

    async def _get_file_value_object(self,
                                     url: str,
                                     body_included: bool,
                                     pretty_name=None) -> FileValueObject:
        if not self._download_files:
            return FileValueObject(
                public_url=url,
                pretty_name=pretty_name,
                body_included=body_included,
            )

        path = await self._download_data(url=url)

        if self._PUBLIC_URL:
            return FileValueObject(
                path=path,
                public_url=url,
                pretty_name=pretty_name,
                body_included=body_included,
            )
        return FileValueObject(
            path=path,
            pretty_name=pretty_name,
            body_included=body_included,
        )

    async def _download_data(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                file_data = await resp.read()

        return await self._save_file(file_data=file_data, url=url)

    @staticmethod
    async def _get_filename_from_url(url: str) -> str:
        return os.path.basename(url.split('?')[0])

    async def _save_file(self, file_data: bytes, url: str) -> str:
        path = os.path.join(self._data_directory, await self._get_filename_from_url(url=url))
        async with aiofiles.open(path, mode='wb') as file:
            await file.write(file_data)
        return path

    async def run(self):
        """Run instance."""
        self._logger.info("Instance is working")
        await self._load_cache()
        await self._loop_manager(wait_time=self._wait_time, state_change_queue=self._state_change_queue)

    async def _get_site_content(self, *, url) -> bytes:
        """This method get a url and return content in bytes."""
        async with self._session.get(url) as resp:
            response = await resp.read()
            return response

    async def _get_site_head(self, *, url) -> ClientResponse:
        """This method get a url and return ClientResponse."""
        async with self._session.head(url) as resp:
            return resp

    @classmethod
    def create_tasks_from_configuration(cls, *, configuration, senders, loop, app_name, environment,
                                        logger_configuration: dict, download_files: bool):
        """Application will call this method to create tasks or only one task of each receiver service.
        Application is the responsible to pass all necessary information or configuration to create these tasks."""
        instance_value_objects: List[TaskValueObject] = []

        for configuration_item in configuration:
            receiver_config = cls._CONFIG.from_dict(configuration_item['module_config'])
            if receiver_config.instance_name:
                instance_fullname = cls._get_instance_name(receiver_config.instance_name)
            else:
                instance_fullname = cls._get_instance_name()
            instance_directory = cls._get_instance_directory(app_name=app_name,
                                                             environment=environment,
                                                             instance_name=instance_fullname)
            state_change_queue = Queue()

            cls._set_database(instance_directory=instance_directory)

            receiver_full_config = ReceiverCommonConfig(
                logger=Logger.get_logger(configuration=logger_configuration,
                                         name=instance_fullname,
                                         path=instance_directory),
                state_change_queue=state_change_queue,
                queue_manager=cls._get_queue_manager(config=configuration_item['senders'], senders=senders),
                data_directory=cls._get_sub_directory(directory=instance_directory, sub_directory=cls._DATA_DIRECTORY),
                download_files=download_files)

            instance_value_objects.append(
                TaskValueObject(
                    name=instance_fullname,
                    task=loop.create_task(cls(receiver_common_config=receiver_full_config, receiver_custom_config=receiver_config).run(), name=instance_fullname),
                    state_change_queue=state_change_queue,
                ))

        return instance_value_objects

    async def _load_cache(self) -> None:
        rows = await self.MODEL_IDENTIFIER.objects.all(**self._cache_filter_options)
        rows.sort(key=lambda x: x.last_updated)
        rows = rows[:self._CACHE_MAX_ENTRIES]
        self._cache = OrderedDict(
            (tuple(getattr(row, key) for key in self._MODEL_KEYS), row) for row in rows)

    async def _put_in_queue(self, transaction_data: TransactionData):
        for publication in transaction_data.publications:
            await self._queue_manager.put(publication=publication)
            publication_name = await self._get_format_data(data=publication.title, format_data=FormatData.PLAIN)
            self._logger.info(f"New publication: {publication_name}")

        for record in transaction_data.records:
            keys = {key: record.record_data[key] for key in self._MODEL_KEYS}
            try:
                instance = await record.model.objects.get(**keys)
                await instance.update(**record.record_data)
            except NoMatch:
                instance = await record.model.objects.create(**record.record_data)

            keys = tuple([record.record_data[key] for key in self._MODEL_KEYS])
            self._cache[keys] = instance

    @staticmethod
    def _add_html_tag(string: str, tag: str):
        soup = BeautifulSoup(features="html5lib")
        new_tag = soup.new_tag(tag)
        new_tag.string = string

        return str(new_tag)
