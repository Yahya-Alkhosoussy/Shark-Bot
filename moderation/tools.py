from discord.ext import commands
import discord
from utils.checks import is_mod
from utils.core import AppConfig
import datetime as dt


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot, config: AppConfig):
        self.bot = bot
        self.config = config

    @commands.command(name="timeout")
    @is_mod()
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: int, *, reason: str = "No Reason Provided"):
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
        await member.ban(reason=reason)
        await ctx.send(f"{member.name} has been banned.")
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has banned user {member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}from the server. Reason: {reason}",  # noqa: E501
            bot=self.bot,
            guild_id=ctx.guild.id,
        )