from twitchAPI.chat import EventData # noqa
from twitchAPI.eventsub.websocket import EventSubWebsocket # noqa
from twitchAPI.helper import first # noqa
from twitchAPI.oauth import UserAuthenticationStorageHelper # noqa
from twitchAPI.object.eventsub import ChannelBanEvent, ChannelUnbanEvent, ChannelWarningSendEvent # noqa
from twitchAPI.twitch import Twitch # noqa
from twitchAPI.type import AuthScope # noqa

from moderation.tools import Moderation # noqa

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
