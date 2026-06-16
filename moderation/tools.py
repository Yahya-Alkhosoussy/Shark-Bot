import datetime as dt
from pathlib import Path

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
                if len(images) == 10:
                    await ctx.send(files=images)
                elif len(images) == 20:
                    await ctx.send(files=images[10:])
                elif len(images) > 10:
                    await ctx.send(files=images[10:])
                else:
                    await ctx.send(files=images)

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
