"""Bot config value object."""
from dataclasses import dataclass
from typing import Dict

import discord

from src.ser.common.itf.sender_config import SenderConfig
from src.ser.discord.data.bot_activity import BotActivity
from src.ser.discord.data.channel_config import ChannelConfig


@dataclass
class DiscordConfig(SenderConfig):
    """Bot Config value object."""
    token: str
    bot_activity: BotActivity
    channels: Dict[int, ChannelConfig]

    @property
    def activity(self) -> discord.Activity:
        activity_type = getattr(discord.ActivityType, self.bot_activity.type)
        return discord.Activity(name=self.bot_activity.name, type=activity_type)
