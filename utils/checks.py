from pathlib import Path

import discord
from discord.ext import commands

import exceptions.exceptions as ex
from utils.core import AppConfig

CONFIG_PATH = Path(r"config.YAML")
config = AppConfig(CONFIG_PATH)


def is_mod():
    async def check(ctx: commands.Context):
        assert isinstance(ctx.author, discord.Member)
        if not config.check_for_mod_role(ctx.author.roles):
            raise ex.InvalidRole("Invalid role, this is only for mods")
        return True

    return commands.check(check)


def is_palworld_member():
    async def check(ctx: commands.Context):
        assert isinstance(ctx.author, discord.Member)
        if ctx.message.channel.id != 1534815931568619582:
            return False

        for role in ctx.author.roles:
            if role.id == 1543988824584093809:
                return True
        raise ex.InvalidRole("Invalid role, you need the palworld fins role to use this")

    return commands.check(check)
