"""Discord Client Module"""
import copy
import mimetypes
import re
from typing import Dict, List, Tuple

import discord

from src.ser.common.enums.format_data import FormatData
from src.ser.common.sender_mixin import SenderMixin
from src.ser.common.value_object.file_value_object import FileValueObject
from src.ser.common.value_object.queue_data import QueueData
from src.ser.common.value_object.sender_common_config import SenderCommonConfig
from src.ser.discord.data.discord_config import DiscordConfig


class DiscordService(discord.Client, SenderMixin):
    """Discord Client."""
    MODULE = 'Discord'
    _MAX_DESCRIPTION_LENGTH = 2000
    _FORMAT_DATA = FormatData.PLAIN
    REQUIRED_DOWNLOAD_FILES = True

    _ALLOWED_IMAGE_PREVIEW = 'image/png', 'image/jpeg', 'image/gif'

    _CONFIG = DiscordConfig

    def __init__(self, *, sender_common_config: SenderCommonConfig, sender_config: DiscordConfig):
        discord.Client.__init__(self, loop=sender_common_config.loop)
        SenderMixin.__init__(self, sender_common_config, sender_config=sender_config)
        self._sender_config = sender_config
        self._channels: Dict[int, discord.TextChannel] = {}

    async def on_ready(self):
        """On ready: create tasks"""
        self._logger.info("Instance is working")
        await self.change_presence(activity=self._sender_config.activity)
        self.loop.create_task(self._manager())

    async def run(self):
        await self.start(self._sender_config.token)

    async def _load_publication(self, *, queue_data: QueueData) -> None:
        embed_file = None
        iteration = 1

        files = copy.deepcopy(queue_data.publication.files)

        channel = await self._get_channel(channel_id=queue_data.channel)

        description_chunks = await self._get_description_chunks(queue_data=queue_data)

        for description_chunk in description_chunks:
            embed = discord.Embed(
                title=await self._get_format_data(data=queue_data.publication.title, format_data=self._FORMAT_DATA),
                description=description_chunk,
                url=queue_data.publication.url,
            )

            if queue_data.publication.author:
                embed.set_author(name=queue_data.publication.author.name,
                                 url=queue_data.publication.author.url,
                                 icon_url=queue_data.publication.author.icon_url)

            await self._first_iteration(iteration=iteration, queue_data=queue_data, embed=embed)

            if iteration == len(description_chunks):
                embed_file, files = await self._get_first_image_allowed_preview(files=files, embed=embed)
            await channel.send(embed=embed,
                               file=embed_file
                               )
            iteration += 1
        await self._send_extras(files=files, channel=channel)

    async def _get_description_chunks(self, queue_data: QueueData) -> List[str]:
        if queue_data.publication.description:
            description = queue_data.publication.description.to_format(format_data=self._FORMAT_DATA)
            description_chunks = await self._get_text_chunks(description, self._MAX_DESCRIPTION_LENGTH)
        else:
            description_chunks = [None]
        return description_chunks

    @staticmethod
    async def _first_iteration(iteration: int, queue_data: QueueData, embed: discord.Embed):
        if iteration == 1:
            if queue_data.publication.custom_fields:
                for field in queue_data.publication.custom_fields:
                    embed.add_field(name=field.name, value=field.value)

    async def _get_first_image_allowed_preview(
            self,
            files: List[FileValueObject],
            embed: discord.Embed) -> Tuple[discord.File, List[FileValueObject]]:

        embed_file = None
        for file in files:
            path = file.public_url or file.path
            if mimetypes.guess_type(path)[0] not in self._ALLOWED_IMAGE_PREVIEW:
                continue
            if file.public_url:
                embed.set_image(url=file.public_url)
            else:
                pretty_name = await self._clean_file_name(string=file.pretty_filename)
                embed.set_image(url=f"attachment://{pretty_name}")
                embed_file = discord.File(file.path, filename=pretty_name)
            files.remove(file)
            break
        return embed_file, files

    async def _send_extras(self, files: List[FileValueObject], channel: discord.TextChannel):
        for file in files:
            pretty_name = await self._clean_file_name(string=file.pretty_filename)
            file = discord.File(file.path, filename=pretty_name)
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
        return re.sub(r'[^[A-z0-9_.]', r'', string.replace(' ', '_'))
