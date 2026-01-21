from MyClient import AppConfig

# This is to check if the guild ID is in the config
def is_guild_in_config(config: AppConfig, guild_id: int):

    guild_ids: dict = config.get("guilds")

    if guild_id in guild_ids.values():
        return True
    else:
        return False
    
def is_rr_message_id_in_config(config: AppConfig, guild_name: str):

    guild_role_message_ids: dict = config.get("guild role messages")

    if guild_name in guild_role_message_ids.keys():
        return True
    else:
        return False

def get_channel_id(config: AppConfig, guild_name: str, channel: str):

    channels = config.get("channels").get(channel)

    if channels is None:
        return "Channel not in config"
    
    channels = channels.get(guild_name)

    if channels is None:
        return "Channel does not exist in the server"
    else:
        return int(channels)