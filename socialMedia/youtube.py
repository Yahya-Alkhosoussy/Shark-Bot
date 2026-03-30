import logging

import discord
from discord.ext import tasks

from SQL.rolesSQL.roles import get_role_id
from SQL.socialMedia.youtube import add_video, get_youtube_handles, is_video_existing
from utils.core import AppConfig
from utils.socials.youtubeCore.youtube import get_channel_item, get_video_items


class YoutubeLoop:
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
        assert guild
        channel_id = self.config.get_channel_id(guild_name=guild_name, channel="clips")
        channel = guild.get_channel(channel_id)

        async def _tick():
            handles = get_youtube_handles()
            for handle in handles:
                handle = handle[0]
                video_items = get_video_items(handle)
                for item in video_items:
                    url = item.snippet.url
                    if is_video_existing(url):
                        continue
                    title = item.snippet.title
                    id = item.snippet.resourceId.videoId
                    add_video(youtube_handle=handle, title=title, id=id, url=url)
                    embed = discord.Embed(title=title, colour=discord.Color(0xF6A6BB))
                    icon = get_channel_item(handle)
                    icon_url = icon.snippet.profile_url
                    embed.set_author(name="sharkocalypse", icon_url=icon_url)
                    embed.set_image(url=item.snippet.thumbnail_url)
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Watch Video", url=url))
                    if isinstance(channel, discord.TextChannel) and guild is not None:
                        role_id = get_role_id("shark updates")
                        role = guild.get_role(role_id)
                        if role is not None:
                            await channel.send(
                                f"new post alert! Check out Shark's latest Youtube video here. {role.mention}",
                                embed=embed,
                                view=view,
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
