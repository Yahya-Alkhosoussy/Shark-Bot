import asyncio
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands

from exceptions.exceptions import ItemNotFound
from SQL.deletedSQL.deleted_messages import get_deleted_messages as get_messages
from SQL.deletedSQL.deleted_messages import get_user_id
from utils.checks import is_mod
from utils.core import AppConfig


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot, config: AppConfig):
        self.bot = bot
        self.config = config

    @commands.command(name="timeout")
    @is_mod()
    async def timeout(
        self, ctx: commands.Context, member: discord.Member, duration: int, *, reason: str = "No Reason Provided"
    ):
        assert ctx.guild
        until = dt.timedelta(seconds=duration)
        await member.timeout(until, reason=reason)
        await ctx.send(f"{member.name} has been timedout.")
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has timed out user ({member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}for {duration} seconds. Reason: {reason}",  # noqa: E501
            bot=self.bot,
            guild_id=ctx.guild.id,
        )

    @commands.command(name="kick")
    @is_mod()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No Reason Provided"):
        assert ctx.guild
        await member.kick(reason=reason)
        await ctx.send(f"{member.name} has been kicked.")
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has kicked user {member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}from the server. Reason: {reason}",  # noqa: E501
            bot=self.bot,
            guild_id=ctx.guild.id,
        )

    @commands.command(name="ban")
    @is_mod()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No Reason Provided"):
        assert ctx.guild
        await member.ban(reason=reason, delete_message_days=0, delete_message_seconds=0)
        await ctx.send(f"{member.name} has been banned.")
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has banned user {member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}from the server. Reason: {reason}",  # noqa: E501
            bot=self.bot,
            guild_id=ctx.guild.id,
        )

    @commands.command(name="deleted")
    @is_mod()
    async def get_deleted_messages(self, ctx: commands.Context, *, username: str = ""):
        try:
            user_id = get_user_id(username)
        except ItemNotFound as e:
            await ctx.send(
                f"Got an error while trying to find the user: \nError message: {e.message} \nError code: {e.error_code}"
            )
            return
        messages, image_paths, deleted_at = get_messages(user_id, dt.datetime.now())
        list_to_send: list[str] = []
        to_send = ""
        for message, time in zip(messages, deleted_at):
            if len(to_send) + len(message) + len(f"\nDeleted at: {time}") >= 2000:
                list_to_send.append(to_send)
                to_send = message + f"\nDeleted at: {time}"
                continue
            to_send += message + f"\nDeleted at: {time}"
        if to_send != "":
            list_to_send.append(to_send)

        for message in list_to_send:
            await ctx.send("Here is all that you requested")
            await ctx.send(message)
        await self.send_images(ctx, image_paths)

    async def send_images(self, ctx: commands.Context, image_paths: list[str | None]):
        images_found = False
        images: list[discord.File] = []
        for path in image_paths:
            if path is not None and not images_found:
                images_found = True
                await ctx.send("Here are the images that were deleted:")
            if path is not None:
                img_location = Path(path)
                images.append(discord.File(img_location))
        if images_found:
            for i in range(0, len(images), 10):
                await ctx.send(files=images[i : i + 10])

    @commands.group()
    async def mod(self, ctx: commands.Context):
        pass

    @mod.command(name="help")
    @is_mod()
    async def mod_help(self, ctx: commands.Context):
        to_send = """Thank you for asking for help!
The following are mod exclusive actions:
1. `!timeout [@user] [duration in seconds] [reason (optional)]` - This command is to timeout any user for a set duration, if no duration is given it will default to a 10 minute timeout
2. `!kick [@user] [reason (optional)]` - This command is to kick any user from the server.
3. `!ban [@user] [reason (optional)]` - This command is to ban any user from the server.
4. `!add role` - This command prompts a series of requests that the bot will send for more information to add a role to react roles.
5. `!update shop items` - This command prompts a series of requests that the bot will send for more information to update shop items for the bait shop.
6. `!update shop prices` - same as above but for prices.
7. `!get deleted [username]` - gets all the messages that were deleted by a user in the past week. """  # noqa: E501
        await ctx.reply(to_send)

    async def get_entry(
        self, guild: discord.Guild, action: discord.AuditLogAction, user: discord.Member
    ) -> discord.AuditLogEntry | None:
        async for entry in guild.audit_logs(limit=100, action=action):
            try:
                assert entry.target
            except AssertionError:
                continue
            if entry.target.id == user.id:
                return entry

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.Member):
        ban_log: discord.AuditLogEntry | None = await self.get_entry(guild, discord.AuditLogAction.ban, user)

        if ban_log is None:
            await asyncio.sleep(1)
            for _ in range(5):
                ban_log = await self.get_entry(guild, discord.AuditLogAction.ban, user)
                if ban_log is not None:
                    break
                await asyncio.sleep(1)
            if ban_log is None:
                return

        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG] {user.name}{f' ({user.nick})' if user.nick else ''} got banned from the server by:"
            f" {ban_log.user.name if ban_log.user else 'an unknown moderator'} and the reason given was:"
            f" {ban_log.reason if ban_log.reason else 'No reason was given'}",
            bot=self.bot,
            guild_id=guild.id,
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.Member):
        unban_log = await self.get_entry(guild, discord.AuditLogAction.unban, user)

        if unban_log is None:
            await asyncio.sleep(1)
            for _ in range(5):
                unban_log = await self.get_entry(guild, discord.AuditLogAction.unban, user)
                if unban_log is not None:
                    break
                await asyncio.sleep(1)
            if unban_log is None:
                return

        await self.config.send_discord_mod_log(
            log_message=f"{user.name}{f' ({user.nick})' if user.nick else ''} was unbanned from the server by"
            f" {unban_log.user.name if unban_log.user else 'an unknown moderator'} and the reason given was"
            f" {unban_log.reason if unban_log.reason else 'No reason was given'}",
            bot=self.bot,
            guild_id=guild.id,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, user: discord.Member):
        kick_log = await self.get_entry(user.guild, discord.AuditLogAction.kick, user)

        if kick_log is None:
            await asyncio.sleep(1)
            for _ in range(5):
                kick_log = await self.get_entry(user.guild, discord.AuditLogAction.kick, user)
                if kick_log is not None:
                    break
                await asyncio.sleep(1)
            if kick_log is None:
                return

        await self.config.send_discord_mod_log(
            log_message=f"{user.name}{f' ({user.nick})' if user.nick else ''} was kicked from the server by"
            f" {kick_log.user.name if kick_log.user else 'an unknown moderator'} and the reason given was"
            f" {kick_log.reason if kick_log.reason else ': No reason was given'}",
            bot=self.bot,
            guild_id=user.guild.id,
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):

        if before.timed_out_until is None and after.timed_out_until is None:
            return
        if before.timed_out_until is None and after.timed_out_until is not None:
            try:
                timeout_length = after.timed_out_until - dt.datetime.now(tz=ZoneInfo("UTC"))
            except Exception as e:
                print(e)
                return
            await self.config.send_discord_mod_log(
                log_message=f"{after.name}{f' ({after.nick})' if after.nick else ''} was timed out for"
                f" {timeout_length.seconds} seconds ({timeout_length.seconds // 60} minutes)",
                bot=self.bot,
                guild_id=after.guild.id,
            )
        elif before.timed_out_until is not None and after.timed_out_until is None:
            await self.config.send_discord_mod_log(
                log_message=f"{after.name}{f' ({after.nick})' if after.nick else ''} has had their timeout removed"
                " (either ended or manually removed)",
                bot=self.bot,
                guild_id=after.guild.id,
            )
