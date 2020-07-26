"""Sender Mixin Module"""

import asyncio
import os
import pickle
import re
import traceback
from abc import abstractmethod
from asyncio import Queue, Task
from datetime import datetime
from typing import Optional, List, Coroutine

import aiofiles
import aiofiles.os

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.inf.logger.logger import Logger
from src.ser.common.abstract.attribute import AbstractAttribute
from src.ser.common.enums.environment import Environment
from src.ser.common.enums.state import State
from src.ser.common.itf.sender_config import SenderConfig
from src.ser.common.service_mixin import ServiceMixin
from src.ser.common.value_object.queue_data import QueueData
from src.ser.common.value_object.sender_common_config import SenderCommonConfig
from src.ser.common.value_object.task_value_object import TaskValueObject


class SenderMixin(ServiceMixin):  # pylint: disable=too-few-public-methods
    """Sender Common Service Mixin. This mixin include methods required by senders services."""
    _FAILED_PUBLICATIONS = 'failed-publications'
    REQUIRED_DOWNLOAD_FILES = AbstractAttribute()
    _CONFIG: SenderConfig = AbstractAttribute()

    def __init__(self, sender_common_config: SenderCommonConfig, sender_config: SenderConfig):
        self._state_change_queue = sender_common_config.state_change_queue
        self._logger = sender_common_config.logger
        self._publication_queue = sender_common_config.publication_queue
        self._failed_publication_directory = sender_common_config.failed_publication_directory
        self._sender_config = sender_config

    async def _manager(self):
        await self._load_failed_publications()
        await self._loop_manager()

    async def _load_failed_publications(self):
        failed_publications_files = os.listdir(self._failed_publication_directory)
        for failed_publication_file in failed_publications_files:
            path = os.path.join(self._failed_publication_directory, failed_publication_file)
            async with aiofiles.open(path, mode='rb') as file:
                data = await file.read()
            queue_data: QueueData = pickle.loads(data)
            try:
                await self._load_publication(queue_data=queue_data)
                await aiofiles.os.remove(path)
            except:  # pylint: disable=bare-except
                self._logger.error(traceback.format_exc())

    async def _loop_manager(self):
        running = True
        while running:
            if self._publication_queue.empty():
                state: Optional[State] = await self._new_state()
                if state == State.STOP:
                    await self._close()
                    self._logger.info("Shutdown.")
                    running = False
                elif state is None:
                    await asyncio.sleep(self._WAIT_TIME)
                else:
                    raise NotImplementedError
            else:
                await self._new_publication()

    async def _new_publication(self):
        queue_data: QueueData = await self._publication_queue.get()
        try:
            await self._load_publication(queue_data=queue_data)
        except:  # pylint: disable=bare-except
            self._logger.error(traceback.format_exc())
            file_path = os.path.join(self._failed_publication_directory, f'{datetime.now().isoformat()}.p')
            async with aiofiles.open(file_path, mode='wb') as file:
                await file.write(pickle.dumps(queue_data))

    async def _new_state(self):
        self._logger.debug("No publications.")
        if not self._state_change_queue.empty():
            return await self._state_change_queue.get()
        self._logger.debug("No new state.")

    @abstractmethod
    async def _load_publication(self, *, queue_data) -> None:
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> Coroutine:
        raise NotImplementedError

    @classmethod
    def create_tasks_from_configuration(cls, *, configuration, loop, app_name: str, environment: Environment,
                                        logger_configuration: dict):
        """Application will call this method to create tasks or only one task of each sender service. Application is the
        responsible to pass all necessary information or configuration to create these tasks."""
        repository_instances_value_objects = {}

        for instance_entry_name, instance_configuration in configuration['instances'].items():
            instance_directory = cls._get_instance_directory(app_name=app_name,
                                                             environment=environment,
                                                             instance_name=instance_entry_name)
            publication_queue = Queue()
            state_change_queue = Queue()

            instance_name = cls._get_instance_name(instance_entry_name)
            logger = Logger.get_logger(
                configuration=logger_configuration, name=instance_name, path=instance_directory)

            sender_common_config = SenderCommonConfig(
                loop=loop,
                publication_queue=publication_queue,
                state_change_queue=state_change_queue,
                logger=logger,
                failed_publication_directory=cls._get_sub_directory(
                                                                  directory=instance_directory,
                                                                  sub_directory=cls._FAILED_PUBLICATIONS)
            )

            sender_config = cls._CONFIG.from_dict(instance_configuration)

            instance = cls(sender_common_config=sender_common_config, sender_config=sender_config)
            task = loop.create_task(instance.run())

            repository_instances_value_objects[instance_entry_name] = TaskValueObject(
                name=instance_name,
                state_change_queue=state_change_queue,
                publication_queue=publication_queue,
                task=task)
        return repository_instances_value_objects

    @abstractmethod
    async def _close(self) -> None:
        raise NotImplementedError

    @classmethod
    def _get_failed_publication_instance_directory(cls, app_name: str, environment: Environment, instance_name: str):
        """This return a path string, where it's possible to strore pickle """
        repository_directory = cls._get_instance_directory(app_name=app_name,
                                                           environment=environment,
                                                           instance_name=instance_name)
        failed_publication_directory = os.path.join(repository_directory, cls._FAILED_PUBLICATIONS)
        os.makedirs(failed_publication_directory, exist_ok=True)
        return failed_publication_directory

    @staticmethod
    async def _get_text_chunks(text: str, max_length: int) -> List[str]:
        final = []
        previous_text = ''
        for paragraph in re.split(r'(\n)', text):
            if (len(previous_text) + len(paragraph)) > max_length:
                final.append(previous_text)
                previous_text = ''

            if len(paragraph) < max_length:
                previous_text = previous_text + paragraph
            else:
                for word in re.split(r'( )', paragraph):
                    if (len(previous_text) + len(word)) > max_length:
                        final.append(previous_text)
                        previous_text = ''
                    else:
                        previous_text = previous_text + word
        final.append(previous_text)
        return final
