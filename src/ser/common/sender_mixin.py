"""Sender Mixin Module"""

import asyncio
from abc import abstractmethod
from asyncio import Queue, QueueEmpty, Task
from logging import Logger
from typing import Optional

from src.ser.common.enums.state import State
from src.ser.common.rich_text import RichText
from src.ser.common.service_mixin import ServiceMixin
from src.ser.common.value_object.queue_data import QueueData
from src.ser.common.value_object.task_value_object import TaskValueObject


class SenderMixin(ServiceMixin):
    """Sender Common Service Mixin. This mixin include methods required by senders services."""
    async def _loop_manager(self, *, state_change_queue: Queue, logger: Logger, publication_queue: Queue):
        while True:
            try:
                queue_data: QueueData = publication_queue.get_nowait()
                await self._load_publication(queue_data=queue_data)
            except QueueEmpty:
                logger.debug("No publications.")
                try:
                    new_state: State = state_change_queue.get_nowait()
                    if new_state == State.STOP:
                        await self._close()
                        logger.info("Shutdown.")
                        return
                    raise NotImplementedError
                except QueueEmpty:
                    logger.debug("No new state.")

            await asyncio.sleep(self._WAIT_TIME)

    @abstractmethod
    async def _load_publication(self, *, queue_data) -> None:
        raise NotImplementedError

    @classmethod
    def create_tasks_from_configuration(cls, *, configuration, loop, logging_level):
        """Application will call this method to create tasks or only one task of each sender service. Application is the
        responsible to pass all necessary information or configuration to create these tasks."""
        repository_instances_value_objects = {}
        for key_name, configuration_item in configuration.items():
            publication_queue = Queue()
            state_change_queue = Queue()

            instance_name = cls._get_instance_name(key_name)

            task = cls._create_task_from_configuration_custom(
                configuration_item=configuration_item,
                instance_name=instance_name,
                loop=loop,
                publication_queue=publication_queue,
                state_change_queue=state_change_queue,
                logging_level=logging_level,
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
                                               state_change_queue: Queue, logging_level: str) -> Task:
        """Generate Task for a item in configuration."""
        raise NotImplementedError

    @abstractmethod
    async def _close(self) -> None:
        raise NotImplementedError
