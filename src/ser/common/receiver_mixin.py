"""Receiver Common Service Mixin Module."""

import asyncio
import hashlib
import os
import time
import traceback
from abc import abstractmethod
from asyncio import Queue
from typing import Dict, List

import aiofiles
import aiohttp
import databases
import sqlalchemy
from aiohttp import ClientResponse
from bs4 import BeautifulSoup
from orm.models import ModelMetaclass
from sqlalchemy import MetaData

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.inf.logger.logger import Logger
from src.ser.common.abstract.attribute import AbstractAttribute
from src.ser.common.enums.environment import Environment
from src.ser.common.enums.format_data import FormatData
from src.ser.common.enums.state import State
from src.ser.common.itf.custom_config import CustomConfig
from src.ser.common.queue_manager import QueueManager
from src.ser.common.service_mixin import ServiceMixin
from src.ser.common.value_object.file_value_object import FileValueObject
from src.ser.common.value_object.queue_context import QueueContext
from src.ser.common.value_object.task_value_object import TaskValueObject
from src.ser.common.value_object.transacation_data import TransactionData


class ReceiverMixin(ServiceMixin):
    """Receiver Common Service Mixin. This mixin include methods required by receivers services."""
    MODEL_IDENTIFIER: ModelMetaclass = AbstractAttribute()
    MODELS: List[ModelMetaclass] = AbstractAttribute()
    MODELS_METADATA: MetaData = AbstractAttribute()
    _TITLE_HTML_TAG = 'h1'
    _FILES_DIRECTORY = 'files'

    # pylint: disable=too-many-arguments
    def __init__(self, logger: LoggerInterface, wait_time: int, state_change_queue: Queue, queue_manager: QueueManager,
                 files_directory: str, download_files: bool):
        self._logger = logger
        self._wait_time = wait_time
        self._state_change_queue = state_change_queue
        self._queue_manager = queue_manager
        self._files_directory = files_directory
        self._download_files = download_files
        self._session = aiohttp.ClientSession()

    async def _close(self):
        await self._session.close()

    @classmethod
    def _get_queue_manager(cls, config: Dict[str, dict], senders: Dict[str, Dict[str, TaskValueObject]]):
        queue_context_list = []
        for sender_name, senders_configs in config.items():
            for sender_id, sender_configs in senders_configs.items():
                for channel in sender_configs:
                    queue_context = QueueContext(channel=channel,
                                                 publication_queue=senders[sender_name][sender_id].publication_queue)
                    queue_context_list.append(queue_context)
        return QueueManager(queue_context_list=queue_context_list)

    @classmethod
    def _set_database(cls, *, metadata: MetaData, models: List[ModelMetaclass], app_name: str,
                      environment: Environment):
        repository_directory = cls._get_repository_directory(app_name=app_name, environment=environment)
        database_file = os.path.join(repository_directory, cls._DATABASE_FILE)
        database = databases.Database("sqlite:///" + database_file)

        for model in models:
            model.__database__ = database
        engine = sqlalchemy.create_engine(str(database.url), connect_args={'timeout': 6000000})
        metadata.create_all(engine, checkfirst=True)

    @classmethod
    def _get_repository_files_directory(cls, app_name: str, environment: Environment):
        repository_directory = cls._get_repository_directory(app_name=app_name, environment=environment)
        files_directory = os.path.join(repository_directory, cls._FILES_DIRECTORY)
        os.makedirs(files_directory, exist_ok=True)
        return files_directory

    async def _loop_manager(self, *, wait_time: int, state_change_queue: Queue) -> None:
        start = 0
        running = True
        while running:
            if (time.time() - start) > wait_time:
                try:
                    await self._load_publications()
                except:
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

    @abstractmethod
    async def _load_publications(self) -> None:
        raise NotImplementedError

    async def _get_file_value_object(self,
                                     url: str,
                                     public_url: bool,
                                     pretty_name=None,
                                     filename_unique=True) -> FileValueObject:
        if not self._download_files:
            return FileValueObject(
                public_url=url,
                pretty_name=pretty_name,
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()

        filename = await self._get_filename_from_url(url)

        if not filename_unique:
            hash_obj = hashlib.blake2b()
            hash_obj.update(data)
            filename = f"{hash_obj.hexdigest()}.{filename.split('.')[1]}"

        path = os.path.join(self._files_directory, filename)

        async with aiofiles.open(path, mode='wb') as file:
            await file.write(data)

        if public_url:
            return FileValueObject(
                path=path,
                public_url=url,
                pretty_name=pretty_name,
            )
        return FileValueObject(
            path=path,
            pretty_name=pretty_name,
        )

    @staticmethod
    async def _get_filename_from_url(url: str):
        return os.path.basename(url.split('?')[0])

    async def run(self):
        self._logger.info("Instance is working")
        await self._load_cache()
        await self._loop_manager(wait_time=self._wait_time, state_change_queue=self._state_change_queue)

    async def _get_site_content(self, *, url) -> bytes:
        """This method get a url and return content in bytes."""
        async with self._session.get(url) as resp:
            response = await resp.read()
            return response

    async def _get_site_head(self, *, url) -> ClientResponse:
        """This method get a url and return content in bytes."""
        async with self._session.head(url) as resp:
            return resp

    @classmethod
    def create_tasks_from_configuration(cls, *, configuration, senders, loop, app_name, environment,
                                        logger_configuration: dict):
        """Application will call this method to create tasks or only one task of each receiver service.
        Application is the responsible to pass all necessary information or configuration to create these tasks."""
        cls._set_database(models=cls.MODELS, metadata=cls.MODELS_METADATA, app_name=app_name, environment=environment)
        files_directory = cls._get_repository_files_directory(app_name=app_name, environment=environment)

        service_global_config = {
            'colour': configuration['colour'],
            'wait_time': configuration['wait_time'],
            'download_files': configuration['download_files'],
            'files_directory': files_directory,
        }

        service_instances_config = cls._get_custom_configuration(configuration=configuration, senders=senders)

        instance_value_objects: List[TaskValueObject] = []
        for service_instance_config in service_instances_config:
            state_change_queue = Queue()
            custom_config = service_instance_config.__dict__
            instance_name = custom_config.pop('instance_name')
            logger = Logger.get_logger(configuration=logger_configuration, name=instance_name, path=files_directory)
            task = loop.create_task(cls(
                logger=logger,
                **service_global_config,
                **custom_config,
                state_change_queue=state_change_queue,
            ).run(),
                                    name=instance_name)

            instance_value_objects.append(
                TaskValueObject(
                    name=instance_name,
                    task=task,
                    state_change_queue=state_change_queue,
                ))

        return instance_value_objects

    async def _load_cache(self) -> None:
        self._cache = [announcement.id for announcement in await self.MODEL_IDENTIFIER.objects.all()]

    @classmethod
    @abstractmethod
    def _get_custom_configuration(cls, *, configuration: dict,
                                  senders: Dict[str, Dict[str, TaskValueObject]]) -> List[CustomConfig]:
        """Method that build custom configuration for instance."""
        raise NotImplementedError

    async def _put_in_queue(self, transaction_data: TransactionData):
        for publication in transaction_data.publications:
            await self._queue_manager.put(publication=publication)
            publication_name = await self._get_format_data(data=publication.title, format_data=FormatData.PLAIN)
            self._logger.info(f"New publication: {publication_name}")
        await self.MODEL_IDENTIFIER.objects.create(id=transaction_data.transaction_id)
        self._cache.append(transaction_data.transaction_id)

    @staticmethod
    def _add_html_tag(string: str, tag: str):
        soup = BeautifulSoup(features="html5lib")
        new_tag = soup.new_tag(tag)
        new_tag.string = string

        return str(new_tag)
