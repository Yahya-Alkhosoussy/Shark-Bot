import asyncio

import discord
from discord.ext import commands

from SQL.musicSQL.music import add_song, clear_queue, get_song, remove_song
from utils.get_song import get_stream_url, resolve_spotify_track


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="play")
    async def play_song(self, ctx: commands.Context, spotify_url: str):
        guild = ctx.guild

        if not isinstance(ctx.author, discord.Member):
            return None

        if not isinstance(guild, discord.Guild):
            return None

        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send("Join a voice channel first.")
            return
        target = ctx.author.voice.channel
        vc = ctx.voice_client

        if vc is None or not isinstance(vc, discord.VoiceClient):
            vc = await target.connect()
        elif vc.channel != target:
            await vc.move_to(target)

        if vc.is_playing():
            vc.stop()

        tracks = resolve_spotify_track(spotify_url)

        for track in tracks:
            url = get_stream_url(track)
            add_song(track, url, ctx.author.id)

        track, url, requested_by = get_song()
        source = discord.FFmpegPCMAudio(url)
        member = guild.get_member(requested_by)
        await vc.channel.send(f"Playing {track}{f', requested by: {member.mention}' if member else ''}")
        vc.play(source, after=lambda error: self.play(track, guild, vc))

    def play(self, old_track: str, guild: discord.Guild, vc: discord.VoiceClient):
        remove_song(old_track)
        track, url, requested_by = get_song()
        source = discord.FFmpegPCMAudio(url)
        member = guild.get_member(requested_by)
        asyncio.run_coroutine_threadsafe(
            vc.channel.send(f"Playing {track}{f', requested by: {member.mention}' if member else ''}"), self.bot.loop
        )
        vc.play(source, after=self.play(track, guild, vc))

    @commands.command(name="Add")
    async def add_song(self, ctx: commands.Context, track_url: str):
        tracks = resolve_spotify_track(track_url)
        for track in tracks:
            url = get_stream_url(track)
            add_song(track, url, ctx.author.id)
            await ctx.send(f"Added {track} to the queue")

    @commands.command(name="Clear")
    async def clear_queue(self, ctx: commands.Context):
        await ctx.reply("Clearing queue")
        clear_queue()
        await ctx.send("Queue clearerd!")

    @commands.command(name="Remove")
    async def remove_track(self, ctx: commands.Context, track_url: str):
        tracks = resolve_spotify_track(track_url)
        for track in tracks:
            remove_song(track)
            await ctx.send(f"Track {track} removed!")

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        vc = ctx.voice_client
        if vc and isinstance(vc, discord.VoiceClient):
            await self.clear_queue(ctx)
            vc.stop()
            await ctx.send("Stopped.")
