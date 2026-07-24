from twitchAPI.chat import Chat, EventData # noqa
from twitchAPI.eventsub.websocket import EventSubWebsocket # noqa
from twitchAPI.helper import first # noqa
from twitchAPI.oauth import UserAuthenticationStorageHelper # noqa
from twitchAPI.object.eventsub import ChannelBanEvent, ChannelUnbanEvent, ChannelWarningSendEvent # noqa
from twitchAPI.twitch import Twitch # noqa
from twitchAPI.type import AuthScope # noqa

from moderation.tools import Moderation # noqa
from MyClient import MyBot
from utils.core import AppConfig
from pathlib import Path
import asyncio

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

    async def on_ban(self, ban: ChannelBanEvent):
        pass

    async def on_unban(self, unban: ChannelUnbanEvent):
        pass

    async def on_warning(self, warning: ChannelWarningSendEvent):
        pass

    async def close_bot(self):
        pass

    async def run(self):
        pass
