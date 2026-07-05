from collections import deque  # noqa
from hashlib import md5  # noqa
from datetime import datetime
from _hashlib import HASH
from datetime import timedelta
from aiohttp import ClientSession

from discord.ext import commands
import discord
from exceptions.exceptions import FormatError
from SQL.knownhashes.knownhashes import get_hashes, add_hash  # noqa


class custom_message:
    def __init__(
        self,
        message_id: int,
        timestamp: datetime,
        content: str,
        user_id: int,
        image_hashes: set[HASH] | None = None,
        image_binaries: set[bytes] | None = None,
    ):
        self.message_id = message_id
        self.timestamp = timestamp
        self.content = content
        self.image_hashes = image_hashes
        self.image_binaries = image_binaries
        self.user_id = user_id

        if not self.image_binaries and not self.image_hashes:
            raise FormatError("Provide a set of image binaries or the hashed image binaries.", 2000)
        if not self.image_hashes and self.image_binaries:
            self.image_hashes: set[HASH] | None = set()
            for binary in self.image_binaries:
                self.image_hashes.add(md5(binary))

    def __str__(self) -> str:
        return (
            f"A User with the ID of {self.user_id} sent a message with the "
            f"content of {self.content} at {self.timestamp.strftime(r'%m/%d %H:%M:%S')}."
        )

    def __repr__(self) -> str:
        return (
            f"A User with the ID of {self.user_id} sent a message with the content of "
            f"{self.content} at {self.timestamp.strftime(r'%m/%d %H:%M:%S')} and the following "
            f"image hashes: {self.image_hashes}"
        )


class SpamDetectionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deque: deque[custom_message] = deque(maxlen=5)

    async def add_msg_to_deque(self, message: custom_message | None = None, discord_message: discord.Message | None = None):
        if not message and not discord_message:
            raise FormatError("Could not add message to deque as no message was given to add", 2001)

        if self.deque.maxlen is None:
            raise FormatError("The deque wasn't set up properly and doesn't have a max length", 2002)

        if not message and discord_message:
            image_binaries: set[bytes] = set()
            for attachment in discord_message.attachments:
                async with ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            image_binaries.add(await resp.read())

            message = custom_message(
                message_id=discord_message.id,
                timestamp=discord_message.created_at,
                content=discord_message.content,
                user_id=discord_message.author.id,
                image_binaries=image_binaries,
            )
            last_index = self.deque.maxlen - 1

            try:
                self.deque[last_index]
            except IndexError:
                self.deque.appendleft(message)
                return

            if datetime.now() - self.deque[last_index].timestamp < timedelta(seconds=10):
                old_deque = deque(maxlen=self.deque.maxlen + 1)
                old_deque.extend(self.deque)
                self.deque = old_deque
                self.deque.appendleft(message)
                return
            self.deque.appendleft(message)

    async def check_for_spam(self):
        badHashes = get_hashes()
        hashes: set[str] = set()
        for message in self.deque:
            if not message.image_hashes:
                raise FormatError("Image hashes is None!!!", 2003)
            for hash in message.image_hashes:
                if hash.hexdigest() in hashes:
                    # if the same image was sent in 2 channels within the 10 second window
                    await self.possible_spam_detected(message)
                if hash.hexdigest() in badHashes:
                    await self.bad_spam_detected(message)  # await the deal with it function
                    return
                hashes.add(hash.hexdigest())

    async def bad_spam_detected(self, message: custom_message):
        guild = self.bot.get_guild(1273776575266951268)
        if guild is None:
            raise ValueError("Guild is None!!")
        member = guild.get_member(message.user_id)
        if member is None or self.bot.user is None:
            raise ValueError("Member or bot not found!")
        if message.user_id == self.bot.user.id:
            return
        channel = guild.get_channel(1505513311024840864)
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not found or bot doesn't have access to it")
        await member.ban(delete_message_days=1)
        await channel.send(f"SPAM DETECTED: \nSpammer: {member.global_name}\n Action taken: BAN \n Requires Mod Review: No")

    async def possible_spam_detected(self, message: custom_message):
        guild = self.bot.get_guild(1273776575266951268)
        if guild is None:
            raise ValueError("Guild is None!!")
        member = guild.get_member(message.user_id)
        if member is None or self.bot.user is None:
            raise ValueError("Member or bot not found!")
        if message.user_id == self.bot.user.id:
            return
        channel = guild.get_channel(1505513311024840864)
        if not isinstance(channel, discord.TextChannel):
            raise ValueError("Channel is not found or bot doesn't have access to it")
        mod_role = guild.get_role(1386628035591012393)
        if not mod_role:
            raise ValueError("Mod role is None for some reason.")
        await member.timeout(timedelta(1))
        await channel.send(
            f"POSSIBLE SPAM DETECTED: \nSpammer: {member.global_name}\nAction taken: 1 Day timeout"
            f"Requires Mod Review: Yes, check messages for possible ban {mod_role.mention}"
        )
