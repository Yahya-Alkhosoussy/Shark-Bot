from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from enum import Enum
from os.path import getmtime
from pathlib import Path
from typing import Any, Callable, Generic, TypeVar, Union, cast, overload

import yaml
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_serializer
from pydantic_core import core_schema
from typing_extensions import Self

DiscordNamedObjType = TypeVar("DiscordNamedObjType", bound="DiscordNamedObj")


class DiscordNamedObjTypes(Enum):
    NONE = 0
    GUILD = 1
    ROLE = 2
    CHANNEL = 3
    ROLE_MESSAGE = 4
    LEVEL_ROLE = 5
    TICKET_ROLE = 6
    TICKET_CHANNEL = 7
    CATEGORY_ID = 8
    EMBED_TITLE = 9
    EMBED_DESCRIPTION = 10


class DiscordNamedObj(ABC, tuple, Generic[DiscordNamedObjType]):
    objType: DiscordNamedObjTypes
    name: str
    id: int

    def __new__(cls, name: str, id: int, objType: DiscordNamedObjTypes = DiscordNamedObjTypes.NONE):
        inst = super().__new__(cls, (objType, name, id))
        inst.objType = objType
        inst.name = name
        inst.id = id
        return inst

    @abstractmethod
    def __deepcopy__(self, memo) -> Self:
        pass

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Callable[[Any], core_schema.CoreSchema]
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.tuple_schema(
                [
                    core_schema.is_instance_schema(DiscordNamedObjTypes),
                    core_schema.str_schema(),
                    core_schema.int_schema(),
                ]
            ),
        )

    @classmethod
    def _validate(cls, value: Any) -> "DiscordNamedObj":
        if isinstance(value, cls):
            return value
        # Subclasses (Guild, Role) expect __new__(cls, name, id)
        return cls(value[1], value[2])

    @model_serializer
    def serialize_model(self) -> str:
        return self.name

    def __str__(self) -> str:
        return f'({self.objType.name}Name: "{self.name}", {self.objType.name}Id: {self.id})'

    def __repr__(self) -> str:
        return f'({self.objType.name}Name: "{self.name}", {self.objType.name}Id: {self.id})'


class DiscordNamedObjSet(ABC, Generic[DiscordNamedObjType]):
    def __init__(self, setData: list[DiscordNamedObjType]):
        self._byName: dict[str, DiscordNamedObjType] = {obj.name: obj for obj in setData}
        self._byId: dict[int, DiscordNamedObjType] = {obj.id: obj for obj in setData}
        self._errText = f"Must provide {self.setType.name}Name (str) or {self.setType.name}Id (int)."

    @property
    @abstractmethod
    def setType(self) -> DiscordNamedObjTypes:
        pass

    @abstractmethod
    def upsert(self, name, id):
        pass

    @model_serializer
    def todict(self) -> dict[str, int]:
        return {obj.name: obj.id for obj in self._byName.values()}

    @overload
    def __getitem__(self, selector: str) -> int: ...

    @overload
    def __getitem__(self, selector: int) -> str: ...

    @overload
    def __getitem__(self, selector: DiscordNamedObj) -> int: ...

    def __getitem__(self, selector: Union[str, int, DiscordNamedObj]) -> Union[int, str]:
        if isinstance(selector, str):
            return self._byName[selector].id
        elif isinstance(selector, int):
            return self._byId[selector].name
        elif isinstance(selector, DiscordNamedObj):
            return self._byName[selector.name].id
        else:
            raise TypeError(self._errText + f" Got {type(selector)}.")

    @overload
    def get(self, selector: str) -> DiscordNamedObjType: ...

    @overload
    def get(self, selector: int) -> DiscordNamedObjType: ...

    @overload
    def get(self, selector: DiscordNamedObj) -> DiscordNamedObjType: ...

    def get(self, selector: Union[str, int, DiscordNamedObj]) -> DiscordNamedObjType:
        if isinstance(selector, str):
            return self._byName[selector]
        elif isinstance(selector, int):
            return self._byId[selector]
        elif isinstance(selector, DiscordNamedObj):
            return self._byName[selector.name]
        else:
            raise TypeError(self._errText + f" Got {type(selector)}.")

    @overload
    def __setitem__(self, k: str, v: int): ...

    @overload
    def __setitem__(self, k: int, v: str): ...

    def __setitem__(self, k: Union[str, int], v: Union[int, str]):
        sample = next(iter(self._byName.values()))
        if isinstance(k, str) and isinstance(v, int):
            newObj = type(sample)(k, v)
            self._byName[k] = newObj
            self._byId[v] = newObj
        elif isinstance(k, int) and isinstance(v, str):
            newObj = type(sample)(v, k)
            self._byId[k] = newObj
            self._byName[v] = newObj
        else:
            raise TypeError(f"keyvaluepair must be (str, int) or (int, str). Received ({type(k)}, {type(v)})")

    def __repr__(self) -> str:
        separator = ", "
        strOut = "{" + separator.join([f"'{v.name}': {v.id}" for k, v in self._byName.items()]) + "}"
        return strOut

    def __len__(self) -> int:
        return len(self._byName)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(list(self._byName.values()), memo))
        memo[id(self)] = new_instance
        return new_instance

    def __iter__(self):
        return iter(self._byName.items())

    def _upsert(self, newObj: DiscordNamedObjType):
        self._byName[newObj.name] = newObj
        self._byId[newObj.id] = newObj

    def items(self):
        return self._byName.items()

    def remove(self, selector: str | int) -> bool:
        backups = (self._byName, self._byId)

        try:
            if isinstance(selector, str):
                name = selector
                id = self._byName[selector].id
            elif isinstance(selector, int):
                id = selector
                name = self._byId[selector].name

            del self._byName[name]
            del self._byId[id]
            return True
        except Exception:
            self._byName = backups[0]
            self._byId = backups[1]
            return False


