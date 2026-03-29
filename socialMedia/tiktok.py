import logging

import discord
from discord.ext import tasks

from SQL.rolesSQL.roles import get_role_id
from SQL.socialMedia.tiktok import add_link, check_if_link_exists
from utils.core import AppConfig
from utils.socials.pullingFromTiktok import get_latest_videos


class TikTokLoop:
    def __init__(self, bot: discord.Client, config: AppConfig):
        self.bot = bot
        self.config = config
        self._loops: dict[int, tasks.Loop] = {}  # guild_id -> loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns None if not exists
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        guild_name = self.config.guilds[guild_id]
        guild = self.bot.get_guild(guild_id)

        async def _tick():
            all_links, all_ids, all_thumbnails, profile_picture = await get_latest_videos()
            channel_id = self.config.get_channel_id(guild_name=guild_name, channel="clips")
            channel = self.bot.get_channel(channel_id)
            for link, id, thumbnail in zip(all_links, all_ids, all_thumbnails):
                is_existing: bool = check_if_link_exists(link)
                if is_existing:
                    continue

                add_link(link, id)
                embed = discord.Embed(title="New Tiktok!", colour=discord.Color(0xF6A6BB))
                embed.set_author(name="sharkocalypse", icon_url=profile_picture)
                embed.set_thumbnail(url=thumbnail)
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Watch Video", url=link))

                if isinstance(channel, discord.TextChannel) and guild is not None:
                    role_id = get_role_id("shark updates")
                    role = guild.get_role(role_id)
                    if role is not None:
                        await channel.send(
                            f"new post alert! Check out Shark's latest TikTok here. {role.mention}", embed=embed, view=view
                        )

        loop = tasks.loop(hours=1, reconnect=True)(_tick)

        @loop.before_loop
        async def _before():
            await self.bot.wait_until_ready()
            logging.info(f"[{guild_name}] TikTok loop has been initialised and is running")

        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.info(f"[{guild_name}] TikTok loop has been cancelled (shutdown)")
            else:
                logging.info(f"[{guild_name}] TikTok loop has ended normally.")

        @loop.error
        async def _error(self, error: BaseException):
            logging.exception(f"An Error has occured: {str(error)}")

        self._loops[guild_id] = loop
        loop.start()

    def stop_for(self, guild_id: int):
        loop = self._loops.get(guild_id)
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
