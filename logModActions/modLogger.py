import asyncio
from pathlib import Path

from discord.ext import commands
from twitchAPI.chat import Chat, EventData
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import (
    ChannelBanEvent,
    ChannelUnbanEvent,
    ChannelUnbanRequestCreateEvent,
    ChannelWarningSendEvent,
)
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent

from utils.core import AppConfig


class ModLogger(commands.Cog):
    def __init__(self, bot: commands.Bot, config: AppConfig):
        self.bot = bot
        self.config = config

    async def ban_detected(self, username: str, channel: str, mod_responsible: str, reason: str):
        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG: TWITCH] {username} was banned on twitch on {channel}'s twitch by {mod_responsible}"
            f"{f' with the reason stated being {reason}' if reason else ''}",
            bot=self.bot,
            guild_id=1273776575266951268,
        )

    async def timeout_detected(self, username: str, channel: str, duration: int, mod_responsible: str, reason: str):
        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG: TWITCH] {username} was timedout on twitch for {duration} seconds on {channel}'s twitch"
            f" by {mod_responsible}{f' with the reason stated being {reason}' if reason else ''}",
            bot=self.bot,
            guild_id=1273776575266951268,
        )

    async def unban_detected(self, username: str, channel: str, mod_responsible: str):
        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG: TWITCH] {username} was unbanned on twitch on {channel}'s twitch by {mod_responsible}",
            bot=self.bot,
            guild_id=1273776575266951268,
        )

    async def unban_request_detected(self, username: str, channel: str, text: str):
        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG: TWITCH] {username} has submitted an unban request on twitch to {channel}'s twitch"
            f" the text provided is: {text}",
            bot=self.bot,
            guild_id=1273776575266951268,
        )

    async def warning_detected(
        self, username: str, reason: str | None, chat_rules_cited: list[str] | None, channel: str, mod_responsible: str
    ):
        await self.config.send_discord_mod_log(
            log_message=f"[AUTO MOD LOG: TWITCH] {username} was warned on twitch on {channel}'s twitch by {mod_responsible}"
            f"{f' with the reason stated being {reason}' if reason else ''}"
            f"{f' and the chat rules cited are: {','.join(chat_rules_cited)}' if chat_rules_cited else ''}",
            bot=self.bot,
            guild_id=1273776575266951268,
        )


class TwitchBot:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        bot_scopes: list[AuthScope],
        mod_scopes: list[AuthScope],
        target_channels: list[str],
        cog: ModLogger,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.bot_scopes = bot_scopes
        self.mod_scopes = mod_scopes
        self.target_channels = target_channels
        self.cog = cog

        self.twitch: Twitch | None = None
        self.shark_eventsub: EventSubWebsocket | None = None
        self.dys_eventsub: EventSubWebsocket | None = None
        self.chat: Chat | None = None
        self.dys_id: str | None = None
        self.shark_id: str | None = None
        self.bot_id: str | None = None

    async def setup(self):
        self.twitch = await Twitch(self.app_id, self.app_secret)
        twitch_helper = UserAuthenticationStorageHelper(self.twitch, self.bot_scopes, Path("tokens/bot_token.json"))
        await twitch_helper.bind()

        main_loop = asyncio.get_event_loop()

        self.shark_eventsub = EventSubWebsocket(self.twitch, callback_loop=main_loop)
        self.shark_eventsub.start()
        self.dys_eventsub = EventSubWebsocket(self.twitch, callback_loop=main_loop)
        self.dys_eventsub.start()

        user = await first(self.twitch.get_users(logins=["sharkocalypse"]))
        if not user:
            raise ValueError("User sharkocalypse not found")
        self.shark_id = user.id

        user_2 = await first(self.twitch.get_users(logins=["dyslexxik"]))
        if not user_2:
            raise ValueError("User, dyslexxik, not found")
        self.dys_id = user_2.id

        user_3 = await first(self.twitch.get_users())
        if not user_3:
            raise ValueError("Bot not found")
        self.bot_id = user_3.id

        self.chat = await Chat(self.twitch)

    async def on_ban(self, ban: ChannelBanEvent):
        event = ban.event
        if event.is_permanent:
            await self.cog.ban_detected(
                event.user_login, event.broadcaster_user_login, event.moderator_user_login, event.reason
            )
            return
        try:
            assert event.ends_at
        except AssertionError:
            return
        duration = event.ends_at - event.banned_at
        await self.cog.timeout_detected(
            event.user_login, event.broadcaster_user_login, duration.seconds, event.moderator_user_login, event.reason
        )

    async def on_unban(self, unban: ChannelUnbanEvent):
        event = unban.event
        await self.cog.unban_detected(event.user_login, event.broadcaster_user_login, event.moderator_user_login)

    async def on_warning(self, warning: ChannelWarningSendEvent):
        event = warning.event
        await self.cog.warning_detected(
            event.user_login, event.reason, event.chat_rules_cited, event.broadcaster_user_login, event.moderator_user_login
        )

    async def on_unban_request(self, request: ChannelUnbanRequestCreateEvent):
        event = request.event
        await self.cog.unban_request_detected(event.user_login, event.broadcaster_user_login, event.text)

    async def on_ready(self, event: EventData):
        print("Twitch bot is ready")
        await event.chat.join_room(self.target_channels)
        print("Joining channels")

    async def close_bot(self):
        if self.dys_eventsub:
            await self.dys_eventsub.stop()
        if self.shark_eventsub:
            await self.shark_eventsub.stop()
        if self.chat:
            self.chat.stop()
        if self.twitch:
            await self.twitch.close()

    async def run(self):
        try:
            await self.setup()
            assert self.chat, "Chat is none"
            assert self.twitch, "Twitch is None"
            assert self.dys_eventsub, "Dys eventsub is None"
            assert self.shark_eventsub, "Shark eventsub is None"
            assert self.dys_id, "Dys' id is None"
            assert self.shark_id, "Shark's ID is None"
            assert self.bot_id, "Bot id is None"

            self.chat.register_event(ChatEvent.READY, self.on_ready)

            await self.dys_eventsub.listen_channel_ban(self.dys_id, self.on_ban)
            await self.dys_eventsub.listen_channel_unban(self.dys_id, self.on_unban)
            await self.dys_eventsub.listen_channel_unban_request_create(self.dys_id, self.bot_id, self.on_unban_request)
            await self.dys_eventsub.listen_channel_warning_send(self.dys_id, self.bot_id, self.on_warning)
            await self.shark_eventsub.listen_channel_ban(self.shark_id, self.on_ban)
            await self.shark_eventsub.listen_channel_unban(self.shark_id, self.on_unban)
            await self.shark_eventsub.listen_channel_unban_request_create(self.shark_id, self.bot_id, self.on_unban_request)
            await self.shark_eventsub.listen_channel_warning_send(self.shark_id, self.bot_id, self.on_warning)

            self.chat.start()

            await asyncio.Event().wait()
        except Exception as e:
            print(f"Error {e}")
        finally:
            await self.close_bot()
