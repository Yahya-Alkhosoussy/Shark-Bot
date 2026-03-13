# imports
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import tasks

from SQL.modActions.modActionsSQL import add_ban, add_timeout, get_streamers, get_timeouts
from SQL.modActions.modActionsSQL import get_bans as saved_bans
from utils.core import AppConfig
from utils.pullingFromTwitch import get_bans as twitch_bans


class ModLoop:
    def __init__(self, bot: discord.Client, config: AppConfig):
        self.bot = bot
        self.config = config
        self._loops: dict[int, tasks.Loop] = {}  # Guild ID -> True or False

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns none if it doesn't exist
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        async def _tick():
            all_bans: list[tuple[int, str, str, str, str, str]] = saved_bans()
            all_timeouts: list[tuple[int, str, str, str, str, int, str]] = get_timeouts()

            streamer_bans, banned_users, ban_reason, mod_ban, when_ban = [], [], [], [], []
            for ban in all_bans:
                streamer_bans.append(ban[1])
                banned_users.append(ban[2])
                ban_reason.append(ban[3])
                mod_ban.append(ban[4])
                when_ban.append(ban[5])

            streamer_timeouts, timeout_users, timeout_reason, mod_timeout, duration_t, when_timeout = [], [], [], [], [], []
            for timeout in all_timeouts:
                streamer_timeouts.append(timeout[1])
                timeout_users.append(timeout[2])
                timeout_reason.append(timeout[3])
                mod_timeout.append(timeout[4])
                duration_t.append(timeout[5])
                when_timeout.append(timeout[6])

            streamers = get_streamers() | {"sharkocalypse"}  # force sharkocalypse to be included
            # format: list[tuple[streamer's name, tuple[names, reasons, mod that banned them, duration]]
            list_of_bans: list[
                tuple[str, tuple[list[str], list[str | None], list[str], list[timedelta | None], list[str]]]
            ] = []
            print(streamers)
            for streamer in streamers:
                if streamer == "sharkocalypse":
                    nick = "shark"
                else:
                    nick = "spider"
                print(streamer)
                list_of_bans.append((streamer, (twitch_bans(user=nick, twitch_user=streamer))))
            """
            dimensions:
                list_of_bans[0] is for first streamer,
                list_of_bans[x][0] is for the streamer's name
                list_of_bans[x][1][0] is for banned users
                list_of_bans[x][1][1] is for reasons
                list_of_bans[x][1][2] is for the mod that banned them
                list_of_bans[x][1][3] is for the duration
            """
            for ban in list_of_bans:
                streamer_name = ban[0]
                ban_info = ban[1]
                user = ban_info[0]
                reason = ban_info[1]
                mod = ban_info[2]
                dur = ban_info[3]
                created = ban_info[4]

                for i in range(len(user)):
                    when = datetime.fromisoformat(created[i])
                    if dur[i] is None:
                        if user[i] not in banned_users:
                            try:
                                await self.config.send_discord_mod_log(
                                    log_message=f"[AUTO MOD LOG] {mod[i]} has banned {user[i]}. {f'Reason given: {reason[i]}.' if reason[i] else ''} The ban happened at {str(when)}",  # noqa: E501
                                    bot=self.bot,
                                    guild_id=guild_id,
                                )
                            except BaseException as e:
                                print(str(e))
                            add_ban(streamer=streamer_name, user=user[i], reason=reason[i], mod=mod[i], when=when)
                    else:
                        await self.config.send_discord_mod_log(
                            log_message=f"[AUTO MOD LOG] {mod[i]} has timedout {user[i]} for {int(dur[i].total_seconds())} seconds. {f'Reason given: {reason[i]}.' if reason[i] else ''} The timeout happened at {str(when)}",  # type: ignore # noqa: E501
                            bot=self.bot,
                            guild_id=guild_id,
                        )
                        try:
                            add_timeout(
                                streamer=streamer_name,
                                user=user[i],
                                reason=reason[i],
                                mod=mod[i],
                                when=when,
                                duration=int(dur[i].total_seconds()),  # type: ignore
                            )
                        except BaseException as e:
                            print(str(e))

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
        if loop and loop.is_running:
            loop.stop()
            return True
        return False
