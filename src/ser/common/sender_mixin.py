"""Sender Mixin Module"""

import asyncio
import os
import pickle
import traceback
from abc import abstractmethod
from asyncio import Queue, Task
from datetime import datetime
from typing import Optional

import aiofiles
import aiofiles.os

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.inf.logger.logger import Logger
from src.ser.common.enums.environment import Environment
from src.ser.common.enums.state import State
from src.ser.common.service_mixin import ServiceMixin
from src.ser.common.value_object.queue_data import QueueData
from src.ser.common.value_object.task_value_object import TaskValueObject


class SenderMixin(ServiceMixin):
    """Sender Common Service Mixin. This mixin include methods required by senders services."""
    _FAILED_PUBLICATIONS = 'failed_publciations'

    def __init__(self, state_change_queue: Queue, logger: LoggerInterface, publication_queue: Queue,
                 failed_publication_directory: str):
        self._state_change_queue = state_change_queue
        self._logger = logger
        self._publication_queue = publication_queue
        self._failed_publication_directory = failed_publication_directory

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
                # FIXME: this is not async currently aiofiles pypi version is not updated. Github version
                #  include a wrapper.
                os.remove(path)
            except:
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
        except:
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

    @classmethod
    def create_tasks_from_configuration(cls, *, configuration, loop, logging_level, app_name: str,
                                        environment: Environment, logger_configuration: dict):
        """Application will call this method to create tasks or only one task of each sender service. Application is the
        responsible to pass all necessary information or configuration to create these tasks."""
        repository_instances_value_objects = {}
        directory_files = cls._get_repository_directory(app_name=app_name, environment=environment)
        failed_publication_directory = cls._get_failed_publication_directory(app_name=app_name, environment=environment)
        for key_name, configuration_item in configuration.items():
            publication_queue = Queue()
            state_change_queue = Queue()

            instance_name = cls._get_instance_name(key_name)
            logger = Logger.get_logger(configuration=logger_configuration, name=instance_name, path=directory_files)

            task = cls._create_task_from_configuration_custom(
                configuration_item=configuration_item,
                instance_name=instance_name,
                loop=loop,
                publication_queue=publication_queue,
                state_change_queue=state_change_queue,
                logging_level=logging_level,
                failed_publication_directory=failed_publication_directory,
                logger=logger,
            )

            repository_instances_value_objects[key_name] = TaskValueObject(name=instance_name,
                                                                           state_change_queue=state_change_queue,
                                                                           publication_queue=publication_queue,
                                                                           task=task)
        return repository_instances_value_objects

    # pylint: disable=too-many-arguments
    @classmethod
    @abstractmethod
    def _create_task_from_configuration_custom(cls, configuration_item: dict, instance_name: str,
                                               loop: asyncio.AbstractEventLoop, publication_queue: Queue,
                                               state_change_queue: Queue, logging_level: str,
                                               failed_publication_directory: str, logger: LoggerInterface) -> Task:
        """Generate Task for a item in configuration."""
        raise NotImplementedError

    @abstractmethod
    async def _close(self) -> None:
        raise NotImplementedError

    @classmethod
    def _get_failed_publication_directory(cls, app_name: str, environment: Environment):
        """This return a path string, where it's possible to strore pickle """
        repository_directory = cls._get_repository_directory(app_name=app_name, environment=environment)
        failed_publication_directory = os.path.join(repository_directory, cls._FAILED_PUBLICATIONS)
        os.makedirs(failed_publication_directory, exist_ok=True)
        return failed_publication_directory
