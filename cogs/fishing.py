from __future__ import annotations

from sqlite3 import OperationalError
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from exceptions.exceptions import ItemNotFound
from SQL.fishingSQL.baits import get_baits
from SQL.sharkGamesSQL.sharkGameSQL import check_for_username_change, remove_net
from utils.checks import is_mod
from utils.core import AppConfig

if TYPE_CHECKING:
    from MyClient import MyBot


class FishingCog(commands.Cog):
    def __init__(self, bot: "MyBot", config: AppConfig):
        self.bot = bot
        self.config = config

    @commands.command(name="fish")
    async def fishing(self, ctx: commands.Context):
        self.bot.loop_processing = True
        after: str | None = None if len(ctx.message.content[6:]) == 0 else ctx.message.content[6:]
        if after is not None:
            check_for_username_change(ctx.author.name, ctx.author.id)
            baits, _ = get_baits(ctx.author.name)
            if after not in baits:
                await ctx.reply(f"You do not own the bait ({after}) or it is an invalid bait, try the command again")
                return
        try:
            await self.bot.fishing.fish(message=ctx.message, bait=after)
        except ItemNotFound as e:
            await ctx.channel.send(f"{ctx.author.mention} {str(e)}")
        self.bot.loop_processing = False

    @commands.group(name="Update")
    async def update(self, ctx: commands.Context):
        pass

    @update.group()
    async def shop(self, ctx: commands.Context):
        pass

    @shop.command(name="items")
    @is_mod()
    async def update_shop_items(self, ctx: commands.Context):
        assert ctx.guild
        self.bot.updating_store = True
        await self.bot.fishing.add_into_shop_internal(message=ctx.message)
        self.bot.updating_store = False
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has added an item to the shop.",
            bot=self.bot,
            guild_id=ctx.guild.id,
        )

    @shop.command(name="prices")
    @is_mod()
    async def update_shop_prices(self, ctx: commands.Context):
        assert ctx.guild
        self.bot.updating_store = True
        await self.bot.fishing.update_shop_prices_internal(message=ctx.message)
        self.bot.updating_store = False
        await self.config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has updated prices in the shop.",
            bot=self.bot,
            guild_id=ctx.guild.id,
        )

    @commands.group()
    async def remove(self, ctx: commands.Context):
        pass

    @remove.command(name="net")
    @is_mod()
    async def remove_net(self, ctx: commands.Context, member: discord.Member, net: str):
        await ctx.reply(f"Attempting to remove {net}")

        try:
            remove_net(member.name, net)
        except OperationalError as e:
            await ctx.send(f"I encounered an error while trying to remove {net}. Error: {str(e)}")
            return
        await ctx.send("Net removed!")
