"""Application Module."""
import asyncio
import logging
import signal
from typing import Tuple, Dict, Union, List

from src.inf.configuration.configuration import Configuration
from src.ser.blackfire.service import BlackfireService
from src.ser.common.enums.state import State
from src.ser.common.receiver_mixin import ReceiverMixin
from src.ser.common.sender_mixin import SenderMixin
from src.ser.common.value_object.task_value_object import TaskValueObject
from src.ser.discord.service import DiscordService
from src.ser.ws_banner.service import WSBannerService
from src.ser.ws_news.service import WSNews
from src.ser.ws_today_card.service import WSTodayCard
from src.ser.ws_tournament_en.service import WSTournamentEn
from src.ser.ws_tournament_jp.service import WSTournamentJp


class Application:
    """Application class. The one in charge of governing all the modules."""
    _APP_NAME = 'GabrielMessenger'
    _SLEEPING_SECONDS = 5
    _SENDERS: Tuple[SenderMixin] = (DiscordService, )
    _RECEIVERS: Tuple[ReceiverMixin] = (
        BlackfireService,
        WSBannerService,
        WSNews,
        WSTodayCard,
        WSTournamentEn,
        WSTournamentJp,
    )

    def __init__(self, configuration: Configuration):
        self._logger = logging.getLogger(self._APP_NAME)
        self._logger.setLevel(configuration.get_global_configuration()['app_logging_level'])
        self._environment = configuration.get_global_configuration()['environment']
        self._loop = asyncio.get_event_loop()
        self._loop.add_signal_handler(signal.SIGINT, self._clean_shutdown)
        self._senders_repositories_instances_value_objects = self._get_senders(
            config=configuration.get_modules()['sender'], loop=self._loop, configuration=configuration)
        self._receivers_repositories_instances_value_objects = self._get_receivers(
            config=configuration.get_modules()['receiver'],
            senders=self._senders_repositories_instances_value_objects,
            logging_level=configuration.get_global_configuration()['app_logging_level'],
            loop=self._loop,
        )

    def _get_senders(self, *, config: Dict, loop: asyncio.AbstractEventLoop,
                     configuration: Configuration) -> Dict[str, Dict[str, TaskValueObject]]:
        return {
            sender_name: self._get_sender_class(sender_name=sender_name).create_tasks_from_configuration(
                configuration=sender_config,
                loop=loop,
                logging_level=configuration.get_global_configuration()['app_logging_level'])
            for sender_name, sender_config in config.items()
        }

    def _get_receivers(self, *, config: dict, senders: Dict[str, Dict[str, TaskValueObject]], logging_level: str,
                       loop: asyncio.AbstractEventLoop) -> List[TaskValueObject]:
        tasks = []
        for receiver_name, receiver_config in config.items():
            tasks.extend(
                self._get_receiver_class(receiver_name=receiver_name).create_tasks_from_configuration(
                    configuration=receiver_config,
                    senders=senders,
                    loop=loop,
                    app_name=self._APP_NAME,
                    environment=self._environment,
                    logging_level=logging_level))
        return tasks

    def _get_sender_class(self, *, sender_name: str) -> SenderMixin:
        return self._get_class(tuple_class=self._SENDERS, name_class=sender_name)

    def _get_receiver_class(self, *, receiver_name: str) -> ReceiverMixin:
        return self._get_class(tuple_class=self._RECEIVERS, name_class=receiver_name)

    @staticmethod
    def _get_class(*, tuple_class: Tuple[Union[ReceiverMixin, SenderMixin]],
                   name_class: str) -> Union[ReceiverMixin, SenderMixin]:
        for class_item in tuple_class:
            if class_item.MODULE == name_class:
                return class_item
        raise EnvironmentError(f"NameClass: {name_class} is not defined.")

    def run(self):
        """Run Application. Run until complete all task of all services."""
        self._loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
        self._logger.info("Shutdown.")

    def _clean_shutdown(self):
        """Handler that will be activated when app receives a SIGINT signal. This create a task to programming a clean
        shutdown."""
        self._logger.info("Starting shutdown.")
        self._loop.create_task(self._clean())

    async def _clean(self):
        """Method that will be called as a Task, when user wants to end execution of the app. This task send to all
        services a stop flag in "state change queue". When all services are finished, this task will be completed, and
        app will be completed."""
        await self._clean_receivers()
        await self._clean_senders()
        self._logger.info("Cleaned all services.")
        return

    async def _clean_receivers(self):
        """This method send to all receiver services a stop flag in "state change queue". When all receiver services
        are finished, this method will be completed."""
        self._logger.info("Cleaning Receivers.")
        await self._send_stop_flag_tasks(
            repositories_instances_value_objects=self._receivers_repositories_instances_value_objects)
        await self._check_tasks_finished(
            repositories_instances_value_objects=self._receivers_repositories_instances_value_objects)
        self._logger.info("Cleaned Receivers.")

    async def _clean_senders(self):
        """This method send to all senders services a stop flag in "state change queue". When all receiver services
        are finished, this method will be completed."""
        self._logger.info("Cleaning Senders.")
        senders = []
        for repository_dict_instance in self._senders_repositories_instances_value_objects.values():
            senders.extend(repository_dict_instance.values())

        await self._send_stop_flag_tasks(repositories_instances_value_objects=senders)
        await self._check_tasks_finished(repositories_instances_value_objects=senders)
        self._logger.info("Cleaned Senders.")

    @staticmethod
    async def _send_stop_flag_tasks(*, repositories_instances_value_objects: List[TaskValueObject]):
        await asyncio.gather(
            *[value_object.state_change_queue.put(State.STOP) for value_object in repositories_instances_value_objects])

    async def _check_tasks_finished(self, *, repositories_instances_value_objects: List[TaskValueObject]):
        while True:
            are_finished = True
            for value in repositories_instances_value_objects:
                if not value.task.done():
                    self._logger.info('Task: "%s" is currently working.', value.name)
                    are_finished = False
            if are_finished:
                break
            self._logger.info("Sleeping %s seconds.", self._SLEEPING_SECONDS)
            await asyncio.sleep(5)
