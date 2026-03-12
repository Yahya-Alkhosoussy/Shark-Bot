# imports
from datetime import timedelta

import discord

from SQL.modActions.modActionsSQL import get_bans as saved_bans
from SQL.modActions.modActionsSQL import get_streamers, get_timeouts
from utils.pullingFromTwitch import get_bans as twitch_bans

twitch_bans


class ModLoop:
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self._loops: dict[int, bool] = {}  # Guild ID -> True or False

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns none if it doesn't exist
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        async def _tick():
            all_bans: list[tuple[str, str, str, str, str]] = saved_bans()
            all_timeouts: list[tuple[str, str, str, str, int, str]] = get_timeouts()

            streamer_bans, banned_users, ban_reason, mod_ban, when_ban = [], [], [], [], []
            for ban in all_bans:
                streamer_bans.append(ban[0])
                banned_users.append(ban[1])
                ban_reason.append(ban[2])
                mod_ban.append(ban[3])
                when_ban.append(ban[4])

            streamer_timeouts, timeout_users, timeout_reason, mod_timeout, duration, when_timeout = [], [], [], [], [], []
            for timeout in all_timeouts:
                streamer_timeouts.append(timeout[0])
                timeout_users.append(timeout[1])
                timeout_reason.append(timeout[2])
                mod_timeout.append(timeout[3])
                duration.append(timeout[4])
                when_timeout.append(timeout[5])

            streamers = get_streamers()
            list_of_bans: list[tuple[str, tuple[list[str], list[str], list[str], list[timedelta | None]]]] = []
            for streamer in streamers:
                if streamer == "sharkocalypse":
                    nick = "shark"
                else:
                    nick = "spider"
                list_of_bans.append((streamer, (twitch_bans(user=nick, twitch_user=streamer))))
