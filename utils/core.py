from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class AppConfig(BaseModel):
    guilds: dict[str, int]
    roles: dict[str, dict[str, int]]
    channels: dict[str, dict[str, int]]
    guild_role_messages: dict[str, dict[str, int]]
    birthday_message: dict[str, bool]
    boost: bool
    boost_amount: int
    time_per_loop: int
    set_up_done: dict[str, bool]

    def to_yaml_dict(self) -> dict:
        """App config to dictionary"""
        return {
            "guilds": self.guilds,
            "roles": self.roles,
            "channels": self.channels,
            "guild role messages": self.guild_role_messages,
            "birthday message": self.birthday_message,
            "boost": self.boost,
            "boost amount": self.boost_amount,
            "time per loop": self.time_per_loop,
            "set up done": self.set_up_done
        }

# This is to check if the guild ID is in the config
def is_guild_in_config(config: AppConfig, guild_id: int):

    guild_ids: dict = config.guilds

    if guild_id in guild_ids.values():
        return True
    else:
        return False
    
def is_rr_message_id_in_config(config: AppConfig, guild_name: str):

    guild_role_message_ids: dict = config.guild_role_messages

    if guild_name in guild_role_message_ids.keys():
        return True
    else:
        return False

def get_channel_id(config: AppConfig, guild_name: str, channel: str):

    channels = config.channels
    channels = channels.get(channel)

    if channels is None:
        return "Channel not in config"
    
    channels = channels.get(guild_name)

    if channels is None:
        return "Channel does not exist in the server"
    else:
        return int(channels)