import asyncio
import logging

import discord
from discord.ext import commands, tasks

from SQL.banListSQL.banList import get_banned_members
from utils.ban_list import BannedMember, Statuses  # noqa
from utils.core import AppConfig


class BanListChecker:
    def __init__(self, bot: commands.Bot, config: AppConfig):
        self.bot = bot
        self.config = config
        self.membersLookedAt: dict[BannedMember, Statuses] = {}
        self._loops: dict[int, tasks.Loop] = {}  # Guild_id --> Loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)
        return bool(loop and loop.is_running())

    async def handle_ban_request(self, member: BannedMember, guild: discord.Guild):

        user = guild.get_member(member.id)

        if not isinstance(user, discord.Member):
            return

        await self.config.send_discord_mod_log(
            "Ban detected: "
            f"{member.name} had been banned from {member.initial_server_ban} for {member.reason_for_ban}. "
            "Should I go ahead and ban them?"
            "(Reply with `!confirm` to ban them or `!deny` to not ban them within 2 days.)",
            self.bot,
            guild.id,
        )

        def check(m: discord.Message):
            guild_name = self.config.guilds[guild.id]
            return (m.content == "!confirm" or m.content == "!deny") and (
                m.channel.id == self.config.channels["log"][guild_name]
            )

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=2 * 24 * 60 * 60)  # 48 hours
        except asyncio.TimeoutError:
            await self.config.send_discord_mod_log(f"Got no reply. {member.name} will not be banned.", self.bot, guild.id)
            return
        if reply.content == "!deny":
            await self.config.send_discord_mod_log(
                f"Request denied successfully. {member.name} will not be banned.", self.bot, guild.id
            )
            return
        await self.config.send_discord_mod_log(
            f"Request to ban {member.name} acknowledged. Starting ban process...", self.bot, guild.id
        )

        await user.ban(reason=member.reason_for_ban)
        await self.config.send_discord_mod_log(f"{member.name} successfully banned.", self.bot, guild.id)

    async def handle_unban_request(self, member: BannedMember, guild: discord.Guild):
        await self.config.send_discord_mod_log(
            f"User {member.name} was unbanned from the original server they were banned in. "
            "Should I attempt to unban them? (Within the next 2 days reply with `!confirm` to allow me to try to unban them"
            f" or `!deny` to keep them banned.) As a reminder the reason they were banned is: {member.reason_for_ban}",
            self.bot,
            guild.id,
        )

        def check(m: discord.Message):
            guild_name = self.config.guilds[guild.id]
            return (m.content == "!confirm" or m.content == "!deny") and (
                m.channel.id == self.config.channels["log"][guild_name]
            )

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=2 * 24 * 60 * 60)  # 48 hours
        except asyncio.TimeoutError:
            await self.config.send_discord_mod_log(f"Got no reply. {member.name} will not be unbanned.", self.bot, guild.id)
            return
        if reply.content == "!deny":
            await self.config.send_discord_mod_log(
                f"Request denied successfully. {member.name} will not be unbanned.", self.bot, guild.id
            )
            return
        await self.config.send_discord_mod_log(
            f"Request to ban {member.name} acknowledged. Starting unban process...", self.bot, guild.id
        )
        try:
            await guild.unban(member)
        except discord.NotFound as e:
            await self.config.send_discord_mod_log(
                f"Unban failed. Could not find user {member.name}. Error: {str(e)}", self.bot, guild.id
            )
        except discord.Forbidden:
            await self.config.send_discord_mod_log("Unban failed. I do not have the proper permissions.", self.bot, guild.id)
        except discord.HTTPException:
            await self.config.send_discord_mod_log(
                "Something went wrong while unbanning, could not complete.", self.bot, guild.id
            )

    def start_for(self, guild_id: int):  # noqa: C901
        if self.is_running(guild_id):
            return

        async def _tick():
            banned_members = await get_banned_members()
            for member in banned_members:
                if member in self.membersLookedAt and self.membersLookedAt[member] == member.status:
                    # if the member was looked at and the cached status is the same as the current status, no need to look at it
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return
                bans = [ban async for ban in guild.bans()]
                banned_user_ids = [ban.user.id for ban in bans]
                if member.status == Statuses.UNBANNED and member.id in banned_user_ids:
                    await self.handle_unban_request(member, guild)

                if member.id not in banned_user_ids and member.status == Statuses.BANNED:
                    await self.handle_ban_request(member, guild)
                self.membersLookedAt[member] = member.status

        loop = tasks.loop(hours=8, reconnect=True)(_tick)

        @loop.before_loop
        async def _before():
            await self.bot.wait_until_ready()
            logging.info("BanTracker started!")

        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.warning("BanTracker cancelled (Shutdown)")
            else:
                logging.info("BanTracker loop ended normally")

        @loop.error
        async def _error(something, error):
            logging.exception(f"BanTracker error: {error}")

        self._loops[guild_id] = loop
        loop.start()

    def stop_for(self, guild_id: int):
        loop = self._loops[guild_id]
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
