import asyncio
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from twitchAPI.chat import Chat, EventData
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first  # noqa
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import ChannelBanEvent, ChannelUnbanEvent, ChannelWarningSendEvent  # noqa
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent

from moderation.tools import Moderation
from MyClient import MyBot
from utils.core import AppConfig
from utils.twitch_core import TwitchBan, TwitchUnban, TwitchUser, TwitchWarning

TARGET_CHANNELS = ["sharkocalypse", "dyslexxik"]

MOD_SCOPES = [
    AuthScope.CHANNEL_BOT,
    AuthScope.CHANNEL_MODERATE,
    AuthScope.MODERATION_READ,
    AuthScope.MODERATOR_READ_BANNED_USERS,
    AuthScope.MODERATOR_READ_UNBAN_REQUESTS,
    AuthScope.MODERATOR_READ_WARNINGS,
]

BOT_SCOPES = [
    AuthScope.USER_BOT,
    AuthScope.USER_READ_CHAT,
    AuthScope.CHAT_READ,
    AuthScope.CHAT_EDIT,
    AuthScope.USER_WRITE_CHAT,
    AuthScope.MODERATION_READ,
    AuthScope.MODERATOR_READ_CHAT_MESSAGES,
    AuthScope.MODERATOR_READ_BANNED_USERS,
    AuthScope.MODERATOR_READ_UNBAN_REQUESTS,
    AuthScope.MODERATOR_READ_WARNINGS,
]

