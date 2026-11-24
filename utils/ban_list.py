from dataclasses import dataclass
from enum import StrEnum


class Servers(StrEnum):
    SHARKOCALYPSE = "shark's cult"
    DAVEX = "davex's graveyard"
    SHARKTROCITY = "The nocturnal cavern"


class Channels(StrEnum):
    SHARKOCALYPSE = "sharkocalypse"
    DAVEX = "davex_gundyr"


class Statuses(StrEnum):
    BANNED = "banned"
    UNBANNED = "unbanned"


@dataclass()
class BannedMember:
    name: str
    id: int
    reason_for_ban: str
    status: Statuses
    initial_server_ban: Servers


@dataclass()
class TwitchUser:
    display: str
    id: str
    reason_for_ban: str
    status: Statuses
    initial_channel_ban: Channels
