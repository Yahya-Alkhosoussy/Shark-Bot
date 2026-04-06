from discord.ext import commands
import discord
import exceptions.exceptions as ex
from pathlib import Path
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