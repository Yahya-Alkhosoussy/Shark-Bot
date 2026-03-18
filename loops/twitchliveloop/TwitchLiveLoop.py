import logging

import discord
from discord.ext import tasks

from SQL.socialMedia.twitchLive import get_custom_message, get_live_status, get_users, update_live_status
from utils.core import AppConfig
from utils.pullingFromTwitch import get_profile_picture, get_stream_details, is_live


class TwitchLiveLoop:
    def __init__(self, bot: discord.Client, config: AppConfig):
        self.bot = bot
        self.config = config
        self._loops: dict[int, tasks.Loop] = {}  # guild_id -> tasks.Loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns None if it's empty
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        async def _tick():
            users = get_users()
            for user in users:
                saved_live_status: bool = get_live_status(user)
                new_live_status: bool = is_live(username=user)
                if saved_live_status != new_live_status and (not saved_live_status):
                    update_live_status(username=user, status=new_live_status)
                    live_link = f"www.twitch.tv/{user}"
                    custom_message = get_custom_message(user)
                    details = get_stream_details(user)
                    if details is not None:
                        title, game_name = details
                    else:
                        continue
                    embed_to_send = discord.Embed(
                        title=f"{user} is live on Twitch! Go check them out!",
                        colour=discord.Color(0xF6A6BB),
                        description=f"[{title}]({live_link})",
                    )
                    profile_url = get_profile_picture(username=user)
                    embed_to_send.set_thumbnail(url=profile_url)
                    embed_to_send.add_field(name="Game", value=game_name)
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Watch Stream", url=live_link))
                    channel_id = self.config.get_channel_id("shark squad", "live")
                    guild = self.bot.get_guild(guild_id)
                    if guild is None:
                        logging.error("GUILD IS NOT FOUND")
                        continue
                    channel = guild.get_channel(channel_id)
                    if isinstance(channel, discord.TextChannel):
                        await channel.send(content=custom_message, embed=embed_to_send, view=view)

        loop = tasks.loop(minutes=2, reconnect=True)(_tick)
        guild_name = self.config.guilds[guild_id]

        @loop.before_loop
        async def _before_loop():
            await self.bot.wait_until_ready()
            logging.info(f"[{guild_name}] twitch live loop started (start up)")

        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.info(f"[{guild_name}] twitch live loop cancelled (shutdown)")
            else:
                logging.info(f"[{guild_name}] twitch live loop ended normally.")

        @loop.error
        async def _error(self, error: BaseException):
            logging.exception("Error ocurred %s", error)
            print(str(error))

        self._loops[guild_id] = loop
        loop.start()
