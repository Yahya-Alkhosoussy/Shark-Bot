from discord.ext import commands
import discord
import exceptions.exceptions as ex

def is_mod():
    async def check(ctx: commands.Context):
        assert isinstance(ctx.author, discord.Member)
        config = ctx.cog.config  # type: ignore This works on run time
        if not config.check_for_mod_role(ctx.author.roles):
            raise ex.InvalidRole("Invalid role, this is only for mods")
        return True

    return commands.check(check)