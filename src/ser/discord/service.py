"""Discord Client Module"""
import asyncio
import re
from asyncio import Queue, AbstractEventLoop, Task
from typing import Dict, Any, List, Optional

import discord
from discord import File

from src.inf.logger.itf.logger_interface import LoggerInterface
from src.ser.common.enums.format_data import FormatData
from src.ser.common.sender_mixin import SenderMixin
from src.ser.common.value_object.queue_data import QueueData
from src.ser.discord.data.bot_config import BotConfig
from src.ser.discord.data.channel_config import ChannelConfig
from src.ser.discord.data.reaction_change_config import ReactionChangeConfig
from src.ser.discord.data.reaction_config import ReactionConfig
from src.ser.discord.data.reporting_channel_config import ReportingChannelConfig


class DiscordService(discord.Client, SenderMixin):
    """Discord Client."""
    MODULE = 'Discord'
    _MAX_DESCRIPTION_LENGTH = 2000
    _FORMAT_DATA = FormatData.PLAIN
    _REQUIRED_DOWNLOAD_FILES = True

    def __init__(self, *, config: BotConfig, loop: AbstractEventLoop, publication_queue: Queue,
                 state_change_queue: Queue, logger: LoggerInterface, failed_publication_directory: str):
        discord.Client.__init__(self, loop=loop)
        SenderMixin.__init__(self,
                             state_change_queue=state_change_queue,
                             publication_queue=publication_queue,
                             logger=logger,
                             failed_publication_directory=failed_publication_directory)
        self._config = config
        self._publication_queue = publication_queue
        self._channels: Dict[int, discord.TextChannel] = {}

    async def on_ready(self):
        """On ready: create tasks"""
        self._logger.info("Instance is working")
        await self.change_presence(activity=self._config.activity)
        self.loop.create_task(self._manager())

    @classmethod
    def _create_task_from_configuration_custom(cls, instance_configuration: dict, instance_name: str,
                                               loop: asyncio.AbstractEventLoop, publication_queue: Queue,
                                               state_change_queue: Queue, failed_publication_directory,
                                               logger: LoggerInterface, **kwargs) -> Task:
        bot_config = BotConfig(
            activity=cls._get_activity(activity_configuration=instance_configuration['activity']),
            channels_config=cls._get_channels_config(channels_config=instance_configuration['channels']),
            clean_channels=instance_configuration['clean_channels'],
            reporting_channels=instance_configuration['reporting_channels'])
        discord_instance = cls(
            config=bot_config,
            loop=loop,
            publication_queue=publication_queue,
            state_change_queue=state_change_queue,
            failed_publication_directory=failed_publication_directory,
            logger=logger,
        )
        return loop.create_task(discord_instance.start(instance_configuration['token']), name=instance_name)

    @staticmethod
    def _get_activity(activity_configuration: dict) -> discord.Activity:
        activity_type = getattr(discord.ActivityType, activity_configuration['type'])
        activity_name = activity_configuration['name']
        return discord.Activity(name=activity_name, type=activity_type)

    @classmethod
    def _get_channels_config(cls, *, channels_config: Dict[int, dict]) -> Dict[int, ChannelConfig]:
        return {
            channel_id: ChannelConfig(reactions=channel_config['reactions'],
                                      reporting_channels_config=cls._get_reporting_channels_config(
                                          config=channel_config['reporting_channels']))
            for channel_id, channel_config in channels_config.items()
        }

    @classmethod
    def _get_reporting_channels_config(cls, *, config: Dict[int, dict]) -> Dict[int, ReportingChannelConfig]:
        return {
            channel_id: ReportingChannelConfig(
                reactions=cls._get_reporting_channels_reactions_config(config=reporting_channels_config['reactions']),
                description=reporting_channels_config['description'],
                footer=reporting_channels_config['footer'],
            )
            for channel_id, reporting_channels_config in config.items()
        }

    @classmethod
    def _get_reporting_channels_reactions_config(cls, *, config: Dict[str, Any]) -> Dict[str, ReactionConfig]:
        return {
            reaction: ReactionConfig(
                text=reaction_config['text'],
                reaction_add=ReactionChangeConfig(**(reaction_config.get('reaction_add') or {})),
                reaction_remove=ReactionChangeConfig(**(reaction_config.get('reaction_remove') or {})),
            )
            for reaction, reaction_config in config.items()
        }

    async def _load_publication(self, *, queue_data: QueueData) -> None:
        channel = await self._get_channel(channel_id=queue_data.channel)
        if queue_data.publication.description:
            description = queue_data.publication.description.to_format(format_data=self._FORMAT_DATA)
            description_chunks = await self._get_text_chunks(description, self._MAX_DESCRIPTION_LENGTH)
        else:
            description_chunks = [None]
        iteration = 1

        embed_optional_config: Dict[str, Any] = {}
        if queue_data.publication.colour:
            embed_optional_config['colour'] = queue_data.publication.colour

        for description_chunk in description_chunks:
            embed = discord.Embed(
                title=await self._get_format_data(data=queue_data.publication.title, format_data=self._FORMAT_DATA),
                description=description_chunk,
                url=queue_data.publication.url,
                **embed_optional_config,
            )
            if queue_data.publication.timestamp:
                embed.timestamp = queue_data.publication.timestamp

            if queue_data.publication.author:
                embed.set_author(name=queue_data.publication.author.name,
                                 url=queue_data.publication.author.url,
                                 icon_url=queue_data.publication.author.icon_url)

            await self._first_iteration(iteration=iteration, queue_data=queue_data, embed=embed)
            file = await self._last_iteration(iteration=iteration,
                                              description_chunks=description_chunks,
                                              queue_data=queue_data,
                                              embed=embed)

            await channel.send(embed=embed, file=file)
            iteration += 1
        await self._send_extras(queue_data=queue_data, channel=channel)

    @staticmethod
    async def _first_iteration(iteration: int, queue_data: QueueData, embed: discord.Embed):
        if iteration == 1:
            if queue_data.publication.custom_fields:
                for field in queue_data.publication.custom_fields:
                    if field:
                        embed.add_field(name=field.name, value=field.value)

    async def _last_iteration(self, iteration: int, description_chunks: List[str], queue_data: QueueData,
                              embed: discord.Embed) -> Optional[File]:
        file = None
        if iteration == len(description_chunks):
            if queue_data.publication.images:
                if queue_data.publication.images[0].public_url:
                    embed.set_image(url=queue_data.publication.images[0].public_url)
                else:
                    pretty_name = await self._clean_file_name(string=queue_data.publication.images[0].pretty_filename)
                    embed.set_image(url=f"attachment://{pretty_name}")
                    file = File(queue_data.publication.images[0].path, filename=pretty_name)
        return file

    async def _send_extras(self, queue_data: QueueData, channel: discord.TextChannel):
        if queue_data.publication.images:
            for image in queue_data.publication.images[1:]:
                pretty_name = await self._clean_file_name(string=image.pretty_filename)
                file = File(image.path, filename=pretty_name)
                await channel.send(file=file)

        for publication_file in queue_data.publication.files:
            pretty_name = await self._clean_file_name(string=publication_file.pretty_filename)
            file = File(publication_file.path, filename=pretty_name)
            await channel.send(file=file)

    async def _get_channel(self, *, channel_id) -> discord.TextChannel:
        channel = self._channels.get(channel_id)
        if not channel:
            channel = self.get_channel(channel_id)
            self._channels[channel_id] = channel
        if not channel:
            raise EnvironmentError(f'Wrong Channel id: {channel_id}')
        return channel

    async def _close(self):
        await self.logout()

    async def on_message(self, message):
        """Receive message that some user send to discord."""
        self._logger.debug(message)

    @staticmethod
    async def _clean_file_name(string: str):
        return re.sub(r'[^[A-z0-9_\.]', r'', string.replace(' ', '_'))