class TwitchBot:
    def __init__(
            self,
            app_id: str | None,
            app_secret: str | None,
            bot_scopes: list[AuthScope],
            mod_scopes: list[AuthScope],
            bot: MyBot,
            config: AppConfig
        ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.bot_scopes = bot_scopes
        self.mod_scopes = mod_scopes

        self.shark_eventsub: EventSubWebsocket | None = None
        self.dys_eventsub: EventSubWebsocket | None = None
        self.bot_eventsub: EventSubWebsocket | None = None
        self.shark_twitch: Twitch | None = None
        self.dys_twitch: Twitch | None = None
        self.bot_twitch: Twitch | None = None
        self.mod_cog = Moderation(bot, config)
        self.chat: Chat | None = None

    async def setup(self):
        assert self.app_id, "App ID is None, check the env file"
        assert self.app_secret, "App secret is None, check the env file"

        if not Path("token").exists():
            Path("token").mkdir()

        self.shark_twitch = await Twitch(self.app_id, self.app_secret)
        shark_twitch_helper = UserAuthenticationStorageHelper(
            self.shark_twitch, self.mod_scopes, Path("tokens/shark_token.json")
        )
        await shark_twitch_helper.bind()

        self.dys_twitch = await Twitch(self.app_id, self.app_secret)
        dys_twitch_helper = UserAuthenticationStorageHelper(
            self.dys_twitch, self.mod_scopes, Path("tokens/dys_token.json")
        )
        await dys_twitch_helper.bind()

        self.bot_twitch = await Twitch(self.app_id, self.app_secret)
        bot_twitch_helper = UserAuthenticationStorageHelper(
            self.bot_twitch, self.bot_scopes, Path("tokens/bot_token.json")
        )
        await bot_twitch_helper.bind()

        main_loop = asyncio.get_event_loop()
        self.shark_eventsub = EventSubWebsocket(self.shark_twitch, callback_loop=main_loop)
        self.shark_eventsub.start()

        self.dys_eventsub = EventSubWebsocket(self.dys_twitch, callback_loop=main_loop)
        self.dys_eventsub.start()

        self.bot_eventsub = EventSubWebsocket(self.bot_twitch, callback_loop=main_loop)
        self.bot_eventsub.start()

        self.chat = await Chat(self.bot_twitch)

    async def on_ready(self, ready_event: EventData):
        print("Bot is ready, joining channels")
        await ready_event.chat.join_room(TARGET_CHANNELS)
        print("Bot has joined the channels")

    async def on_ban(self, _ban: ChannelBanEvent):
        event = _ban.event
        user = TwitchUser(event.user_name, event.user_login, event.user_id)
        mod = TwitchUser(event.moderator_user_name, event.moderator_user_login, event.moderator_user_id)
        broadcaster = TwitchUser(event.broadcaster_user_name, event.broadcaster_user_login, event.broadcaster_user_id)
        duration = event.ends_at - event.banned_at if event.ends_at else None
        time = event.banned_at.astimezone(ZoneInfo("America/Chicago"))
        ban = TwitchBan(user, event.reason, mod, time, broadcaster, duration)
        await self.mod_cog.log_twitch_ban(ban)

    async def on_unban(self, _unban: ChannelUnbanEvent):
        event = _unban.event
        user = TwitchUser(event.user_name, event.user_login, event.user_id)
        mod = TwitchUser(event.moderator_user_name, event.moderator_user_login, event.moderator_user_id)
        broadcaster = TwitchUser(event.broadcaster_user_name, event.broadcaster_user_login, event.broadcaster_user_id)
        unban = TwitchUnban(user, mod, broadcaster)
        await self.mod_cog.log_twitch_unban(unban)

    async def on_warning(self, _warning: ChannelWarningSendEvent):
        event = _warning.event
        user = TwitchUser(event.user_name, event.user_login, event.user_id)
        mod = TwitchUser(event.moderator_user_name, event.moderator_user_login, event.moderator_user_id)
        time = datetime.now().astimezone(ZoneInfo("America/Chicago"))
        broadcaster = TwitchUser(event.broadcaster_user_name, event.broadcaster_user_login, event.broadcaster_user_id)
        warning = TwitchWarning(user, mod, event.reason, event.chat_rules_cited, time, broadcaster)
        await self.mod_cog.log_twitch_warning(warning)

    async def close_bot(self):
        if self.shark_eventsub:
            await self.shark_eventsub.stop()
        if self.dys_eventsub:
            await self.dys_eventsub.stop()
        if self.bot_eventsub:
            await self.bot_eventsub.stop()
        if self.chat:
            self.chat.stop()
        if self.shark_twitch:
            await self.shark_twitch.close()
        if self.dys_twitch:
            await self.dys_twitch.close()
        if self.bot_twitch:
            await self.bot_twitch.close()

    async def run(self):
        try:
            await self.setup()
            assert self.chat, "Chat instance is None"
            assert self.bot_twitch, "Bot twitch instance is None"
            assert self.dys_twitch, "Dys twitch instance is None"
            assert self.shark_twitch, "Shark twitch instance is None"
            assert self.bot_eventsub, "Bot eventsub instance is None"
            assert self.dys_eventsub, "Dys eventsub instance is None"
            assert self.shark_eventsub, "Shark eventsub instance is None"

            self.chat.register_event(ChatEvent.READY, self.on_ready)

            # Dys eventsub stuff
            dys_user = await first(self.dys_twitch.get_users())
            assert dys_user, "Dys user id not found"
            await self.dys_eventsub.listen_channel_ban(broadcaster_user_id=dys_user.id, callback=self.on_ban)
            await self.dys_eventsub.listen_channel_unban(broadcaster_user_id=dys_user.id, callback=self.on_unban)

            # shark eventsub stuff
            shark_user = await first(self.shark_twitch.get_users())
            assert shark_user, "Shark user id is not found"
            await self.shark_eventsub.listen_channel_ban(broadcaster_user_id=shark_user.id, callback=self.on_ban)
            await self.shark_eventsub.listen_channel_unban(broadcaster_user_id=shark_user.id, callback=self.on_unban)

            # bot eventsub stuff
            bot_user = await first(self.bot_twitch.get_users())
            assert bot_user, "Bot user id is not found"
            await self.bot_eventsub.listen_channel_warning_send(
                broadcaster_user_id=dys_user.id, moderator_user_id=bot_user.id, callback=self.on_warning
            )
            await self.bot_eventsub.listen_channel_warning_send(
                broadcaster_user_id=shark_user.id, moderator_user_id=bot_user.id, callback=self.on_warning
            )

        except Exception as e:
            print(f"Got an error: {e}")
        finally:
            await self.close_bot()
