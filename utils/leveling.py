import re
from copy import deepcopy
from pathlib import Path

from pydantic import Field

from utils.core import BaseConfig, DiscordNamedObj, DiscordNamedObjSet, DiscordNamedObjTypes


class LevelRole(DiscordNamedObj):
    objType = DiscordNamedObjTypes.LEVEL_ROLE

    def __new__(cls, level: int, id: int):
        if isinstance(level, str):
            level = int(re.sub(r"[^0-9]", "", level))
        return super().__new__(cls, str(level), id, cls.objType)

    def __deepcopy__(self, memo):
        new_instance = type(self)(deepcopy(self.level, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance

    @property
    def level(self):
        return int(re.sub(r"[^0-9]", "", self.name))


class LevelRoleSet(DiscordNamedObjSet["LevelRole"]):
    def __init__(self, levelRoles: list[LevelRole]):
        super().__init__(levelRoles)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.LEVEL_ROLE

    def upsert(self, name: str, id: int):
        newObj = LevelRole(int(re.sub(r"[^0-9]", "", name)), id)
        self._upsert(newObj)


class LevelingConfig(BaseConfig):
    level_roles: dict[str, LevelRoleSet] = Field(default_factory=dict)
    boost: bool = False
    boost_amount: int = 0

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath, **data)

    def _validate_config(self):
        self._assert_populated(self.level_roles)

    def loadConfig(self, confPath: Path):
        fromYaml = self._loadYamlDict(confPath)

        for confkey, confvalue in fromYaml.items():
            match confkey:
                case "level roles":
                    if confvalue and isinstance(confvalue, dict):
                        self.level_roles = {
                            key: LevelRoleSet([LevelRole(level=subkey, id=subvalue) for subkey, subvalue in value.items()])
                            for key, value in confvalue.items()
                        }
                case "boost":
                    if confvalue and isinstance(confvalue, bool):
                        self.boost = confvalue
                case "boost amount":
                    if confvalue and isinstance(confvalue, int):
                        self.boost_amount = confvalue

        self._afterLoad(confPath)
