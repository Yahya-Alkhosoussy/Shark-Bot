from copy import deepcopy
from pathlib import Path

import yaml
from pydantic import ConfigDict, Field
from typing_extensions import Self

from utils.core import BaseConfig, DiscordNamedObj, DiscordNamedObjSet, DiscordNamedObjTypes


class Guild(DiscordNamedObj):
    objType = DiscordNamedObjTypes.GUILD

    def __new__(cls, guildName: str, guildId: int):
        return super().__new__(cls, guildName, guildId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class TicketChannels(DiscordNamedObj):
    objType = DiscordNamedObjTypes.TICKET_CHANNEL

    def __new__(cls, guildName: str, channelId: int):
        return super().__new__(cls, guildName, channelId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class CategoryIds(DiscordNamedObj):
    objType = DiscordNamedObjTypes.CATEGORY_ID

    def __new__(cls, channelName: str, channelId: int):
        return super().__new__(cls, channelName, channelId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class TicketRole(DiscordNamedObj):
    objType = DiscordNamedObjTypes.TICKET_ROLE

    def __new__(cls, roleName: str, roleId: int):
        return super().__new__(cls, roleName, roleId, cls.objType)

    def __deepcopy__(self, memo) -> Self:
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class EmbedMessages(DiscordNamedObj):
    objType = DiscordNamedObjTypes.TICKET_CHANNEL

    def __new__(cls, guildName: str, messageId: int):
        return super().__new__(cls, guildName, messageId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class LogChannel(DiscordNamedObj):
    objType = DiscordNamedObjTypes.TICKET_CHANNEL

    def __new__(cls, channelName: str, channelId: int):
        return super().__new__(cls, channelName, channelId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class GuildSet(DiscordNamedObjSet[Guild]):
    def __init__(self, guilds: list[Guild]):
        super().__init__(guilds)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.GUILD

    def upsert(self, name: str, id: int):
        self._upsert(Guild(name, id))


class TicketChannelSet(DiscordNamedObjSet[TicketChannels]):
    def __init__(self, channels: list[TicketChannels]):
        super().__init__(channels)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.TICKET_CHANNEL

    def upsert(self, name: str, id: int):
        self._upsert(TicketChannels(name, id))


class CategoryIdSet(DiscordNamedObjSet):
    def __init__(self, categorys: list[CategoryIds]):
        super().__init__(categorys)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.CATEGORY_ID

    def upsert(self, name: str, id: int):
        self._upsert(CategoryIds(name, id))


class TicketRoleSet(DiscordNamedObjSet[TicketRole]):
    def __init__(self, roles: list[TicketRole]):
        super().__init__(roles)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.TICKET_ROLE

    def upsert(self, name: str, id: int):
        self._upsert(TicketRole(name, id))


class EmbedMessagesSet(DiscordNamedObjSet[EmbedMessages]):
    def __init__(self, message: list[EmbedMessages]):
        super().__init__(message)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.TICKET_ROLE

    def upsert(self, name: str, id: int):
        self._upsert(EmbedMessages(name, id))


class LogChannelSet(DiscordNamedObjSet[LogChannel]):
    def __init__(self, channel: list[LogChannel]):
        super().__init__(channel)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.TICKET_ROLE

    def upsert(self, name: str, id: int):
        self._upsert(LogChannel(name, id))


class TicketingConfig(BaseConfig):
    guilds: GuildSet = Field(default_factory=lambda: GuildSet([]), serialization_alias="guilds")
    ticket_channels: TicketChannelSet = Field(
        default_factory=lambda: TicketChannelSet([]), serialization_alias="ticket channels"
    )
    categories: dict[str, CategoryIdSet] = Field(default_factory=dict, serialization_alias="categories")
    roles: dict[str, TicketRoleSet] = Field(default_factory=dict, serialization_alias="roles")
    embed_messages: EmbedMessagesSet = Field(default_factory=lambda: EmbedMessagesSet([]), serialization_alias="embed messages")
    log_channels: dict[str, LogChannelSet] = Field(default_factory=dict, serialization_alias="log channels")
    path: str | None = None

    model_config = ConfigDict(serialize_by_alias=True)

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath=confPath, **data)

    def _validate_config(self):
        self._assert_populated(self.guilds)
        self._assert_populated(self.ticket_channels)
        self._assert_populated(self.categories)
        self._assert_populated(self.roles)
        self._assert_populated(self.embed_messages)
        self._assert_populated(self.log_channels)

    def loadConfig(self, confPath: Path):
        fromYaml = self._loadYamlDict(confPath)
        self.path = str(confPath)

        for confkey, confvalue in fromYaml.items():
            match confkey:
                case "guilds":
                    if confvalue and isinstance(confvalue, dict):
                        self.guilds = GuildSet([Guild(guildName=key, guildId=value) for key, value in confvalue.items()])
                case "ticket channels":
                    if confvalue and isinstance(confvalue, dict):
                        self.ticket_channels = TicketChannelSet(
                            [TicketChannels(guildName=key, channelId=value) for key, value in confvalue.items()]
                        )
                case "categories":
                    if confvalue and isinstance(confvalue, dict):
                        self.categories = {
                            key: CategoryIdSet(
                                [CategoryIds(channelName=subkey, channelId=subvalue) for subkey, subvalue in value.items()]
                            )
                            for key, value in confvalue.items()
                        }
                case "roles":
                    if confvalue and isinstance(confvalue, dict):
                        self.roles = {
                            key: TicketRoleSet(
                                [TicketRole(roleName=subkey, roleId=subvalue) for subkey, subvalue in value.items()]
                            )
                            for key, value in confvalue.items()
                        }
                case "embed messages":
                    if confvalue and isinstance(confvalue, dict):
                        self.embed_messages = EmbedMessagesSet(
                            [EmbedMessages(guildName=key, messageId=value) for key, value in confvalue.items()]
                        )
                case "log channels":
                    if confvalue and isinstance(confvalue, dict):
                        self.log_channels = {
                            key: LogChannelSet(
                                [LogChannel(channelName=subkey, channelId=subvalue) for subkey, subvalue in value.items()]
                            )
                            for key, value in confvalue.items()
                        }

    def save_message_id(self, guild_name: str, message_id: int) -> bool:
        guild_names: list[str] = []
        for guild in self.guilds:
            guild_names.append(guild[0])
        if guild_name in guild_names:
            self.embed_messages[guild_name] = message_id
            if self.path is not None:
                temp = Path(self.path).with_suffix(".tmp")
                temp.write_text(
                    yaml.safe_dump(self.model_dump(exclude={"path"}), sort_keys=False, allow_unicode=True), encoding=("UTF-8")
                )
                temp.replace(Path(self.path))
            return True
        else:
            raise KeyError(f"Could not find {guild_name} in config!")
