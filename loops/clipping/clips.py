import logging

import discord
from discord.ext import commands, tasks

from SQL.clipManagement.clips import check_live, get_channel, get_discord_id, get_nick, get_users, update_live
from utils.core import AppConfig
from utils.pullingFromTwitch import internal_handle_stream_end  # noqa: F401


class ClipLoop:
    def __init__(self, bot: commands.Bot, config: AppConfig):
        self.bot = bot
        self.config = config
        self._loops: dict[int, tasks.Loop] = {}  # guild_id -> loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns none if it doesn't exist
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return None

        async def _tick():
            users, discord_ids = get_users()
            channels: dict[str, int] = {}  # username -> channel_id or 1
            live_statuses: dict[str, bool] = {}
            for discord_id, user in zip(discord_ids, users):
                channel_chosen = get_channel(discord_id)
                channels[user] = channel_chosen
                live_statuses[user] = check_live(discord_id)

            for user in live_statuses.keys():
                if update_live(user) and live_statuses[user]:
                    live_statuses[user] = check_live(user)

                    discord_id = get_discord_id(user)
                    nick = get_nick(user)

                    clips = internal_handle_stream_end(username=user, user=nick)
                    if channels[user] != 1:
                        channel = self.bot.get_channel(channels[user])
                        if isinstance(channel, discord.TextChannel):
                            messages = []
                            to_send = (
                                f"Hey everyone! {nick} has ended their stream! Here's all the highlights and clips from it: \n"
                            )

                            for clip in clips:
                                if len(to_send) + len(clip) + 1 > 2000:
                                    messages.append(to_send)
                                    to_send = clip + "\n"
                                else:
                                    to_send += clip + "\n"

                            for message in messages:
                                await channel.send(message)
                    else:
                        discord_user = self.bot.fetch_user(discord_id)
                        messages = []
                        to_send = "Hey your stream just ended! Here's all the highlights and clips from it: \n"

                        for clip in clips:
                            if len(to_send) + len(clip) + 1 > 2000:
                                messages.append(to_send)
                                to_send = clip + "\n"
                            else:
                                to_send += clip + "\n"
                        for message in messages:
                            await discord_user.send(message)

                elif update_live(user):
                    live_statuses[user] = check_live(user)
                    continue
                else:
                    continue

        loop = tasks.loop(seconds=10, reconnect=True)(_tick)
        guild_name = self.config.guilds[guild_id]

        @loop.before_loop
        async def _before():
            await self.bot.wait_until_ready()
            logging.info(f"[{guild_name}] mod log loop started (start up)")

        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.info(f"[{guild_name}] mod log loop cancelled (shutdown)")
            else:
                logging.info(f"[{guild_name}] mod log loop ended normally.")

        @loop.error
        async def _error(self, error: BaseException):
            logging.exception("Error ocurred %s", error)
            print(str(error))

        self._loops[guild_id] = loop
        loop.start()

    def stop_for(self, guild_id: int):
        loop = self._loops.get(guild_id)
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