class Guild(DiscordNamedObj):
    objType = DiscordNamedObjTypes.GUILD

    def __new__(cls, guildName: str, guildId: int):
        return super().__new__(cls, guildName, guildId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class Role(DiscordNamedObj):
    objType = DiscordNamedObjTypes.ROLE

    def __new__(cls, roleName: str, roleId: int):
        return super().__new__(cls, roleName, roleId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class Channel(DiscordNamedObj):
    objType = DiscordNamedObjTypes.CHANNEL

    def __new__(cls, channelName: str, channelId: int):
        return super().__new__(cls, channelName, channelId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class RoleMessage(DiscordNamedObj):
    objType = DiscordNamedObjTypes.ROLE_MESSAGE

    def __new__(cls, roleMessageName: str, roleMessageId: int):
        return super().__new__(cls, roleMessageName, roleMessageId, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class RoleSet(DiscordNamedObjSet[Role]):
    def __init__(self, roles: list[Role]):
        super().__init__(roles)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.ROLE

    def upsert(self, name: str, id: int):
        self._upsert(Role(name, id))


class GuildSet(DiscordNamedObjSet[Guild]):
    def __init__(self, guilds: list[Guild]):
        super().__init__(guilds)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.GUILD

    def upsert(self, name: str, id: int):
        self._upsert(Guild(name, id))


class ChannelSet(DiscordNamedObjSet[Channel]):
    def __init__(self, channels: list[Channel]):
        super().__init__(channels)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.CHANNEL

    def upsert(self, name: str, id: int):
        self._upsert(Channel(name, id))


class RoleMessageSet(DiscordNamedObjSet[RoleMessage]):
    def __init__(self, roleMessages: list[RoleMessage]):
        super().__init__(roleMessages)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.ROLE_MESSAGE

    def upsert(self, name: str, id: int):
        self._upsert(RoleMessage(name, id))


class BirthdayMessageSet(list[tuple[str, bool]]):
    def __init__(self, birthdayMessages: list[tuple[str, bool]]):
        self._byMonth = {birthdayMessage[0]: birthdayMessage[1] for birthdayMessage in birthdayMessages}

    def upsert(self, month: str, state: bool):
        self._byMonth[month] = state


class BaseConfig(ABC, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    _last_load: datetime = PrivateAttr(default_factory=datetime.now)
    _loaded_config_path: Path = PrivateAttr(default_factory=Path)

    def __init__(self, confPath: Path, **data):
        super().__init__(**data)
        self.loadConfig(confPath)
        self._validate_config()

    @staticmethod
    def _loadYamlDict(confPath: Path) -> dict:
        return yaml.safe_load(confPath.read_text(encoding="UTF-8")) or {}

    @abstractmethod
    def _validate_config(self):
        pass

    @abstractmethod
    def loadConfig(self, confPath: Path):
        pass

    def __getitem__(self, selector: str):
        return getattr(self, selector.replace(" ", "_"))

    def _assert_populated(self, obj: Union[dict, DiscordNamedObjSet]):
        if not isinstance(obj, bool):
            assert obj
        if hasattr(obj, "__len__"):
            assert len(obj) > 0
        if isinstance(obj, dict):
            for v in obj.values():
                self._assert_populated(v)

    def _afterLoad(self, confPath: Path):
        self._last_load = datetime.now()
        self._loaded_config_path = confPath

    def reload(self) -> bool:
        if self._last_load < datetime.fromtimestamp(getmtime(self._loaded_config_path)):
            self.__dict__.update(type(self)(self._loaded_config_path).__dict__)
            return True
        return False

    def model_dump(self, **kwargs) -> dict[str, Any]:
        model = super().model_dump(**kwargs)

        def yaml_clean(obj):
            if isinstance(obj, dict):
                return {(k.name if hasattr(k, "name") else yaml_clean(k)): yaml_clean(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [yaml_clean(i) for i in obj]
            elif isinstance(obj, tuple):
                return obj[1]
            elif hasattr(obj, "todict"):
                return obj.todict()
            elif hasattr(obj, "id"):
                return obj.id
            elif isinstance(obj, Enum):
                return obj.name
            return obj

        return cast(dict[str, Any], yaml_clean(model))

    def saveConfig(self, confPath: Path | None = None):
        temp = confPath.with_suffix(".tmp") if confPath else self._loaded_config_path.with_suffix(".tmp")
        temp.write_text(yaml.safe_dump(self.model_dump(), sort_keys=False, allow_unicode=True), encoding=("UTF-8"))
        temp.replace(confPath if confPath else self._loaded_config_path)
        self._last_load = datetime.now()


class AppConfig(BaseConfig):
    guilds: GuildSet = Field(default_factory=lambda: GuildSet([]))
    roles: dict[str, RoleSet] = Field(default_factory=dict)
    channels: dict[str, ChannelSet] = Field(default_factory=dict)
    guild_role_messages: dict[Guild, RoleMessageSet] = Field(default_factory=dict)
    birthday_message: dict[str, bool] = Field(default_factory=dict)
    boost: bool = False
    boost_amount: int = 0
    time_per_loop: int = 0
    set_up_done: dict[Guild, bool] = Field(default_factory=dict)

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath=confPath, **data)

    def _validate_config(self):
        self._assert_populated(self.guilds)
        self._assert_populated(self.channels)
        self._assert_populated(self.roles)
        self._assert_populated(self.guild_role_messages)
        self._assert_populated(self.birthday_message)
        self._assert_populated(self.set_up_done)
        assert self.time_per_loop > 0

    def loadConfig(self, confPath: Path):
        fromYaml = self._loadYamlDict(confPath)

        for confkey, confvalue in fromYaml.items():
            match confkey:
                case "guilds":
                    if confvalue and isinstance(confvalue, dict):
                        self.guilds = GuildSet([Guild(guildName=key, guildId=value) for key, value in confvalue.items()])
                case "roles":
                    if confvalue and isinstance(confvalue, dict):
                        self.roles = {
                            key: RoleSet([Role(roleName=subkey, roleId=subvalue) for subkey, subvalue in value.items()])
                            for key, value in confvalue.items()
                        }
                case "channels":
                    if confvalue and isinstance(confvalue, dict):
                        self.channels = {
                            key: ChannelSet(
                                [Channel(channelName=subkey, channelId=subvalue) for subkey, subvalue in value.items()]
                            )
                            for key, value in confvalue.items()
                        }
                case "guild role messages":
                    if confvalue and isinstance(confvalue, dict):
                        new_guild_role_messages = {}
                        if self.guilds:
                            for key, value in confvalue.items():
                                if key in self.guilds._byName:
                                    guild = self.guilds.get(key)
                                    new_guild_role_messages[guild] = RoleMessageSet(
                                        [
                                            RoleMessage(roleMessageName=subkey, roleMessageId=subvalue)
                                            for subkey, subvalue in value.items()
                                        ]
                                    )
                        self.guild_role_messages = new_guild_role_messages
                case "birthday message":
                    if confvalue and isinstance(confvalue, dict):
                        self.birthday_message = {
                            key: value for key, value in confvalue.items() if isinstance(key, str) and isinstance(value, bool)
                        }
                case "boost":
                    if confvalue and isinstance(confvalue, bool):
                        self.boost = confvalue
                case "boost amount":
                    if confvalue and isinstance(confvalue, int):
                        self.boost_amount = confvalue
                case "time per loop":
                    if confvalue and isinstance(confvalue, int):
                        self.time_per_loop = confvalue
                case "set up done":
                    if confvalue and isinstance(confvalue, dict):
                        new_set_up_done = {}
                        if self.guilds:
                            for key, value in confvalue.items():
                                if isinstance(value, bool) and key in self.guilds._byName:
                                    guild = self.guilds.get(key)
                                    new_set_up_done[guild] = value
                        self.set_up_done = new_set_up_done

        self._afterLoad(confPath)

    # This is to check if the guild ID is in the config
    def is_guild_in_config(self, guild_id: int) -> bool:
        guild_ids = self.guilds._byId.keys() if self.guilds else []

        if guild_id in guild_ids:
            return True
        else:
            return False

    def is_rr_message_id_in_config(self, guild_name: str) -> bool:
        guild_role_message_names: list[str] = [guild.name for guild in self.guild_role_messages.keys()]

        if guild_name in guild_role_message_names:
            return True
        else:
            return False

    def get_channel_id(self, guild_name: str, channel: str) -> int:
        channels = self.channels.get(channel)

        if channels is None:
            raise KeyError(f"Channel type {channel} not in config")

        guild_channel = channels.get(guild_name)

        if guild_channel is None:
            raise KeyError(f"Channel type {channel} for guild {guild_name} does not exist in the server")
        else:
            return guild_channel.id

    def mark_reminder_as_done(self, month: str) -> bool:
        if month in self.birthday_message:
            self.birthday_message[month] = True
            self.saveConfig()
            return True
        else:
            return False
