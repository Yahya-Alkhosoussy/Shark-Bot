from copy import deepcopy
from pathlib import Path

from pydantic import ConfigDict, Field
from typing_extensions import Self

from utils.core import BaseConfig, DiscordNamedObj, DiscordNamedObjSet, DiscordNamedObjTypes


class Bait(DiscordNamedObj):
    objType = DiscordNamedObjTypes.PRICE

    def __new__(cls, baitName: str, baitPrice: int):
        return super().__new__(cls, baitName, baitPrice, cls.objType)

    def __deepcopy__(self, memo) -> Self:
        new_instance = type(self)(deepcopy(self.name, memo), deepcopy(self.id, memo))
        memo[id(self)] = new_instance
        return new_instance


class BaitSet(DiscordNamedObjSet):
    def __init__(self, Bait: list[Bait]):
        super().__init__(Bait)

    @property
    def setType(self) -> DiscordNamedObjTypes:
        return DiscordNamedObjTypes.PRICE

    def upsert(self, name: str, id: int):
        self._upsert(Bait(name, id))


class FishingConfig(BaseConfig):
    boost: bool = False
    boost_amount: int = Field(default=0, serialization_alias="boost amount")
    baits: BaitSet = Field(default_factory=lambda: BaitSet([]), serialization_alias="baits")

    model_config = ConfigDict(serialize_by_alias=True)

    def __init__(self, confPath: Path, **data):
        super().__init__(confPath=confPath, **data)

    def _validate_config(self):
        self._assert_populated(self.baits)

    def loadConfig(self, confPath: Path):
        fromYaml = self._loadYamlDict(confPath)

        for confkey, confvalue in fromYaml.items():
            match confkey:
                case "boost":
                    if confvalue and isinstance(confvalue, bool):
                        self.boost = confvalue
                case "boost amount":
                    if confvalue and isinstance(confvalue, int):
                        self.boost_amount = confvalue
                case "baits":
                    if confvalue and isinstance(confvalue, dict):
                        self.baits = BaitSet([Bait(baitName=key, baitPrice=value) for key, value in confvalue.items()])
